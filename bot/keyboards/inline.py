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


def get_categories_keyboard_from_db(categories: list, parent_id: int = None) -> InlineKeyboardMarkup:
    """
    КРОК 6: Inline клавіатура категорій з БД

    Args:
        categories: Список об'єктів Category з БД
        parent_id: ID батьківської категорії (для кнопки "Назад")

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
        # Якщо це головні категорії - кнопка "До меню"
        builder.row(
            InlineKeyboardButton(
                text="🏠 До головного меню",
                callback_data="back_to_menu"
            )
        )

    return builder.as_markup()


def get_products_keyboard(products: list, category_parent_id: int = None) -> InlineKeyboardMarkup:
    """
    Inline клавіатура для списку товарів категорії

    Args:
        products: Список об'єктів Product з БД
        category_parent_id: ID батьківської категорії для кнопки "Назад"

    Returns:
        InlineKeyboardMarkup: Список товарів з кнопкою "Назад"
    """
    builder = InlineKeyboardBuilder()

    # Кнопки товарів (поки просто показуємо список)
    for product in products:
        builder.button(
            text=f"📦 {product.name}",
            callback_data=f"product:{product.id}"
        )

    # По 1 товару в ряд (бо назви довгі)
    builder.adjust(1)

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
