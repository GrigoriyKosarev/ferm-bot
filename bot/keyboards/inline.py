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


def get_categories_keyboard_from_db(categories: list) -> InlineKeyboardMarkup:
    """
    КРОК 6: Inline клавіатура головних категорій з БД

    Args:
        categories: Список об'єктів Category з БД

    Returns:
        InlineKeyboardMarkup: Категорії товарів
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

    return builder.as_markup()
