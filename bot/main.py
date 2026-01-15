"""
КРОК 5: Telegram бот з меню та клавіатурами

Що нового в цьому кроці:
- ✅ Reply клавіатура (головне меню)
- ✅ Inline клавіатури (кнопки з callback)
- ✅ Роутери для модульної організації (start, menu)
- ✅ Обробники меню (Каталог, Кошик, Інформація, Налаштування)

Що було раніше:
- ✅ Крок 1: Мінімальний бот з /start
- ✅ Крок 2: Конфігурація через .env файл
- ✅ Крок 3: Логування через стандартну бібліотеку logging
- ✅ Крок 4: База даних (SQLAlchemy 2.0)

Що потрібно для запуску:
1. Файл .env з BOT_TOKEN (створіть з .env.example)
2. Встановлені залежності: aiogram, pydantic-settings, sqlalchemy, aiosqlite

Як запустити:
    python -m bot.main

Структура проекту:
- bot/handlers/ - обробники (start, menu)
- bot/keyboards/ - клавіатури (reply, inline)
- bot/models/ - моделі БД (User)
- bot/database.py - робота з БД
- bot/config.py - конфігурація
- bot/logger.py - логування
"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# КРОК 2: Імпортуємо налаштування
from bot.config import settings

# КРОК 3: Імпортуємо logger
from bot.logger import logger

# КРОК 4: Імпортуємо БД
from bot.database import init_db, close_db, get_session
from bot.middlewares import PhoneCheckMiddleware
from bot.handlers import start_router, menu_router, catalog_router, ai_consultation_router

# ========================================
# КРОК 2: Токен тепер з .env файлу!
# ========================================
# Більше не пишемо токен в коді!
# settings.BOT_TOKEN читається з .env файлу автоматично
#
# Як це працює:
# 1. Python імпортує bot.config
# 2. config.py читає .env файл
# 3. Pydantic перевіряє що BOT_TOKEN є
# 4. settings.BOT_TOKEN містить токен з .env
#
# Переваги:
# ✅ Токен не в Git (безпечно!)
# ✅ Легко змінювати (просто .env)
# ✅ Різні токени для dev/prod


# ========================================
# КРОК 5: Обробники винесено в окремі модулі
# ========================================


# ========================================
# ШАГ 1.3: Головна функція запуску
# ========================================
async def main():
    """
    Головна функція, яка запускає бота

    Що відбувається:
    1. Ініціалізація БД (КРОК 4)
    2. Створюється об'єкт бота з токеном
    3. Створюється диспетчер (обробник повідомлень)
    4. Реєструється обробник для /start
    5. Запускається polling (бот постійно перевіряє нові повідомлення)
    6. При зупинці - закриття БД та бота
    """

    # ========================================
    # КРОК 4: Ініціалізація бази даних
    # ========================================
    await init_db()

    # Крок 1: Створення бота
    logger.info("🤖 Створюю бота...")
    # КРОК 2: Використовуємо токен з config (з .env файлу)
    bot = Bot(token=settings.BOT_TOKEN)

    # Крок 2: Створення диспетчера з FSM storage
    logger.info("📦 Створюю диспетчер...")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Крок 2.5: Підключення middleware
    logger.info("🔒 Підключаю middleware перевірки номера телефону...")
    dp.message.middleware(PhoneCheckMiddleware())
    dp.callback_query.middleware(PhoneCheckMiddleware())
    logger.info("✅ Middleware підключено")

    # Крок 3: Реєстрація обробників
    logger.info("🔧 Реєструю обробники...")
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(catalog_router)
    dp.include_router(ai_consultation_router)
    logger.info("✅ Роутери підключено: start, menu, catalog, ai_consultation")

    # Крок 4: Видалення webhook (якщо був)
    logger.info("🧹 Очищаю webhook...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Крок 5: Отримання інформації про бота
    me = await bot.get_me()
    logger.info(f"✅ Бот @{me.username} успішно запущено!")
    logger.info("📡 Очікую повідомлення...")

    # Крок 6: Запуск polling (нескінченний цикл отримання повідомлень)
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.warning("⚠️  Отримано сигнал зупинки (Ctrl+C)...")
    finally:
        # Закриваємо сесію бота
        await bot.session.close()
        logger.info("👋 Бот зупинено!")

        # ========================================
        # КРОК 4: Закриття бази даних
        # ========================================
        await close_db()


# ========================================
# ШАГ 1.4: Точка входу
# ========================================
if __name__ == "__main__":
    """
    Ця частина виконується коли ми запускаємо файл напряму

    asyncio.run(main()) - запускає асинхронну функцію main()

    КРОК 3: Тепер використовуємо logger замість print
    """
    # КРОК 3: Логер вже налаштовано через bot.logger
    # При імпорті logger автоматично викликається setup_logger()

    logger.info("=" * 50)
    logger.info("🌾 FERM BOT - КРОК 5: Меню та клавіатури")
    logger.info("=" * 50)

    # КРОК 2-3: Інформація про конфігурацію
    # Перевірка токена тепер в config.py!
    # Якщо немає .env або BOT_TOKEN - Pydantic викине помилку автоматично
    logger.info("📝 Конфігурація завантажена:")
    logger.info(f"   DEBUG = {settings.DEBUG}")
    logger.info(f"   LOG_LEVEL = {settings.LOG_LEVEL}")
    logger.info(f"   LOG_TO_FILE = {settings.LOG_TO_FILE}")
    logger.info(f"   BOT_TOKEN = {'*' * 20}...{settings.BOT_TOKEN[-4:] if len(settings.BOT_TOKEN) > 4 else '***'}")

    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Це вже оброблено в main(), просто виходимо
        pass
    except Exception as e:
        # КРОК 3: Логуємо критичну помилку з повним traceback
        logger.exception(f"💥 Критична помилка при запуску бота:")
        exit(1)