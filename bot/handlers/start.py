"""
КРОК 5: Обробник команди /start

Що робить:
- Зберігає/оновлює користувача в БД
- Відправляє привітання
- Показує головне меню (Reply клавіатура)
"""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.database import get_session
from bot.models import User
from bot.keyboards import get_main_menu
from bot.logger import logger

# Створюємо Router для цього handler
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обробник команди /start
    
    Що робить:
    - Зберігає нового користувача або оновлює існуючого
    - Відправляє привітання з головним меню
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "друже"

    logger.info(f"👤 Користувач {user_name} (ID: {user_id}) відправив /start")

    # Робота з БД
    async with get_session() as session:
        user = await session.get(User, user_id)

        if user:
            # Оновлюємо дані
            logger.info(f"📝 Оновлюю дані користувача {user_id}")
            user.username = message.from_user.username
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            is_new_user = False
        else:
            # Створюємо нового
            logger.info(f"➕ Створюю нового користувача {user_id}")
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            session.add(user)
            is_new_user = True

        await session.commit()

    # Формуємо відповідь
    if is_new_user:
        text = (
            f"Привіт, {user_name}! 👋\n\n"
            f"Ти вперше запустив бота!\n"
            f"Обери дію з меню нижче:"
        )
    else:
        text = (
            f"З поверненням, {user_name}! 👋\n\n"
            f"Обери дію з меню:"
        )

    # Відправляємо з Reply клавіатурою
    await message.answer(text, reply_markup=get_main_menu())

    logger.debug(f"✉️  Відповідь надіслано з головним меню")
