"""
КРОК 5: Обробники кнопок меню

Обробляє:
- Reply кнопки: Каталог, Кошик, Інформація, Налаштування
- Inline кнопки: info_about, info_help
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.database import get_session
from bot.queries import get_cart, remove_from_cart, update_cart_quantity, clear_cart
from bot.keyboards import get_info_keyboard
from bot.keyboards.inline import get_cart_keyboard
from bot.logger import logger

# Створюємо Router для меню
router = Router(name="menu")


# ========================================
# ОБРОБНИКИ REPLY КНОПОК
# ========================================
# Примітка: Обробник "📦 Каталог" перенесено в start.py
# (використовує реальну БД через core.database.queries)

@router.message(F.text == "🛒 Кошик")
async def menu_cart(message: Message):
    """Обробник кнопки 'Кошик' - показує товари з БД"""
    user_id = message.from_user.id
    logger.info(f"Користувач {user_id} відкрив кошик")

    async with get_session() as session:
        cart_items = await get_cart(session, user_id)

        if not cart_items:
            text = "🛒 <b>Ваш кошик</b>\n\n"
            text += "Кошик порожній.\n"
            text += "Додайте товари з каталогу!"
        else:
            text = "🛒 <b>Ваш кошик</b>\n\n"

            total_sum = 0.0
            for item in cart_items:
                text += f"📦 <b>{item.product.name}</b>\n"
                text += f"   Кількість: {item.quantity} шт\n"

                if item.product.price:
                    item_total = item.product.price * item.quantity
                    total_sum += item_total
                    text += f"   Ціна: {item.product.price:.2f} грн x {item.quantity} = {item_total:.2f} грн\n"

                text += "\n"

            text += f"💰 <b>Разом:</b> {total_sum:.2f} грн\n"

        keyboard = get_cart_keyboard(cart_items)

        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.message(F.text == "ℹ️ Інформація")
async def menu_info(message: Message):
    """Обробник кнопки 'Інформація' - показує inline кнопки"""
    logger.info(f"Користувач {message.from_user.id} запросив інформацію")
    await message.answer(
        "ℹ️ Інформація про бота\n\n"
        "Оберіть розділ:",
        reply_markup=get_info_keyboard()
    )


@router.message(F.text == "⚙️ Налаштування")
async def menu_settings(message: Message):
    """Обробник кнопки 'Налаштування'"""
    logger.info(f"Користувач {message.from_user.id} відкрив налаштування")
    await message.answer(
        "⚙️ Налаштування\n\n"
        "Тут будуть налаштування мови, сповіщень тощо.\n"
        "(Реалізуємо в наступних кроках)"
    )


# ========================================
# ОБРОБНИКИ INLINE КНОПОК (CALLBACK)
# ========================================

@router.callback_query(F.data == "info_about")
async def callback_info_about(callback: CallbackQuery):
    """Обробник inline кнопки 'Про бота'"""
    logger.info(f"Користувач {callback.from_user.id} натиснув 'Про бота'")
    
    await callback.message.edit_text(
        "📖 Про бота\n\n"
        "Це навчальний бот для демонстрації можливостей aiogram 3.x\n\n"
        "Реалізовано:\n"
        "✅ Крок 1: Мінімальний бот\n"
        "✅ Крок 2: Конфігурація (.env)\n"
        "✅ Крок 3: Логування\n"
        "✅ Крок 4: База даних (SQLAlchemy)\n"
        "✅ Крок 5: Меню та клавіатури\n\n"
        "Наступні кроки: Каталог, Кошик, AI-консультант",
        reply_markup=get_info_keyboard()
    )
    
    # ВАЖЛИВО: Підтверджуємо callback щоб прибрати "годинник"
    await callback.answer()


@router.callback_query(F.data == "info_help")
async def callback_info_help(callback: CallbackQuery):
    """Обробник inline кнопки 'Допомога'"""
    logger.info(f"Користувач {callback.from_user.id} натиснув 'Допомога'")

    await callback.message.edit_text(
        "❓ Допомога\n\n"
        "Як користуватись ботом:\n\n"
        "1️⃣ /start - Показати головне меню\n"
        "2️⃣ 📦 Каталог - Переглянути товари\n"
        "3️⃣ 🛒 Кошик - Переглянути ваше замовлення\n"
        "4️⃣ ℹ️ Інформація - Про бота та допомога\n"
        "5️⃣ ⚙️ Налаштування - Налаштування бота\n\n"
        "Виникли питання? Пишіть підтримці!",
        reply_markup=get_info_keyboard()
    )

    await callback.answer()


# ========================================
# ОБРОБНИКИ КОШИКА (CALLBACK)
# ========================================

@router.callback_query(F.data.startswith("cart_qty:"))
async def callback_cart_qty(callback: CallbackQuery):
    """Змінює кількість товару в кошику"""
    # Формат: "cart_qty:123:5:inc" або "cart_qty:123:5:dec"
    parts = callback.data.split(":")
    product_id = int(parts[1])
    current_qty = int(parts[2])
    action = parts[3]
    user_id = callback.from_user.id

    # Змінюємо кількість
    if action == "inc":
        new_qty = current_qty + 1
    elif action == "dec":
        new_qty = max(1, current_qty - 1)
    else:
        await callback.answer("❌ Невірна дія", show_alert=True)
        return

    async with get_session() as session:
        # Оновлюємо кількість в БД
        await update_cart_quantity(session, user_id, product_id, new_qty)

        # Оновлюємо відображення кошика
        cart_items = await get_cart(session, user_id)

        text = "🛒 <b>Ваш кошик</b>\n\n"
        total_sum = 0.0
        for item in cart_items:
            text += f"📦 <b>{item.product.name}</b>\n"
            text += f"   Кількість: {item.quantity} шт\n"
            if item.product.price:
                item_total = item.product.price * item.quantity
                total_sum += item_total
                text += f"   Ціна: {item.product.price:.2f} грн x {item.quantity} = {item_total:.2f} грн\n"
            text += "\n"

        text += f"💰 <b>Разом:</b> {total_sum:.2f} грн\n"

        keyboard = get_cart_keyboard(cart_items)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("cart_remove:"))
async def callback_cart_remove(callback: CallbackQuery):
    """Видаляє товар з кошика"""
    # Формат: "cart_remove:123"
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with get_session() as session:
        # Видаляємо товар з БД
        removed = await remove_from_cart(session, user_id, product_id)

        if removed:
            # Оновлюємо відображення кошика
            cart_items = await get_cart(session, user_id)

            if not cart_items:
                text = "🛒 <b>Ваш кошик</b>\n\n"
                text += "Кошик порожній.\n"
                text += "Додайте товари з каталогу!"
            else:
                text = "🛒 <b>Ваш кошик</b>\n\n"
                total_sum = 0.0
                for item in cart_items:
                    text += f"📦 <b>{item.product.name}</b>\n"
                    text += f"   Кількість: {item.quantity} шт\n"
                    if item.product.price:
                        item_total = item.product.price * item.quantity
                        total_sum += item_total
                        text += f"   Ціна: {item.product.price:.2f} грн x {item.quantity} = {item_total:.2f} грн\n"
                    text += "\n"
                text += f"💰 <b>Разом:</b> {total_sum:.2f} грн\n"

            keyboard = get_cart_keyboard(cart_items)

            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer("✅ Товар видалено з кошика")
        else:
            await callback.answer("❌ Товар не знайдено", show_alert=True)


@router.callback_query(F.data == "cart_clear")
async def callback_cart_clear(callback: CallbackQuery):
    """Очищає весь кошик"""
    user_id = callback.from_user.id

    async with get_session() as session:
        count = await clear_cart(session, user_id)

        text = "🛒 <b>Ваш кошик</b>\n\n"
        text += "Кошик порожній.\n"
        text += "Додайте товари з каталогу!"

        keyboard = get_cart_keyboard([])

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await callback.answer(f"✅ Кошик очищено ({count} товарів видалено)", show_alert=True)


@router.callback_query(F.data == "cart_close")
async def callback_cart_close(callback: CallbackQuery):
    """Закриває кошик"""
    await callback.message.delete()
    await callback.answer()
