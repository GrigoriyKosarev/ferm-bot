"""
Клавіатури для бота
"""

from bot.keyboards.reply import get_main_menu
from bot.keyboards.inline import get_info_keyboard, get_categories_keyboard_from_db

__all__ = [
    "get_main_menu",
    "get_info_keyboard",
    "get_categories_keyboard_from_db",
]
