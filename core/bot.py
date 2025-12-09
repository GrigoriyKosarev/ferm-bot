"""
Головний файл FERM Telegram Bot

Ініціалізація бота, підключення всіх компонентів та запуск
"""
import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from core.config import settings
from core.database.database import init_db, close_db

# Імпорт всіх роутерів (handlers)
from core.handlers import (
    start,
    # catalog,
    # cart,
    # weather,
    # grants,
    # consultation
)

# ============= НАЛАШТУВАННЯ ЛОГУВАННЯ =============

logger.remove()  # Видалити стандартний handler

# Консольне логування з кольорами
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True
)

# Логування у файл
logger.add(
    "logs/bot_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # Новий файл щодня о півночі
    retention="30 days",  # Зберігати логи 30 днів
    compression="zip",  # Стискати старі логи
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)


# ============= ІНІЦІАЛІЗАЦІЯ БОТА =============

async def on_startup(bot: Bot):
    """
    Виконується при запуску бота

    - Ініціалізація бази даних
    - Повідомлення адміну про запуск (опціонально)
    """
    logger.info("🚀 Запуск FERM Telegram Bot...")

    # Ініціалізація БД
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Помилка ініціалізації БД: {e}")
        raise

    # Отримати інформацію про бота
    bot_info = await bot.get_me()
    logger.success(f"✅ Бот @{bot_info.username} успішно запущено!")

    # Можна відправити повідомлення адміну (якщо потрібно)
    # await bot.send_message(settings.ADMIN_ID, "🤖 Бот запущено!")


async def on_shutdown(bot: Bot):
    """
    Виконується при зупинці бота

    - Закриття з'єднань з БД
    - Повідомлення адміну (опціонально)
    """
    logger.info("🛑 Зупинка бота...")

    await close_db()

    logger.success("✅ Бот коректно зупинено")


# ============= ГОЛОВНА ФУНКЦІЯ =============

async def main():
    """
    Головна функція запуску бота

    1. Створення бота та диспетчера
    2. Підключення роутерів (handlers)
    3. Запуск polling або webhook
    """

    # Створення бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML  # Дозволяє використовувати HTML в повідомленнях
        )
    )

    # Storage для FSM (Finite State Machine)
    # У продакшені краще використовувати Redis
    storage = MemoryStorage()

    # Створення диспетчера
    dp = Dispatcher(storage=storage)

    # ============= ПІДКЛЮЧЕННЯ РОУТЕРІВ =============
    # Порядок важливий! start має бути першим

    dp.include_router(start.router)  # Команди /start, /help, головне меню
    # dp.include_router(catalog.router)  # Каталог товарів, категорії, підкатегорії
    # dp.include_router(cart.router)  # Кошик, додавання/видалення товарів
    # dp.include_router(weather.router)  # АгроПогода, підписки
    # dp.include_router(grants.router)  # АгроГранти, заявки
    # dp.include_router(consultation.router)  # ШІ-консультації

    logger.info("📦 Всі роутери підключено")

    # ============= CALLBACK'И ЖИТТЄВОГО ЦИКЛУ =============

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # ============= ЗАПУСК БОТА =============

    try:
        # Видалення webhook якщо був встановлений
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔄 Webhook видалено, використовується polling")

        # Запуск polling (для розробки)
        if not settings.WEBHOOK_ENABLED:
            logger.info("📡 Запуск в режимі polling...")
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types()
            )

        # Запуск webhook (для продакшену)
        else:
            from aiohttp import web

            logger.info(f"🌐 Запуск webhook на {settings.WEBHOOK_URL}")

            # Встановлення webhook
            await bot.set_webhook(
                url=f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}",
                drop_pending_updates=True
            )

            # Створення веб-додатку
            app = web.Application()

            # Додавання webhook handler
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot
            )
            webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)

            setup_application(app, dp, bot=bot)

            # Запуск веб-сервера
            web.run_app(
                app,
                host=settings.WEBAPP_HOST,
                port=settings.WEBAPP_PORT
            )

    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")
        raise

    finally:
        # Закриття сесії бота
        await bot.session.close()
        logger.info("👋 До побачення!")


# ============= ТОЧКА ВХОДУ =============

if __name__ == '__main__':
    """
    Запуск бота

    Команда: python -m core.bot
    або: poetry run python -m core.bot
    або: make run
    """
    try:
        # Запуск через asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("⚠️ Отримано KeyboardInterrupt, зупинка...")
    except Exception as e:
        logger.critical(f"💥 Критична помилка при запуску: {e}")
        sys.exit(1)