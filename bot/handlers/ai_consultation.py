"""
Обробники для AI-консультацій по товарах

Використовує OpenAI API для надання рекомендацій та відповідей на питання
про конкретний товар
"""
import asyncio
from typing import Dict, List

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database import get_session
from bot.queries import get_product_by_id
from bot.states import AIConsultationStates
from bot.config import settings
from bot.keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="ai_consultation")

# Зберігаємо історію чатів користувачів (в пам'яті)
# {user_id: {"product_id": int, "history": [{"role": "user", "content": "..."}, ...]}}
USER_AI_CHATS: Dict[int, Dict] = {}

# System prompt для AI
SYSTEM_PROMPT = """
Ти — досвідчений агроном-консультант агромагазину. Працюєш українською мовою.

Твоя задача:
1. Відповідати на питання про товар у контексті, який я надам
2. Давати практичні рекомендації щодо застосування
3. Пояснювати переваги та особливості використання
4. Радити коли і як застосовувати продукт
5. Попереджати про можливі помилки у використанні

Стиль спілкування:
- Дружній, але професійний
- Конкретний та практичний
- Стислий (до 500-700 символів)
- Використовуй маркіровані списки для чіткості
- Давай приклади з реальної практики

Якщо питання не стосується товару - ввічливо поверни розмову до теми товару.
"""


def get_product_context(product) -> str:
    """Формує контекст про товар для AI"""
    context = f"ТОВАР:\n"
    context += f"Назва: {product.name}\n"
    context += f"Категорія: {product.category.name}\n"

    if product.description:
        context += f"Опис: {product.description}\n"

    if product.price:
        context += f"Ціна: {product.price:.2f} грн\n"

    context += f"\nВідповідай на питання користувача у контексті цього товару."

    return context


async def get_ai_response(messages: List[Dict]) -> str:
    """Отримує відповідь від OpenAI API"""
    if not settings.OPENAI_API_KEY:
        return "❌ AI-консультації недоступні. Зверніться до менеджера."

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content or "Вибачте, не вдалося згенерувати відповідь."

    except ImportError:
        return "❌ Бібліотека OpenAI не встановлена. Зверніться до менеджера."
    except Exception as e:
        return f"❌ Помилка AI: {str(e)[:100]}"


def get_ai_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавіатура для AI чату"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад до товару",
            callback_data=f"product:{product_id}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🏠 Головне меню",
            callback_data="back_to_menu"
        )
    )

    return builder.as_markup()


@router.callback_query(F.data.startswith("ai_consult:"))
async def start_ai_consultation(callback: CallbackQuery, state: FSMContext):
    """
    Початок AI-консультації по товару
    """
    if not settings.OPENAI_API_KEY:
        await callback.answer(
            "❌ AI-консультації недоступні. Зверніться до менеджера.",
            show_alert=True
        )
        return

    # Отримуємо ID товару
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with get_session() as session:
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Ініціалізуємо чат
        USER_AI_CHATS[user_id] = {
            "product_id": product_id,
            "history": []
        }

        # Формуємо контекст товару
        product_context = get_product_context(product)

        # Переходимо у стан чату
        await state.set_state(AIConsultationStates.chatting)
        await state.update_data(product_id=product_id)

        # Вітальне повідомлення
        welcome_text = (
            f"🤖 <b>AI-консультація</b>\n\n"
            f"Товар: <b>{product.name}</b>\n\n"
            f"Я агроном-консультант. Задавайте питання про цей товар:\n"
            f"• Як застосовувати?\n"
            f"• Для яких культур підходить?\n"
            f"• Коли використовувати?\n"
            f"• Які переваги?\n\n"
            f"Введіть ваше питання:"
        )

        # Перевіряємо чи це фото-повідомлення
        if callback.message.photo:
            # Видаляємо і створюємо нове
            await callback.message.delete()
            await callback.bot.send_message(
                callback.message.chat.id,
                welcome_text,
                reply_markup=get_ai_keyboard(product_id),
                parse_mode="HTML"
            )
        else:
            # Редагуємо текстове
            await callback.message.edit_text(
                welcome_text,
                reply_markup=get_ai_keyboard(product_id),
                parse_mode="HTML"
            )

    await callback.answer()


@router.message(AIConsultationStates.chatting)
async def process_ai_chat(message: Message, state: FSMContext):
    """
    Обробка повідомлень у AI-чаті
    """
    # Перевірка на команди
    if message.text and message.text.startswith("/"):
        await state.clear()
        return

    user_id = message.from_user.id
    user_text = (message.text or "").strip()

    if not user_text:
        await message.answer("Будь ласка, введіть текстове питання.")
        return

    # Отримуємо дані чату
    data = await state.get_data()
    product_id = data.get("product_id")

    if not product_id:
        await message.answer("❌ Помилка: товар не знайдено")
        await state.clear()
        return

    # Показуємо індикатор "друкує..."
    thinking_msg = await message.answer("🤖 Думаю...")

    try:
        async with get_session() as session:
            product = await get_product_by_id(session, product_id)

            if not product:
                await thinking_msg.edit_text("❌ Товар не знайдено")
                await state.clear()
                return

            # Отримуємо історію
            chat_data = USER_AI_CHATS.get(user_id, {"history": []})
            history = chat_data.get("history", [])

            # Формуємо повідомлення для AI
            product_context = get_product_context(product)

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": product_context}
            ]

            # Додаємо останні 6 повідомлень з історії
            messages.extend(history[-6:])

            # Додаємо поточне питання
            messages.append({"role": "user", "content": user_text})

            # Отримуємо відповідь від AI
            ai_response = await get_ai_response(messages)

            # Видаляємо індикатор
            await thinking_msg.delete()

            # Відправляємо відповідь
            await message.answer(
                f"🤖 {ai_response}",
                reply_markup=get_ai_keyboard(product_id),
                parse_mode="HTML"
            )

            # Зберігаємо в історію
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": ai_response})

            # Обмежуємо історію 10 останніми повідомленнями
            if len(history) > 10:
                history = history[-10:]

            USER_AI_CHATS[user_id] = {
                "product_id": product_id,
                "history": history
            }

    except Exception as e:
        await thinking_msg.edit_text(f"❌ Помилка: {str(e)[:100]}")
        await state.clear()
