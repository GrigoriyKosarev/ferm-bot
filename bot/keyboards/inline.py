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
