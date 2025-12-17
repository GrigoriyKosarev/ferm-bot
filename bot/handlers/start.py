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
        # Користувач ще не поділився номером
        text += (
            "\n\n🔔 Щоб продовжити, будь ласка, поділіться номером телефону.\n"
            "Це потрібно для оформлення замовлень."
        )
        await message.answer(text, reply_markup=get_phone_keyboard())
        logger.debug(f"✉️  Запит номера телефону надіслано користувачу {user_id}")
    else:
        # Користувач вже має номер - показуємо головне меню
        await message.answer(text, reply_markup=reply.get_main_menu())
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
    """
    Обробник отримання контакту від користувача.
    Зберігає номер телефону в базу даних.

    Захист:
    - Приймає тільки власний контакт користувача
    - Перевіряє наявність користувача в БД
    """
    contact = message.contact
    user_id = message.from_user.id

    # 🔐 Захист від чужих контактів
    if contact.user_id != user_id:
        logger.warning(f"Користувач {user_id} спробував надіслати чужий контакт")
        await message.answer("❌ Будь ласка, поділіться СВОЇМ номером")
        return

    phone = contact.phone_number
    logger.info(f"Користувач {user_id} поділився номером телефону")

    try:
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"Користувач {user_id} не знайдений в БД при збереженні контакту")
                await message.answer(
                    "❌ Помилка: користувач не знайдений.\nСпробуйте /start",
                    reply_markup=reply.get_main_menu()
                )
                return

            # Зберігаємо номер телефону
            user.phone_number = phone
            await session.commit()

        logger.info(f"Номер телефону користувача {user_id} збережено: {phone}")

        await message.answer(
            "✅ Дякую! Номер телефону збережено.\n\n"
            "Тепер ви можете користуватися всіма функціями бота.",
            reply_markup=reply.get_main_menu()
        )

    except Exception as e:
        logger.error(f"Помилка при збереженні номера телефону користувача {user_id}: {e}")
        await message.answer(
            "❌ Сталася помилка при збереженні номера.\nСпробуйте ще раз або зверніться до підтримки.",
            reply_markup=reply.get_main_menu()
        )
