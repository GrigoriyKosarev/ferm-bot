from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавіатура для запиту номера телефону

    Returns:
        ReplyKeyboardMarkup: Клавіатура з кнопкою запиту контакту
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поділитися номером", request_contact=True)],
            # [KeyboardButton(text="⏭ Продовжити без номера")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
