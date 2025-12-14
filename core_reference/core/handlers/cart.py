"""
Обробник кошика користувача

Функції:
- Перегляд товарів у кошику
- Зміна кількості товарів
- Видалення товарів
- Очищення кошика
- Перехід на сайт для оплати
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from core.keyboards.inline import (
    get_cart_actions_keyboard,
    get_cart_item_actions,
    get_yes_no_keyboard
)
from core.keyboards.reply import get_main_menu
from core.database.database import AsyncSessionLocal
from core.database.queries import (
    get_cart_summary,
    update_cart_item_quantity,
    remove_from_cart,
    clear_cart
)

# Створення роутера
router = Router(name="cart")


# ============= РЕДАГУВАННЯ КОШИКА =============

@router.callback_query(F.data == "cart:edit")
async def edit_cart(callback: CallbackQuery):
    """
    Режим редагування кошика

    Показує детальний список з кнопками редагування для кожного товару
    """
    async with AsyncSessionLocal() as session:
        cart_data = await get_cart_summary(session, callback.from_user.id)

        if cart_data['total_items'] == 0:
            await callback.answer(
                "🤷‍♂️ Кошик порожній",
                show_alert=True
            )
            return

        # Формування детального списку
        text = "<b>✏️ Редагування кошика</b>\n\n"

        for idx, item in enumerate(cart_data['items'], 1):
            item_total = item.product_price * item.quantity
            text += (
                f"{idx}. <b>{item.product_name}</b>\n"
                f"   💰 {item.product_price} грн × {item.quantity} {item.unit}\n"
                f"   = {item_total:.2f} грн\n"
                f"   /edit_{item.id}\n\n"
            )

        text += (
            f"━━━━━━━━━━━━━━━━━\n"
            f"<b>💰 Загальна сума:</b> {cart_data['total_price']:.2f} грн\n\n"
            f"<i>Використовуйте команди /edit_ID для редагування товару</i>"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_cart_actions_keyboard()
        )

    await callback.answer()


# ============= ЗМІНА КІЛЬКОСТІ =============

@router.callback_query(F.data.startswith("cart:increase:"))
async def increase_quantity(callback: CallbackQuery):
    """
    Збільшити кількість товару на 1

    Callback format: cart:increase:{cart_item_id}
    """
    cart_item_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        # Отримати поточні дані
        cart_data = await get_cart_summary(session, callback.from_user.id)
        item = next((i for i in cart_data['items'] if i.id == cart_item_id), None)

        if not item:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Перевірка на максимальну кількість
        if item.quantity >= 1000:  # Розумний ліміт
            await callback.answer(
                "⚠️ Досягнуто максимальну кількість",
                show_alert=True
            )
            return

        # Збільшити кількість
        new_quantity = item.quantity + 1
        await update_cart_item_quantity(session, cart_item_id, new_quantity)

        logger.debug(f"Збільшено кількість товару {cart_item_id} до {new_quantity}")

        # Оновити повідомлення
        new_total = item.product_price * new_quantity

        await callback.answer(
            f"✅ Кількість: {new_quantity} {item.unit} | {new_total:.2f} грн",
            show_alert=False
        )

        # Можна оновити текст повідомлення, якщо потрібно
        # await edit_cart(callback)


@router.callback_query(F.data.startswith("cart:decrease:"))
async def decrease_quantity(callback: CallbackQuery):
    """
    Зменшити кількість товару на 1

    Callback format: cart:decrease:{cart_item_id}
    """
    cart_item_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        cart_data = await get_cart_summary(session, callback.from_user.id)
        item = next((i for i in cart_data['items'] if i.id == cart_item_id), None)

        if not item:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Якщо кількість 1 - видаляємо товар
        if item.quantity <= 1:
            await callback.answer(
                "⚠️ Для видалення товару використовуйте кнопку 🗑",
                show_alert=True
            )
            return

        # Зменшити кількість
        new_quantity = item.quantity - 1
        await update_cart_item_quantity(session, cart_item_id, new_quantity)

        logger.debug(f"Зменшено кількість товару {cart_item_id} до {new_quantity}")

        new_total = item.product_price * new_quantity

        await callback.answer(
            f"✅ Кількість: {new_quantity} {item.unit} | {new_total:.2f} грн",
            show_alert=False
        )


# ============= ВИДАЛЕННЯ ТОВАРУ =============

@router.callback_query(F.data.startswith("cart:remove:"))
async def remove_item(callback: CallbackQuery):
    """
    Видалити товар з кошика

    Callback format: cart:remove:{cart_item_id}
    """
    cart_item_id = int(callback.data.split(":")[2])

    async with AsyncSessionLocal() as session:
        # Отримати назву товару для повідомлення
        cart_data = await get_cart_summary(session, callback.from_user.id)
        item = next((i for i in cart_data['items'] if i.id == cart_item_id), None)

        if not item:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        product_name = item.product_name

        # Видалити товар
        await remove_from_cart(
            session,
            cart_item_id=cart_item_id,
            user_id=callback.from_user.id
        )

        logger.info(f"Товар {cart_item_id} видалено з кошика користувача {callback.from_user.id}")

        await callback.answer(
            f"🗑 {product_name} видалено з кошика",
            show_alert=False
        )

        # Оновити відображення кошика
        # Перевірити чи залишились товари
        new_cart_data = await get_cart_summary(session, callback.from_user.id)

        if new_cart_data['total_items'] == 0:
            # Кошик порожній
            text = (
                "<b>🛍 Ваш кошик</b>\n\n"
                "Кошик порожній 🤷‍♂️\n\n"
                "Перейдіть до <b>🛒 Каталогу товарів</b>"
            )
            await callback.message.edit_text(text)
        else:
            # Оновити список
            await edit_cart(callback)


# ============= ОЧИЩЕННЯ КОШИКА =============

@router.callback_query(F.data == "cart:clear")
async def confirm_clear_cart(callback: CallbackQuery):
    """
    Запит підтвердження очищення кошика
    """
    text = (
        "<b>⚠️ Підтвердіть дію</b>\n\n"
        "Ви впевнені, що хочете очистити весь кошик?\n"
        "Всі товари будуть видалені."
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_yes_no_keyboard(
            yes_callback="cart:clear:confirmed",
            no_callback="cart:clear:cancelled"
        )
    )
    await callback.answer()


@router.callback_query(F.data == "cart:clear:confirmed")
async def clear_cart_confirmed(callback: CallbackQuery):
    """
    Підтверджене очищення кошика
    """
    async with AsyncSessionLocal() as session:
        await clear_cart(session, callback.from_user.id)

    logger.info(f"Кошик користувача {callback.from_user.id} очищено")

    text = (
        "<b>🗑 Кошик очищено</b>\n\n"
        "Всі товари видалено з кошика.\n\n"
        "Перейдіть до каталогу, щоб додати нові товари."
    )

    await callback.message.edit_text(text)
    await callback.answer("✅ Кошик очищено", show_alert=False)


@router.callback_query(F.data == "cart:clear:cancelled")
async def clear_cart_cancelled(callback: CallbackQuery):
    """
    Скасування очищення кошика
    """
    # Повернутися до перегляду кошика
    async with AsyncSessionLocal() as session:
        cart_data = await get_cart_summary(session, callback.from_user.id)

        items_text = ""
        for idx, item in enumerate(cart_data['items'], 1):
            items_text += (
                f"{idx}. <b>{item.product_name}</b>\n"
                f"   💰 {item.product_price} грн × {item.quantity} {item.unit}\n"
                f"   = {item.product_price * item.quantity:.2f} грн\n\n"
            )

        text = (
            f"<b>🛍 Ваш кошик</b>\n\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━━━\n"
            f"<b>📦 Товарів:</b> {cart_data['total_items']} шт.\n"
            f"<b>💰 Загальна сума:</b> {cart_data['total_price']:.2f} грн"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_cart_actions_keyboard()
        )

    await callback.answer("↩️ Повернення до кошика", show_alert=False)


# ============= КОМАНДИ ДЛЯ РЕДАГУВАННЯ =============

@router.message(F.text.regexp(r"^/edit_(\d+)$"))
async def edit_cart_item(message: Message):
    """
    Редагування конкретного товару через команду

    Format: /edit_{cart_item_id}
    """
    # Витягнути ID з команди
    import re
    match = re.match(r"^/edit_(\d+)$", message.text)
    if not match:
        return

    cart_item_id = int(match.group(1))

    async with AsyncSessionLocal() as session:
        cart_data = await get_cart_summary(session, message.from_user.id)
        item = next((i for i in cart_data['items'] if i.id == cart_item_id), None)

        if not item:
            await message.answer("❌ Товар не знайдено в кошику")
            return

        item_total = item.product_price * item.quantity

        text = (
            f"<b>✏️ Редагування товару</b>\n\n"
            f"<b>{item.product_name}</b>\n\n"
            f"💰 <b>Ціна:</b> {item.product_price} грн/{item.unit}\n"
            f"📦 <b>Кількість:</b> {item.quantity} {item.unit}\n"
            f"💵 <b>Разом:</b> {item_total:.2f} грн\n\n"
            f"<i>Використовуйте кнопки для зміни кількості:</i>"
        )

        await message.answer(
            text,
            reply_markup=get_cart_item_actions(cart_item_id)
        )


# ============= ДОПОМІЖНІ ФУНКЦІЇ =============

async def format_cart_message(user_id: int) -> tuple[str, bool]:
    """
    Форматування повідомлення кошика

    Returns:
        tuple: (текст повідомлення, чи порожній кошик)
    """
    async with AsyncSessionLocal() as session:
        cart_data = await get_cart_summary(session, user_id)

        if cart_data['total_items'] == 0:
            text = (
                "<b>🛍 Ваш кошик</b>\n\n"
                "Кошик порожній 🤷‍♂️"
            )
            return text, True

        # Формування списку
        items_text = ""
        for idx, item in enumerate(cart_data['items'], 1):
            item_total = item.product_price * item.quantity
            items_text += (
                f"{idx}. <b>{item.product_name}</b>\n"
                f"   💰 {item.product_price} грн × {item.quantity} {item.unit}\n"
                f"   = {item_total:.2f} грн\n\n"
            )

        text = (
            f"<b>🛍 Ваш кошик</b>\n\n"
            f"{items_text}"
            f"━━━━━━━━━━━━━━━━━\n"
            f"<b>📦 Товарів:</b> {cart_data['total_items']} шт.\n"
            f"<b>💰 Загальна сума:</b> {cart_data['total_price']:.2f} грн\n\n"
            f"<i>Для завершення покупки перейдіть на сайт</i>"
        )

        return text, False