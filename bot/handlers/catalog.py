"""
Обробники для роботи з каталогом товарів
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database import get_session
from bot.queries import get_subcategories, get_category_by_id, get_products_by_category, get_product_by_id
from bot.keyboards.inline import get_categories_keyboard_from_db, get_products_keyboard, get_product_detail_keyboard

router = Router(name="catalog")


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """
    Повернення до головного меню каталогу (показ кореневих категорій)
    """
    from bot.queries import get_root_categories

    async with get_session() as session:
        categories = await get_root_categories(session)

        text = "📦 <b>Каталог товарів</b>\n\n"
        text += "Оберіть категорію для перегляду товарів:"

        keyboard = get_categories_keyboard_from_db(categories)

        # Перевіряємо чи це фото-повідомлення
        if callback.message.photo:
            # Якщо фото - видаляємо і створюємо нове
            chat_id = callback.message.chat.id
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Якщо текст - редагуємо
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def callback_category(callback: CallbackQuery):
    """
    Обробник натискання на категорію.
    Показує підкатегорії якщо вони є, або товари якщо підкатегорій немає.
    """
    # Отримуємо ID категорії з callback_data (формат: "category:123")
    category_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        # Отримуємо інформацію про категорію
        category = await get_category_by_id(session, category_id)

        if not category:
            await callback.answer("❌ Категорію не знайдено", show_alert=True)
            return

        # Перевіряємо чи є підкатегорії
        subcategories = await get_subcategories(session, category_id)

        if subcategories:
            # Є підкатегорії - показуємо їх
            text = f"📁 <b>{category.name}</b>\n\nОберіть підкатегорію:"
            # Передаємо parent_id для кнопки "Назад"
            keyboard = get_categories_keyboard_from_db(subcategories, parent_id=category.parent_id)

            # Перевіряємо чи це фото-повідомлення
            if callback.message.photo:
                # Якщо фото - видаляємо і створюємо нове
                chat_id = callback.message.chat.id
                await callback.message.delete()
                await callback.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # Якщо текст - редагуємо
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            # Немає підкатегорій - показуємо товари
            products = await get_products_by_category(session, category_id, limit=10)

            if products:
                text = f"📦 <b>{category.name}</b>\n\n"
                text += f"Знайдено товарів: {len(products)}\n\n"
                text += "Оберіть товар для перегляду деталей:"

                # Клавіатура з товарами та кнопкою "Назад"
                keyboard = get_products_keyboard(products, category_parent_id=category.parent_id)

                # Перевіряємо чи це фото-повідомлення
                if callback.message.photo:
                    # Якщо фото - видаляємо і створюємо нове
                    chat_id = callback.message.chat.id
                    await callback.message.delete()
                    await callback.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    # Якщо текст - редагуємо
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
            else:
                text = f"📦 <b>{category.name}</b>\n\n"
                text += "У цій категорії поки немає товарів."

                # Клавіатура тільки з кнопкою "Назад"
                keyboard = get_products_keyboard([], category_parent_id=category.parent_id)

                # Перевіряємо чи це фото-повідомлення
                if callback.message.photo:
                    # Якщо фото - видаляємо і створюємо нове
                    chat_id = callback.message.chat.id
                    await callback.message.delete()
                    await callback.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                else:
                    # Якщо текст - редагуємо
                    await callback.message.edit_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )

    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def callback_product(callback: CallbackQuery):
    """
    Показує детальну інформацію про товар з фото
    """
    # Отримуємо ID товару з callback_data (формат: "product:123")
    product_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Формуємо текст з деталями товару
        text = f"<b>{product.name}</b>\n\n"

        if product.description:
            text += f"{product.description}\n\n"

        if product.price:
            text += f"💰 <b>Ціна:</b> {product.price:.2f} грн\n"

        text += f"✅ <b>Наявність:</b> {'В наявності' if product.available else 'Немає в наявності'}\n"

        # Клавіатура з управлінням кількості
        keyboard = get_product_detail_keyboard(
            product_id=product.id,
            category_id=product.category_id,
            quantity=1,  # За замовчуванням 1
            product_url=product.product_url  # URL товару на сайті
        )

        # Якщо є фото - показуємо з фото
        if product.image_url:
            # Видаляємо попереднє повідомлення
            await callback.message.delete()

            # Відправляємо нове з фото
            await callback.message.answer_photo(
                photo=product.image_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Якщо немає фото - просто текст
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

    await callback.answer()


@router.callback_query(F.data.startswith("product_qty:"))
async def callback_product_qty(callback: CallbackQuery):
    """
    Змінює кількість товару (➕ або ➖)
    """
    # Формат: "product_qty:123:5:inc" або "product_qty:123:5:dec"
    parts = callback.data.split(":")
    product_id = int(parts[1])
    current_qty = int(parts[2])
    action = parts[3]  # "inc" або "dec"

    # Змінюємо кількість
    if action == "inc":
        new_qty = current_qty + 1
    elif action == "dec":
        new_qty = max(1, current_qty - 1)  # Мінімум 1
    else:
        await callback.answer("❌ Невірна дія", show_alert=True)
        return

    async with get_session() as session:
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Оновлюємо клавіатуру з новою кількістю
        keyboard = get_product_detail_keyboard(
            product_id=product.id,
            category_id=product.category_id,
            quantity=new_qty,
            product_url=product.product_url
        )

        # Оновлюємо клавіатуру (текст залишається той самий)
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception:
            # Якщо не можна редагувати (наприклад, фото) - ігноруємо
            pass

    await callback.answer()


@router.callback_query(F.data.startswith("add_to_cart:"))
async def callback_add_to_cart(callback: CallbackQuery):
    """
    Додає товар в кошик
    TODO: Поки що просто показує повідомлення, реальний кошик буде пізніше
    """
    # Формат: "add_to_cart:123:5"
    parts = callback.data.split(":")
    product_id = int(parts[1])
    quantity = int(parts[2])

    async with get_session() as session:
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Показуємо повідомлення про успішне додавання
        message = f"✅ Додано до кошика:\n{product.name}\nКількість: {quantity} шт"

        if product.price:
            total = product.price * quantity
            message += f"\nВартість: {total:.2f} грн"

        await callback.answer(message, show_alert=True)


@router.callback_query(F.data == "ignore")
async def callback_ignore(callback: CallbackQuery):
    """
    Обробник для неклікабельних кнопок (показ кількості)
    """
    await callback.answer()
