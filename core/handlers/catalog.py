"""
Обробник каталогу товарів

Функції:
- Відображення категорій і підкатегорій
- Перегляд товарів з пагінацією
- Детальна інформація про товар
- Розрахунок норм застосування
- Акції
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from core.config import CATEGORIES, settings
from core.keyboards.inline import (
    get_categories_keyboard,
    get_subcategories_keyboard,
    get_products_keyboard,
    get_product_actions_keyboard,
    get_promotions_keyboard
)
from core.database.database import AsyncSessionLocal
from core.database.queries import add_to_cart, get_cart_items, track_product_view
from core.services.ferm_api import FermAPI

# Створення роутера
router = Router(name="catalog")

# Ініціалізація API клієнта
ferm_api = FermAPI()


# ============= FSM СТАНИ =============

class CatalogStates(StatesGroup):
    """Стани для роботи з каталогом"""
    viewing_products = State()  # Перегляд списку товарів
    viewing_product = State()  # Перегляд конкретного товару
    calculating_rate = State()  # Розрахунок норм застосування
    entering_area = State()  # Введення площі для розрахунку


# ============= КАТЕГОРІЇ =============

@router.callback_query(F.data.startswith("category:"))
async def show_subcategories(callback: CallbackQuery, state: FSMContext):
    """
    Відображення підкатегорій обраної категорії

    Callback format: category:{category_key}
    """
    # Отримати ключ категорії
    category_key = callback.data.split(":")[1]

    # Перевірка чи існує категорія
    if category_key not in CATEGORIES:
        await callback.answer("❌ Категорія не знайдена", show_alert=True)
        return

    category_data = CATEGORIES[category_key]

    # Формування тексту
    text = (
        f"<b>{category_data['name']}</b>\n\n"
        f"Оберіть підкатегорію для перегляду товарів:"
    )

    # Збереження категорії в стані
    await state.update_data(current_category=category_key)

    # Відправка повідомлення
    await callback.message.edit_text(
        text,
        reply_markup=get_subcategories_keyboard(category_key)
    )
    await callback.answer()


@router.callback_query(F.data == "back:categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Повернення до списку категорій"""

    # Очистити стан
    await state.clear()

    text = (
        "<b>🛒 Каталог товарів FERM</b>\n\n"
        "Оберіть категорію:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()


# ============= ПІДКАТЕГОРІЇ ТА ТОВАРИ =============

@router.callback_query(F.data.startswith("subcat:"))
async def show_products(callback: CallbackQuery, state: FSMContext):
    """
    Відображення списку товарів підкатегорії

    Callback format: subcat:{category}:{subcategory}
    """
    # Парсинг callback
    parts = callback.data.split(":")
    category = parts[1]
    subcategory = parts[2]

    # Збереження в стані
    await state.update_data(
        current_category=category,
        current_subcategory=subcategory,
        current_page=1
    )
    await state.set_state(CatalogStates.viewing_products)

    # Отримання товарів з API
    try:
        products_data = await ferm_api.get_products(
            category=category,
            subcategory=subcategory,
            page=1,
            per_page=settings.PRODUCTS_PER_PAGE
        )

        products = products_data.get('products', [])
        total_pages = products_data.get('pages', 1)

        if not products:
            text = (
                "<b>😔 Товари не знайдено</b>\n\n"
                "На жаль, у цій категорії поки немає товарів.\n"
                "Спробуйте іншу категорію або зайдіть пізніше."
            )
            await callback.message.edit_text(text)
            await callback.answer()
            return

        # Формування тексту зі списком товарів
        text = f"<b>📦 Товари ({len(products)} шт.)</b>\n\n"
        for idx, product in enumerate(products, 1):
            availability = "✅ В наявності" if product.get('in_stock') else "❌ Немає в наявності"
            text += (
                f"{idx}. <b>{product['name']}</b>\n"
                f"   💰 {product['price']} грн/{product.get('unit', 'шт')}\n"
                f"   {availability}\n\n"
            )

        # Відправка з клавіатурою
        await callback.message.edit_text(
            text,
            reply_markup=get_products_keyboard(
                products=products,
                category=category,
                subcategory=subcategory,
                page=1,
                total_pages=total_pages
            )
        )

    except Exception as e:
        logger.error(f"Помилка отримання товарів: {e}")
        await callback.answer(
            "❌ Помилка завантаження товарів. Спробуйте пізніше.",
            show_alert=True
        )
        return

    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def change_page(callback: CallbackQuery, state: FSMContext):
    """
    Пагінація товарів

    Callback format: page:{category}:{subcategory}:{page_num}
    """
    parts = callback.data.split(":")
    category = parts[1]
    subcategory = parts[2]
    page = int(parts[3])

    # Отримання товарів
    try:
        products_data = await ferm_api.get_products(
            category=category,
            subcategory=subcategory,
            page=page,
            per_page=settings.PRODUCTS_PER_PAGE
        )

        products = products_data.get('products', [])
        total_pages = products_data.get('pages', 1)

        # Оновлення сторінки в стані
        await state.update_data(current_page=page)

        # Формування тексту
        text = f"<b>📦 Товари - Сторінка {page}/{total_pages}</b>\n\n"
        for idx, product in enumerate(products, 1):
            availability = "✅" if product.get('in_stock') else "❌"
            text += (
                f"{idx}. <b>{product['name']}</b>\n"
                f"   💰 {product['price']} грн | {availability}\n\n"
            )

        # Оновлення повідомлення
        await callback.message.edit_text(
            text,
            reply_markup=get_products_keyboard(
                products=products,
                category=category,
                subcategory=subcategory,
                page=page,
                total_pages=total_pages
            )
        )

    except Exception as e:
        logger.error(f"Помилка пагінації: {e}")
        await callback.answer("❌ Помилка", show_alert=True)
        return

    await callback.answer()


# ============= ДЕТАЛІ ТОВАРУ =============

@router.callback_query(F.data.startswith("product:"))
async def show_product_details(callback: CallbackQuery, state: FSMContext):
    """
    Детальна інформація про товар

    Callback format: product:{product_id}
    """
    # Отримати ID товару
    product_id = int(callback.data.split(":")[1])

    # Збереження в стані
    await state.update_data(current_product_id=product_id)
    await state.set_state(CatalogStates.viewing_product)

    try:
        # Отримання деталей товару з API
        product = await ferm_api.get_product(product_id)

        # Реєстрація перегляду для аналітики
        async with AsyncSessionLocal() as session:
            await track_product_view(
                session=session,
                user_id=callback.from_user.id,
                product_id=product_id,
                category=product.get('category'),
                source="catalog"
            )

        # Перевірка чи товар вже в кошику
        async with AsyncSessionLocal() as session:
            cart_items = await get_cart_items(session, callback.from_user.id)
            in_cart = any(item.product_id == product_id for item in cart_items)

        # Формування тексту
        availability = "✅ <b>В наявності</b>" if product.get('in_stock') else "❌ <b>Немає в наявності</b>"

        text = (
            f"<b>{product['name']}</b>\n\n"
            f"💰 <b>Ціна:</b> {product['price']} грн/{product.get('unit', 'шт')}\n"
            f"📦 <b>Наявність:</b> {availability}\n\n"
            f"<b>📝 Опис:</b>\n{product.get('description', 'Опис відсутній')}\n\n"
        )

        # Додаткові характеристики (якщо є)
        if 'attributes' in product and product['attributes']:
            text += "<b>📊 Характеристики:</b>\n"
            for key, value in product['attributes'].items():
                text += f"• {key}: {value}\n"
            text += "\n"

        # Якщо є фото - відправляємо з фото, якщо ні - просто текст
        if 'images' in product and product['images']:
            # Відправка з фото
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product['images'][0],
                caption=text,
                reply_markup=get_product_actions_keyboard(
                    product_id=product_id,
                    in_cart=in_cart,
                    category=product.get('category'),
                    subcategory=product.get('subcategory')
                )
            )
        else:
            # Без фото
            await callback.message.edit_text(
                text,
                reply_markup=get_product_actions_keyboard(
                    product_id=product_id,
                    in_cart=in_cart,
                    category=product.get('category'),
                    subcategory=product.get('subcategory')
                )
            )

    except Exception as e:
        logger.error(f"Помилка отримання товару {product_id}: {e}")
        await callback.answer(
            "❌ Помилка завантаження товару",
            show_alert=True
        )
        return

    await callback.answer()


# ============= ДОДАВАННЯ ДО КОШИКА =============

@router.callback_query(F.data.startswith("cart:add:"))
async def add_product_to_cart(callback: CallbackQuery, state: FSMContext):
    """
    Додавання товару до кошика

    Callback format: cart:add:{product_id}
    """
    product_id = int(callback.data.split(":")[2])

    try:
        # Отримати деталі товару
        product = await ferm_api.get_product(product_id)

        # Додати до кошика в БД
        async with AsyncSessionLocal() as session:
            await add_to_cart(
                session=session,
                user_id=callback.from_user.id,
                product_id=product_id,
                product_name=product['name'],
                product_price=product['price'],
                quantity=1.0,
                unit=product.get('unit', 'шт'),
                product_image=product.get('images', [None])[0],
                category=product.get('category'),
                subcategory=product.get('subcategory')
            )

        logger.info(f"Товар {product_id} додано до кошика користувача {callback.from_user.id}")

        # Оновити клавіатуру (показати що товар вже в кошику)
        await callback.message.edit_reply_markup(
            reply_markup=get_product_actions_keyboard(
                product_id=product_id,
                in_cart=True,
                category=product.get('category'),
                subcategory=product.get('subcategory')
            )
        )

        # Повідомлення користувачу
        await callback.answer(
            f"✅ {product['name']} додано до кошика!",
            show_alert=False
        )

    except Exception as e:
        logger.error(f"Помилка додавання до кошика: {e}")
        await callback.answer(
            "❌ Помилка додавання до кошика",
            show_alert=True
        )


@router.callback_query(F.data.startswith("cart:already:"))
async def already_in_cart(callback: CallbackQuery):
    """Товар вже в кошику"""
    await callback.answer(
        "ℹ️ Цей товар вже у вашому кошику",
        show_alert=False
    )


"""
Продовження catalog.py
Розрахунок норм застосування та акції
"""


# ============= РОЗРАХУНОК НОРМ =============

@router.callback_query(F.data.startswith("calculate:"))
async def start_calculation(callback: CallbackQuery, state: FSMContext):
    """
    Початок розрахунку норм застосування

    Callback format: calculate:{product_id}
    """
    product_id = int(callback.data.split(":")[1])

    # Збереження ID товару в стані
    await state.update_data(calculating_product_id=product_id)
    await state.set_state(CatalogStates.entering_area)

    # Отримати назву товару
    try:
        product = await ferm_api.get_product(product_id)
        product_name = product['name']
    except:
        product_name = "обраного товару"

    text = (
        f"<b>📊 Розрахунок норм застосування</b>\n\n"
        f"Товар: <b>{product_name}</b>\n\n"
        f"Для розрахунку необхідної кількості товару,\n"
        f"введіть площу вашого господарства в <b>гектарах</b>:\n\n"
        f"<i>Наприклад: 100 або 150.5</i>"
    )

    from core.keyboards.reply import get_cancel_button

    await callback.message.answer(
        text,
        reply_markup=get_cancel_button()
    )
    await callback.answer()


@router.message(CatalogStates.entering_area)
async def process_area_calculation(message: Message, state: FSMContext):
    """
    Обробка введеної площі та розрахунок норм
    """
    # Перевірка на скасування
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer(
            "❌ Розрахунок скасовано",
            reply_markup=get_main_menu()
        )
        return

    # Спроба розпарсити число
    try:
        area = float(message.text.replace(",", ".").strip())

        if area <= 0:
            await message.answer(
                "❌ Площа має бути більше нуля. Спробуйте ще раз:"
            )
            return

        if area > 100000:  # Обмеження на розумну площу
            await message.answer(
                "❌ Занадто велика площа. Перевірте введені дані:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Невірний формат. Введіть число (наприклад: 100 або 50.5):"
        )
        return

    # Отримати дані з стану
    data = await state.get_data()
    product_id = data.get('calculating_product_id')

    if not product_id:
        await message.answer("❌ Помилка. Почніть розрахунок заново.")
        await state.clear()
        return

    # Отримати товар
    try:
        product = await ferm_api.get_product(product_id)
    except Exception as e:
        logger.error(f"Помилка отримання товару для розрахунку: {e}")
        await message.answer(
            "❌ Помилка отримання даних товару",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return

    # ===== РОЗРАХУНОК НОРМ =====
    # Тут має бути логіка розрахунку або виклик ШІ
    # Для прикладу використаємо просту формулу

    # Приблизна норма (це приклад, реально має братися з характеристик товару)
    rate_per_ha = product.get('application_rate', 2.5)  # кг/га
    total_needed = area * rate_per_ha

    # Округлення до упаковок (якщо відома вага упаковки)
    package_size = product.get('package_size', 25)  # кг
    packages_needed = round(total_needed / package_size + 0.5)  # Округлення вгору
    total_packages_weight = packages_needed * package_size

    # Розрахунок вартості
    price_per_unit = product['price']
    total_cost = (total_packages_weight / package_size) * price_per_unit

    # Формування результату
    result_text = (
        f"<b>📊 Результат розрахунку</b>\n\n"
        f"<b>Товар:</b> {product['name']}\n"
        f"<b>Площа:</b> {area} га\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>📦 Норма внесення:</b> {rate_per_ha} кг/га\n"
        f"<b>💼 Необхідно:</b> ~{total_needed:.1f} кг\n\n"
        f"<b>📦 Рекомендована кількість упаковок:</b>\n"
        f"   {packages_needed} шт × {package_size} кг = {total_packages_weight} кг\n\n"
        f"<b>💰 Орієнтовна вартість:</b> ~{total_cost:.2f} грн\n\n"
        f"<i>⚠️ Це орієнтовний розрахунок. Для точних рекомендацій "
        f"враховуйте тип ґрунту, культуру та погодні умови.</i>"
    )

    # Клавіатура з діями
    from core.keyboards.inline import get_product_actions_keyboard
    keyboard = get_product_actions_keyboard(
        product_id=product_id,
        in_cart=False  # Можна перевірити чи вже в кошику
    )

    from core.keyboards.reply import get_main_menu

    await message.answer(
        result_text,
        reply_markup=keyboard
    )

    # Повернення головного меню знизу
    await message.answer(
        "Оберіть дію:",
        reply_markup=get_main_menu()
    )

    # Очистити стан
    await state.clear()

    logger.info(f"Розраховано норми для товару {product_id}, площа {area} га")


# ============= СУПУТНІ ТОВАРИ =============

@router.callback_query(F.data.startswith("related:"))
async def show_related_products(callback: CallbackQuery):
    """
    Показ супутніх товарів (рекомендації)

    Callback format: related:{product_id}
    """
    product_id = int(callback.data.split(":")[1])

    try:
        # Отримати супутні товари з API
        related_products = await ferm_api.get_related_products(product_id)

        if not related_products:
            await callback.answer(
                "ℹ️ Супутні товари не знайдені",
                show_alert=True
            )
            return

        # Формування списку
        text = "<b>💡 Рекомендуємо додати до замовлення:</b>\n\n"

        for idx, product in enumerate(related_products, 1):
            text += (
                f"{idx}. <b>{product['name']}</b>\n"
                f"   💰 {product['price']} грн\n"
                f"   <i>{product.get('short_description', '')}</i>\n\n"
            )

        text += (
            "Ці товари доповнюють вашу покупку "
            "та допоможуть досягти кращих результатів! 🌱"
        )

        # Створити клавіатуру з товарами
        builder = InlineKeyboardBuilder()
        for product in related_products:
            builder.button(
                text=f"👁 {product['name'][:30]}...",
                callback_data=f"product:{product['id']}"
            )

        builder.button(
            text="◀️ Назад до товару",
            callback_data=f"product:{product_id}"
        )

        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        logger.error(f"Помилка отримання супутніх товарів: {e}")
        await callback.answer(
            "❌ Помилка завантаження рекомендацій",
            show_alert=True
        )

    await callback.answer()


# ============= АКЦІЇ =============

@router.callback_query(F.data == "promotions")
async def show_promotions(callback: CallbackQuery):
    """
    Відображення акцій
    """
    try:
        # Отримати акції з API
        promotions = await ferm_api.get_promotions(limit=10)

        if not promotions:
            text = (
                "<b>🔥 Акції</b>\n\n"
                "На даний момент активних акцій немає.\n"
                "Підпишіться на розсилку, щоб не пропустити вигідні пропозиції!"
            )
            await callback.message.edit_text(text)
            await callback.answer()
            return

        # Формування списку акцій
        text = "<b>🔥 Актуальні акції FERM</b>\n\n"

        for promo in promotions:
            discount_text = f"-{promo.get('discount')}%" if promo.get('discount') else "Спеціальна пропозиція"

            text += (
                f"🎁 <b>{promo['title']}</b>\n"
                f"   {discount_text}\n"
                f"   <i>{promo.get('description', '')}</i>\n"
                f"   ⏰ До: {promo.get('valid_until', 'уточнюйте')}\n\n"
            )

        # Відправка з клавіатурою
        await callback.message.edit_text(
            text,
            reply_markup=get_promotions_keyboard(promotions)
        )

    except Exception as e:
        logger.error(f"Помилка отримання акцій: {e}")
        await callback.answer(
            "❌ Помилка завантаження акцій",
            show_alert=True
        )
        return

    await callback.answer()


@router.callback_query(F.data.startswith("promo:"))
async def show_promotion_details(callback: CallbackQuery):
    """
    Детальна інформація про акцію

    Callback format: promo:{promo_id}
    """
    promo_id = int(callback.data.split(":")[1])

    try:
        # Тут має бути метод API для отримання деталей акції
        # Для прикладу використаємо загальний список
        promotions = await ferm_api.get_promotions()
        promo = next((p for p in promotions if p['id'] == promo_id), None)

        if not promo:
            await callback.answer("❌ Акція не знайдена", show_alert=True)
            return

        discount_text = f"<b>Знижка:</b> -{promo.get('discount')}%" if promo.get('discount') else ""

        text = (
            f"<b>🔥 {promo['title']}</b>\n\n"
            f"{promo.get('description', '')}\n\n"
            f"{discount_text}\n"
            f"<b>⏰ Діє до:</b> {promo.get('valid_until', 'уточнюйте')}\n\n"
            f"<b>📦 Товари в акції:</b> {len(promo.get('products', []))} шт.\n\n"
            f"<i>Натисніть кнопку нижче, щоб переглянути товари акції</i>"
        )

        from core.keyboards.inline import get_promotion_actions

        await callback.message.edit_text(
            text,
            reply_markup=get_promotion_actions(
                promo_id=promo_id,
                product_ids=promo.get('products', [])
            )
        )

    except Exception as e:
        logger.error(f"Помилка отримання деталей акції: {e}")
        await callback.answer("❌ Помилка", show_alert=True)

    await callback.answer()


# ============= НАВІГАЦІЯ =============

@router.callback_query(F.data.startswith("back:"))
async def handle_back_navigation(callback: CallbackQuery, state: FSMContext):
    """
    Універсальний обробник навігації "Назад"

    Callback format: back:{destination}:{params}
    """
    parts = callback.data.split(":")
    destination = parts[1]

    if destination == "subcategories":
        # Назад до підкатегорій
        category = parts[2] if len(parts) > 2 else None
        if category:
            data = await state.get_data()
            category = data.get('current_category', category)

            category_data = CATEGORIES.get(category, {})
            text = f"<b>{category_data.get('name', 'Категорія')}</b>\n\nОберіть підкатегорію:"

            await callback.message.edit_text(
                text,
                reply_markup=get_subcategories_keyboard(category)
            )

    elif destination == "products":
        # Назад до списку товарів
        category = parts[2] if len(parts) > 2 else None
        subcategory = parts[3] if len(parts) > 3 else None

        if category and subcategory:
            # Перезавантажити список товарів
            # (можна викликати show_products, але через state)
            await callback.answer("Завантаження...")

    await callback.answer()