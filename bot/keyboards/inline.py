"""
КРОК 5: Inline клавіатури (кнопки під повідомленням)

Що таке Inline клавіатура?
- Кнопки під конкретним повідомленням
- Натискання = callback запит (не текст)
- Можна редагувати повідомлення після натискання

Відмінність від Reply:
- Inline: під повідомленням, callback
- Reply: знизу екрану, текст
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_info_keyboard() -> InlineKeyboardMarkup:
    """
    Inline клавіатура для інформації про бота

    Returns:
        InlineKeyboardMarkup: Клавіатура з кнопками
    """
    builder = InlineKeyboardBuilder()

    # Кнопки з callback_data (для обробки)
    builder.button(text="📖 Про бота", callback_data="info_about")
    builder.button(text="❓ Допомога", callback_data="info_help")
    
    # Кнопка з посиланням (відкриває URL)
    builder.button(text="🔗 GitHub", url="https://github.com")

    # Розміщення: 2 кнопки в ряд, потім 1
    builder.adjust(2, 1)

    return builder.as_markup()


def get_categories_keyboard_from_db(categories: list, parent_id: int = None, show_search: bool = False) -> InlineKeyboardMarkup:
    """
    КРОК 6: Inline клавіатура категорій з БД

    Args:
        categories: Список об'єктів Category з БД
        parent_id: ID батьківської категорії (для кнопки "Назад")
        show_search: Показувати кнопку пошуку (тільки для головних категорій)

    Returns:
        InlineKeyboardMarkup: Категорії товарів з кнопкою "Назад"
    """
    builder = InlineKeyboardBuilder()

    for category in categories:
        # Додаємо емодзі для кращого вигляду
        icon_map = {
            "Добрива": "🧪",
            "Засоби захисту рослин": "🛡",
            "ЗЗР": "🛡",
            "Насіння": "🌾",
        }

        # Шукаємо емодзі для категорії
        icon = ""
        for key, emoji in icon_map.items():
            if key in category.name:
                icon = emoji
                break

        if not icon:
            icon = "📁"  # За замовчуванням

        button_text = f"{icon} {category.name}"

        builder.button(
            text=button_text,
            callback_data=f"category:{category.id}"
        )

    # По 2 кнопки в ряд
    builder.adjust(2)

    # Додаємо кнопку "Назад" якщо є батьківська категорія
    if parent_id is not None:
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"category:{parent_id}"
            )
        )
    else:
        # Якщо це головні категорії - додаємо кнопку пошуку
        if show_search:
            builder.row(
                InlineKeyboardButton(
                    text="🔍 Пошук товарів",
                    callback_data="search_start"
                )
            )

        # Кнопка "До меню"
        builder.row(
            InlineKeyboardButton(
                text="🏠 До головного меню",
                callback_data="back_to_menu"
            )
        )

    return builder.as_markup()


def get_products_keyboard(
        products: list,
        category_parent_id: int = None,
        category_id: int = None,
        offset: int = 0,
        limit: int = 10,
        total_count: int = 0
) -> InlineKeyboardMarkup:
    """
    Inline клавіатура для списку товарів категорії з пагінацією

    Args:
        products: Список об'єктів Product з БД
        category_parent_id: ID батьківської категорії для кнопки "Назад"
        category_id: ID поточної категорії (для пагінації)
        offset: Поточне зміщення (для пагінації)
        limit: Кількість товарів на сторінку
        total_count: Загальна кількість товарів в категорії

    Returns:
        InlineKeyboardMarkup: Список товарів з кнопкою "Назад" та пагінацією
    """
    builder = InlineKeyboardBuilder()

    # Кнопки товарів
    for product in products:
        builder.button(
            text=f"📦 {product.name}",
            callback_data=f"product:{product.id}"
        )

    # По 1 товару в ряд (бо назви довгі)
    builder.adjust(1)

    # Додаємо кнопки пагінації якщо потрібно
    if total_count > limit and category_id is not None:
        pagination_buttons = []

        # Кнопка "◀️ Попередня" якщо не на першій сторінці
        if offset > 0:
            prev_offset = max(0, offset - limit)
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Попередня",
                    callback_data=f"page:{category_id}:{prev_offset}"
                )
            )

        # Показуємо поточну сторінку
        current_page = (offset // limit) + 1
        total_pages = (total_count + limit - 1) // limit
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {current_page}/{total_pages}",
                callback_data="ignore"
            )
        )

        # Кнопка "Наступна ▶️" якщо не на останній сторінці
        if offset + limit < total_count:
            next_offset = offset + limit
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="Наступна ▶️",
                    callback_data=f"page:{category_id}:{next_offset}"
                )
            )

        # Додаємо рядок з пагінацією
        builder.row(*pagination_buttons)

    # Додаємо кнопку "Назад" до батьківської категорії
    if category_parent_id is not None:
        builder.row(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"category:{category_parent_id}"
            )
        )
    else:
        # Якщо немає батька - до головного меню
        builder.row(
            InlineKeyboardButton(
                text="🏠 До головного меню",
                callback_data="back_to_menu"
            )
        )

    return builder.as_markup()


def get_product_detail_keyboard(product_id: int, category_id: int, quantity: int = 1, product_url: str = None, application_rate: float = None, show_ai_button: bool = False) -> InlineKeyboardMarkup:
    """
    Inline клавіатура для детальної картки товару

    Args:
        product_id: ID товару
        category_id: ID категорії (для кнопки "Назад")
        quantity: Поточна кількість товару (за замовчуванням 1)
        product_url: URL товару на сайті (опціонально)
        application_rate: Норма застосування кг/га (опціонально)
        show_ai_button: Показувати кнопку AI-консультації (опціонально)

    Returns:
        InlineKeyboardMarkup: Клавіатура з управлінням кількості та кнопкою "Додати в кошик"
    """
    builder = InlineKeyboardBuilder()

    # Рядок 1: Управління кількістю
    builder.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"product_qty:{product_id}:{quantity}:dec"
        ),
        InlineKeyboardButton(
            text=f"📦 {quantity} шт",
            callback_data="ignore"  # Кнопка не клікабельна (показує кількість)
        ),
        InlineKeyboardButton(
            text="➕",
            callback_data=f"product_qty:{product_id}:{quantity}:inc"
        )
    )

    # Рядок 2: Додати в кошик
    builder.row(
        InlineKeyboardButton(
            text=f"🛒 Додати в кошик ({quantity} шт)",
            callback_data=f"add_to_cart:{product_id}:{quantity}"
        )
    )

    # Рядок 3: Розрахунок норм застосування (якщо є норма)
    if application_rate:
        builder.row(
            InlineKeyboardButton(
                text="📊 Розрахувати норму застосування",
                callback_data=f"calc_norm:{product_id}"
            )
        )

    # Рядок 4: AI-консультація (якщо увімкнено)
    if show_ai_button:
        builder.row(
            InlineKeyboardButton(
                text="🤖 Консультація з ШІ по товару",
                callback_data=f"ai_consult:{product_id}"
            )
        )

    # Рядок 5: Перейти на сайт (якщо є URL)
    if product_url:
        builder.row(
            InlineKeyboardButton(
                text="🌐 Перейти на сайт",
                url=product_url
            )
        )

    # Рядок 5: Назад до категорії
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад до списку",
            callback_data=f"category:{category_id}"
        )
    )

    return builder.as_markup()


def get_cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    """
    Inline клавіатура для перегляду кошика

    Args:
        cart_items: Список об'єктів CartItem з БД

    Returns:
        InlineKeyboardMarkup: Товари в кошику з кнопками управління
    """
    builder = InlineKeyboardBuilder()

    if not cart_items:
        # Кошик порожній - тільки кнопка "Назад"
        builder.row(
            InlineKeyboardButton(
                text="🏠 Головне меню",
                callback_data="cart_close"
            )
        )
        return builder.as_markup()

    # Кнопки для кожного товару в кошику
    for item in cart_items:
        # Рядок 1: Назва товару та кнопки управління
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 {item.product.name}",
                callback_data=f"cart_remove:{item.product_id}"
            )
        )
        # Рядок 2: Управління кількістю
        builder.row(
            InlineKeyboardButton(
                text="➖",
                callback_data=f"cart_qty:{item.product_id}:{item.quantity}:dec"
            ),
            InlineKeyboardButton(
                text=f"{item.quantity} шт",
                callback_data="ignore"
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart_qty:{item.product_id}:{item.quantity}:inc"
            )
        )

    # Кнопки внизу
    # Кнопка оформлення замовлення (відкриває сайт)
    builder.row(
        InlineKeyboardButton(
            text="✅ Оформити замовлення",
            url="https://ferm.in.ua/checkout.php"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Очистити кошик",
            callback_data="cart_clear"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 Головне меню",
            callback_data="cart_close"
        )
    )

    return builder.as_markup()
