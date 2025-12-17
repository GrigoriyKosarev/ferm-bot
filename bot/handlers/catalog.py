"""
Обробники для роботи з каталогом товарів
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database import get_session
from bot.queries import (
    get_subcategories, get_category_by_id, get_products_by_category, get_product_by_id,
    add_to_cart, search_products, count_search_results, count_products_by_category
)
from bot.keyboards.inline import get_categories_keyboard_from_db, get_products_keyboard, get_product_detail_keyboard
from bot.states import SearchStates

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

        keyboard = get_categories_keyboard_from_db(categories, show_search=True)

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
            limit = 10
            offset = 0
            products = await get_products_by_category(session, category_id, limit=limit, offset=offset)
            total_count = await count_products_by_category(session, category_id)

            if products:
                text = f"📦 <b>{category.name}</b>\n\n"
                text += f"Знайдено товарів: {total_count}\n\n"
                text += "Оберіть товар для перегляду деталей:"

                # Клавіатура з товарами, пагінацією та кнопкою "Назад"
                keyboard = get_products_keyboard(
                    products,
                    category_parent_id=category.parent_id,
                    category_id=category_id,
                    offset=offset,
                    limit=limit,
                    total_count=total_count
                )

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
    Додає товар в кошик (реальне збереження в БД)
    """
    # Формат: "add_to_cart:123:5"
    parts = callback.data.split(":")
    product_id = int(parts[1])
    quantity = int(parts[2])
    user_id = callback.from_user.id

    async with get_session() as session:
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Додаємо товар в кошик (або оновлюємо кількість)
        cart_item = await add_to_cart(session, user_id, product_id, quantity)

        # Показуємо повідомлення про успішне додавання
        message = f"✅ Додано до кошика:\n{product.name}\nКількість: {cart_item.quantity} шт"

        if product.price:
            total = product.price * cart_item.quantity
            message += f"\nВартість: {total:.2f} грн"

        await callback.answer(message, show_alert=True)


@router.callback_query(F.data == "ignore")
async def callback_ignore(callback: CallbackQuery):
    """
    Обробник для неклікабельних кнопок (показ кількості)
    """
    await callback.answer()


# ========================================
# ПАГІНАЦІЯ ТОВАРІВ
# ========================================

@router.callback_query(F.data.startswith("page:"))
async def callback_pagination(callback: CallbackQuery):
    """
    Обробник пагінації товарів - перехід між сторінками

    Формат callback_data: "page:category_id:offset"
    """
    # Розбираємо callback_data
    parts = callback.data.split(":")
    category_id = int(parts[1])
    offset = int(parts[2])
    limit = 10

    async with get_session() as session:
        # Отримуємо категорію та товари
        category = await get_category_by_id(session, category_id)

        if not category:
            await callback.answer("❌ Категорію не знайдено", show_alert=True)
            return

        products = await get_products_by_category(session, category_id, limit=limit, offset=offset)
        total_count = await count_products_by_category(session, category_id)

        if not products:
            await callback.answer("❌ Товари не знайдено", show_alert=True)
            return

        # Формуємо текст
        text = f"📦 <b>{category.name}</b>\n\n"
        text += f"Знайдено товарів: {total_count}\n\n"
        text += "Оберіть товар для перегляду деталей:"

        # Створюємо клавіатуру з пагінацією
        keyboard = get_products_keyboard(
            products,
            category_parent_id=category.parent_id,
            category_id=category_id,
            offset=offset,
            limit=limit,
            total_count=total_count
        )

        # Оновлюємо повідомлення
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()


# ========================================
# ПОШУК ТОВАРІВ
# ========================================

@router.callback_query(F.data == "search_start")
async def callback_search_start(callback: CallbackQuery, state: FSMContext):
    """
    Початок пошуку товарів - запит на введення пошукового запиту
    """
    await state.set_state(SearchStates.waiting_for_query)

    await callback.message.edit_text(
        "🔍 <b>Пошук товарів</b>\n\n"
        "Введіть назву або опис товару для пошуку:\n\n"
        "Наприклад: <code>добриво</code>, <code>насіння</code>, <code>захист</code>\n\n"
        "Для скасування натисніть /start",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(SearchStates.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    """
    Обробка пошукового запиту від користувача
    """
    query = message.text.strip()

    # Перевірка на команди
    if query.startswith("/"):
        await state.clear()
        return

    # Мінімальна довжина запиту
    if len(query) < 2:
        await message.answer(
            "❌ Занадто короткий запит.\n"
            "Введіть мінімум 2 символи для пошуку."
        )
        return

    async with get_session() as session:
        # Пошук товарів
        products = await search_products(session, query, limit=20)
        total_count = await count_search_results(session, query)

        if not products:
            text = (
                f"🔍 <b>Результати пошуку</b>\n\n"
                f"За запитом <b>«{query}»</b> нічого не знайдено.\n\n"
                f"Спробуйте змінити запит або перегляньте каталог."
            )

            from bot.queries import get_root_categories
            categories = await get_root_categories(session)
            keyboard = get_categories_keyboard_from_db(categories, show_search=True)

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            # Формуємо список знайдених товарів
            text = f"🔍 <b>Результати пошуку</b>\n\n"
            text += f"За запитом <b>«{query}»</b> знайдено: <b>{total_count}</b> товарів\n\n"

            if total_count > 20:
                text += f"<i>Показано перші 20 результатів</i>\n\n"

            # Створюємо клавіатуру з товарами
            # Використовуємо category_parent_id=None щоб показати кнопку "До меню"
            keyboard = get_products_keyboard(products, category_parent_id=None)

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    # Очищаємо стан FSM
    await state.clear()
