from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from bot.database import get_session
from bot.logger import logger
from bot.models import User

from bot.keyboards import reply, inline
from bot.keyboards.phone import get_phone_keyboard


router = Router(name="start")

@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Функція, яка викликається коли користувач відправляє /start

    Параметри:
    - message: об'єкт повідомлення від користувача

    Що робить:
    - Отримує ім'я користувача (якщо є)
    - КРОК 4: Зберігає/оновлює користувача в БД
    - Відправляє привітальне повідомлення
    - Логує інформацію про користувача
    """
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "друже"

    # КРОК 3: Логуємо що користувач запустив бота
    logger.info(f"👤 Користувач {user_name} (ID: {user_id}) відправив /start")

    # ========================================
    # КРОК 6: Робота з базою даних (оновлено для core/database)
    # ========================================
    async with get_session() as session:
        # Шукаємо користувача по user_id (telegram_id)
        # ВАЖЛИВО: session.get() працює тільки з PRIMARY KEY (id)
        # Тому використовуємо select() з фільтром по user_id
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Користувач вже є - оновлюємо дані
            logger.info(f"📝 Оновлюю дані користувача {user_id}")
            user.username = message.from_user.username
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            is_new_user = False
        else:
            # Новий користувач - створюємо запис
            logger.info(f"➕ Створюю нового користувача {user_id}")
            user = User(
                user_id=user_id,  # КРОК 6: Поле тепер називається user_id
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            session.add(user)
            is_new_user = True

        # Зберігаємо зміни в БД
        await session.commit()

    # Формуємо текст відповіді
    if is_new_user:
        text = (
            f"Привіт, {user_name}! 👋\n\n"
            f"Ти вперше запустив бота!\n"
            f"Я зберіг твої дані в базі даних."
        )
    else:
        text = (
            f"З поверненням, {user_name}! 👋\n\n"
            f"Я оновив твої дані в базі даних."
        )

    need_phone = user.phone_number is None

    if need_phone:
        text = (
            "\n\n🔔 Щоб продовжити необхідно поділитися номером телефону."
        )

        await message.answer(text, reply_markup=get_phone_keyboard())
    else:
        await message.answer(text, reply_markup=reply.get_main_menu())

    # # Відправляємо відповідь користувачу
    # await message.answer(text, reply_markup=reply.get_main_menu())
    # # await message.answer(text)

    # КРОК 3: Логуємо що відповідь надіслано
    logger.debug(f"✉️  Відповідь на /start надіслано користувачу {user_id}")


@router.message(F.text == "📦 Каталог")
async def show_catalog(message: Message):
    """Відображення каталогу товарів"""
    from bot.queries import get_root_categories
    from bot.database import get_session
    from bot.keyboards.inline import get_categories_keyboard_from_db

    logger.info(f"Користувач {message.from_user.id} відкрив каталог")

    async with get_session() as session:
        categories = await get_root_categories(session)

        if not categories:
            await message.answer(
                "😔 <b>Каталог порожній</b>\n\n"
                "База даних ще не заповнена."
            )
            return

        text = (
            "<b>🛒 Каталог товарів FERM</b>\n\n"
            "Оберіть категорію для перегляду товарів:"
        )

        await message.answer(
            text,
            reply_markup=get_categories_keyboard_from_db(categories, show_search=True),
            parse_mode="HTML"
        )

@router.message(F.contact)
async def handle_contact(message: Message):
    contact = message.contact

    # 🔐 Захист
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Будь ласка, поділіться СВОЇМ номером")
        return

    phone = contact.phone_number
    user_id = message.from_user.id

    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one()

        user.phone_number = phone
        await session.commit()

    await message.answer(
        "✅ Дякую! Номер збережено.",
        reply_markup=reply.get_main_menu()
    )