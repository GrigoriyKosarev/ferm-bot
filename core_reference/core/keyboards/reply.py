"""
Reply клавіатури (кнопки внизу екрану)

Використовуються для постійного меню,
яке завжди доступне користувачу
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Головне меню бота

    Відображається при /start та завжди доступне користувачу

    Returns:
        ReplyKeyboardMarkup: Клавіатура головного меню
    """
    keyboard = [
        # Перший ряд - основні функції
        [
            KeyboardButton(text="🛒 Каталог товарів"),
            KeyboardButton(text="🌤 АгроПогода")
        ],
        # Другий ряд - консультації та підтримка
        [
            KeyboardButton(text="💡 Консультація ШІ"),
            KeyboardButton(text="💰 АгроГранти")
        ],
        # Третій ряд - додаткові сервіси
        [
            KeyboardButton(text="🚜 Оренда техніки"),
            KeyboardButton(text="🛍 Кошик")
        ],
        # Четвертий ряд - довідка
        [
            KeyboardButton(text="ℹ️ Допомога")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,  # Автоматичний розмір кнопок
        input_field_placeholder="Оберіть розділ...",  # Підказка в полі вводу
        one_time_keyboard=False  # Клавіатура не зникає після використання
    )


def get_back_button() -> ReplyKeyboardMarkup:
    """
    Кнопка "Назад до меню"

    Використовується в підрозділах для повернення

    Returns:
        ReplyKeyboardMarkup: Клавіатура з кнопкою "Назад"
    """
    keyboard = [
        [KeyboardButton(text="◀️ Назад до меню")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_cancel_button() -> ReplyKeyboardMarkup:
    """
    Кнопка "Скасувати"

    Використовується під час заповнення форм (FSM)

    Returns:
        ReplyKeyboardMarkup: Клавіатура зі скасуванням
    """
    keyboard = [
        [KeyboardButton(text="❌ Скасувати")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_location_request() -> ReplyKeyboardMarkup:
    """
    Кнопка для надсилання геолокації

    Використовується для точного визначення локації для погоди

    Returns:
        ReplyKeyboardMarkup: Клавіатура з запитом локації
    """
    keyboard = [
        [KeyboardButton(text="📍 Надіслати мою локацію", request_location=True)],
        [KeyboardButton(text="✍️ Ввести назву міста вручну")],
        [KeyboardButton(text="◀️ Назад до меню")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True  # Зникає після використання
    )


def get_contact_request() -> ReplyKeyboardMarkup:
    """
    Кнопка для надсилання контакту

    Використовується при заповненні заявок
    для автоматичного отримання номеру телефону

    Returns:
        ReplyKeyboardMarkup: Клавіатура з запитом контакту
    """
    keyboard = [
        [KeyboardButton(text="📱 Надіслати мій номер", request_contact=True)],
        [KeyboardButton(text="✍️ Ввести номер вручну")],
        [KeyboardButton(text="❌ Скасувати")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавіатура підтвердження дії

    Використовується для важливих дій (очищення кошика тощо)

    Returns:
        ReplyKeyboardMarkup: Клавіатура Так/Ні
    """
    keyboard = [
        [
            KeyboardButton(text="✅ Так"),
            KeyboardButton(text="❌ Ні")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )