"""
Налаштування з'єднання з базою даних

Використовується SQLAlchemy async для асинхронної роботи з БД
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from loguru import logger

from core.config import settings
from core.database.models import Base

# Створення async engine
# echo=True виводить SQL запити в консоль (для DEBUG)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # Для SQLite використовуємо NullPool
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
)

# Фабрика для створення сесій
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Об'єкти не експіруються після commit
    autoflush=False,
    autocommit=False,
)


async def init_db():
    """
    Ініціалізація бази даних

    Створює всі таблиці згідно з моделями.
    Викликається при старті бота.
    """
    try:
        async with engine.begin() as conn:
            # Створення всіх таблиць
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База даних успішно ініціалізована")
    except Exception as e:
        logger.error(f"❌ Помилка ініціалізації бази даних: {e}")
        raise


async def get_session() -> AsyncSession:
    """
    Отримання сесії бази даних

    Використовується як async context manager:
    async with get_session() as session:
        # робота з БД

    Returns:
        AsyncSession: Асинхронна сесія для роботи з БД
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Помилка в сесії БД: {e}")
            raise
        finally:
            await session.close()


async def close_db():
    """
    Закриття з'єднання з базою даних

    Викликається при зупинці бота для коректного завершення
    """
    await engine.dispose()
    logger.info("🔌 З'єднання з базою даних закрито")