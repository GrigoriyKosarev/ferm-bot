"""
Обробники кнопок меню

Обробляє:
- Reply кнопка: Кошик
- Inline кнопки кошика: управління кількістю, видалення товарів
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.database import get_session
from bot.queries import get_cart, remove_from_cart, update_cart_quantity, clear_cart
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
