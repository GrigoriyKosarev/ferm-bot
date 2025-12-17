"""
КРОК 5: Reply клавіатури (кнопки в чаті)

Що таке Reply клавіатура?
- Кнопки знизу екрану (замінюють клавіатуру)
- Натискання кнопки = відправлення тексту
- Завжди видимі користувачу

Відмінність від Inline клавіатур:
- Reply: знизу екрану, замінюють клавіатуру
- Inline: під повідомленням, callback запити
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Головне меню бота (Reply клавіатура)

    Returns:
        ReplyKeyboardMarkup: Клавіатура з основними кнопками
    """
    builder = ReplyKeyboardBuilder()

    # Додаємо кнопки
    builder.button(text="📦 Каталог")
    builder.button(text="🛒 Кошик")

    # Розміщення: 2 кнопки в ряд
    builder.adjust(2)

    return builder.as_markup(
        resize_keyboard=True,  # Компактний розмір
        input_field_placeholder="Оберіть дію з меню"  # Підказка
    )
