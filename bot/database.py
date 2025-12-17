"""
КРОК 4: Підключення до бази даних через SQLAlchemy 2.0

Що таке база даних (БД)?
- Місце для збереження даних (користувачі, замовлення, тощо)
- Дані зберігаються навіть після зупинки бота
- Можна шукати, оновлювати, видаляти дані

Що таке SQLAlchemy?
- ORM (Object-Relational Mapping) для Python
- Дозволяє працювати з БД через Python класи (моделі)
- Версія 2.0 має async підтримку (для aiogram)

Що таке async (асинхронність)?
- Бот може обробляти багато запитів одночасно
- Не чекає поки закінчиться запит до БД
- Aiogram теж async, тому БД має бути async

Приклад використання:
    from bot.database import init_db, get_session

    # Ініціалізація БД при запуску бота
    await init_db()

    # Отримання сесії для роботи з БД
    async with get_session() as session:
        # Тут виконуємо запити до БД
        user = await session.get(User, user_id)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import settings
from bot.logger import logger


# ========================================
# БАЗОВИЙ КЛАС ДЛЯ МОДЕЛЕЙ
# ========================================
# КРОК 6: Базовий клас для всіх моделей
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовий клас для всіх моделей БД

    Всі моделі (User, Category, Product) наслідуються від цього класу
    DeclarativeBase автоматично створює таблиці та відстежує зміни
    """
    pass


# ========================================
# ГЛОБАЛЬНІ ЗМІННІ
# ========================================
# Ці змінні будуть ініціалізовані в init_db()

engine: AsyncEngine | None = None
"""
Движок (Engine) - підключення до БД

Що робить:
- Керує pool (басейном) з'єднань до БД
- Виконує SQL запити
- Один engine на весь додаток
"""

async_session_maker: async_sessionmaker[AsyncSession] | None = None
"""
Фабрика сесій - створює нові сесії для роботи з БД

Що таке сесія (Session):
- Тимчасове з'єднання з БД для виконання операцій
- Відстежує зміни в об'єктах
- Після закінчення роботи - закривається

Аналогія:
- Engine = з'єднання з БД (одне на додаток)
- Session = робоча сесія (нова для кожного запиту)
"""


# ========================================
# ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ
# ========================================
async def init_db() -> None:
    """
    Ініціалізує базу даних

    Що робить:
    1. Створює engine (підключення до БД)
    2. Створює session_maker (фабрику сесій)
    3. Створює всі таблиці з моделей (якщо їх немає)

    Викликається ОДИН РАЗ при запуску бота

    Приклад:
        await init_db()
    """
    global engine, async_session_maker

    logger.info(f"🗄️  Підключаюсь до БД: {settings.DATABASE_URL}")

    # ========================================
    # Крок 1: Створення engine
    # ========================================
    engine = create_async_engine(
        url=settings.DATABASE_URL,

        # echo=True - виводити всі SQL запити в консоль
        # Корисно для відладки, але багато тексту!
        echo=settings.DEBUG,

        # pool_size - скільки з'єднань тримати відкритими
        # max_overflow - скільки додаткових з'єднань можна створити
        pool_size=5,        # 5 постійних з'єднань
        max_overflow=10,    # +10 тимчасових якщо потрібно
    )

    # ========================================
    # Крок 2: Створення session maker
    # ========================================
    async_session_maker = async_sessionmaker(
        bind=engine,

        # class_=AsyncSession - тип сесії (async)
        class_=AsyncSession,

        # expire_on_commit=False - об'єкти залишаються доступними після commit
        # True - потрібно повторно завантажувати з БД після commit
        expire_on_commit=False,
    )

    # ========================================
    # Крок 3: Створення таблиць
    # ========================================
    logger.info("📝 Створюю таблиці БД (якщо їх немає)...")

    async with engine.begin() as conn:
        # Base.metadata.create_all - створює ВСІ таблиці з моделей
        # drop_all - видаляє існуючі таблиці (обережно! втратяться дані!)
        # await conn.run_sync(Base.metadata.drop_all)  # Розкоментуйте щоб видалити таблиці

        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ База даних готова до роботи!")

    # КРОК 6: Додаємо тестові дані якщо БД порожня
    await seed_data()


# ========================================
# SEED-ДАНІ (тестові категорії та товари)
# ========================================
async def seed_data() -> None:
    """
    Додає тестові дані в БД (категорії та товари)

    Викликається автоматично після init_db()
    Якщо дані вже є - нічого не робить
    """
    if async_session_maker is None:
        return

    from bot.models import Category, Product
    from sqlalchemy import select

    async with async_session_maker() as session:
        # Перевіряємо чи є вже категорії
        result = await session.execute(select(Category))
        exists = result.scalars().first()

        if exists:
            logger.debug("Seed-дані вже є в БД")
            return

        logger.info("📝 Додаю тестові категорії та товари...")

        # ========================================
        # КАТЕГОРІЇ (3-рівнева ієрархія)
        # ========================================
        categories = []

        # Рівень 1: Головні категорії
        cat_fertilizers = Category(name="Добрива")
        cat_protection = Category(name="Засоби захисту рослин (ЗЗР)")
        cat_seeds = Category(name="Насіння")
        categories.extend([cat_fertilizers, cat_protection, cat_seeds])

        session.add_all(categories)
        await session.flush()  # Отримуємо ID для parent

        # Рівень 2: Підкатегорії Добрив
        cat_micro = Category(name="Мікродобрива", parent_id=cat_fertilizers.id)
        cat_organic = Category(name="Органічні добрива", parent_id=cat_fertilizers.id)
        cat_mineral = Category(name="Основні мінеральні добрива", parent_id=cat_fertilizers.id)

        # Рівень 2: Підкатегорії ЗЗР
        cat_inoculants = Category(name="Інокулянти", parent_id=cat_protection.id)
        cat_bio = Category(name="Біопрепарати", parent_id=cat_protection.id)
        cat_insecticides = Category(name="Інсектициди", parent_id=cat_protection.id)
        cat_adjuvants = Category(name="Ад'юванти", parent_id=cat_protection.id)
        cat_herbicides = Category(name="Гербіциди", parent_id=cat_protection.id)
        cat_fungicides = Category(name="Фунгіциди", parent_id=cat_protection.id)

        # Рівень 2: Підкатегорії Насіння
        cat_legumes = Category(name="Бобові", parent_id=cat_seeds.id)
        cat_cereals = Category(name="Зернові", parent_id=cat_seeds.id)
        cat_oilseeds = Category(name="Олійні", parent_id=cat_seeds.id)

        subcategories = [
            cat_micro, cat_organic, cat_mineral,
            cat_inoculants, cat_bio, cat_insecticides, cat_adjuvants, cat_herbicides, cat_fungicides,
            cat_legumes, cat_cereals, cat_oilseeds,
        ]
        session.add_all(subcategories)
        await session.flush()

        # ========================================
        # ТОВАРИ (тестові мікродобрива)
        # ========================================
        products = [
            Product(
                name="Мікродобриво UltraStart марка А, 20 кг",
                description="Мікрогранульоване стартове добриво для локального внесення. "
                           "Забезпечує культури збалансованим живленням з першого дня.",
                price=2320.00,
                image_url="https://ferm.in.ua/getimage/products/au3l-a2kasi_5r1(1).webp",
                product_url="https://ferm.in.ua/ua/p1985735515-mikrodobrivo-ultrastart-marka.html",
                category_id=cat_micro.id,
                available=True,
            ),
            Product(
                name="Мікродобриво Інтермаг Олійні, 20 л",
                description="Рідке мікродобриво для позакореневого підживлення соняшника, "
                           "ріпаку, гірчиці, льону та інших олійних культур.",
                price=3950.00,
                image_url="https://ferm.in.ua/getimage/products/lb89ubuyxb4pqmn(1).webp",
                product_url="https://ferm.in.ua/ua/p1770933449-mikrodobrivo-intermag-olijni.html",
                category_id=cat_micro.id,
                available=True,
            ),
            Product(
                name="Мікродобриво Avangard Crystalmax B-21, 10 кг",
                description="Водорозчинне мікродобриво з високим вмістом бору (20,8%). "
                           "Спеціально розроблене для підживлення соняшника.",
                price=1950.00,
                image_url="https://ferm.in.ua/getimage/products/xiql7fcsy1x2zqb(1).webp",
                product_url="https://ferm.in.ua/ua/p1985735542-mikrodobrivo-avangard-crystalmax.html",
                category_id=cat_micro.id,
                available=True,
            ),
        ]

        session.add_all(products)
        await session.commit()

        logger.info(f"✅ Додано {len(categories) + len(subcategories)} категорій та {len(products)} товарів")


# ========================================
# ОТРИМАННЯ СЕСІЇ
# ========================================
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager для отримання сесії БД

    Використовується з async with для автоматичного закриття сесії

    Що робить:
    1. Створює нову сесію
    2. Повертає її для роботи
    3. Автоматично закриває після використання

    Приклад:
        async with get_session() as session:
            user = await session.get(User, 123)
            user.name = "Нове ім'я"
            await session.commit()
        # Тут сесія вже закрита автоматично

    Yields:
        AsyncSession: Сесія для роботи з БД

    Raises:
        RuntimeError: Якщо БД не ініціалізована (не викликали init_db)
    """
    if async_session_maker is None:
        raise RuntimeError(
            "База даних не ініціалізована! "
            "Спочатку викличте await init_db()"
        )

    # Створюємо нову сесію
    async with async_session_maker() as session:
        try:
            # Повертаємо сесію для роботи
            yield session

        except Exception as e:
            # Якщо сталась помилка - rollback (відміна змін)
            logger.error(f"❌ Помилка при роботі з БД: {e}")
            await session.rollback()
            raise

        finally:
            # Закриваємо сесію (відбувається автоматично через async with)
            await session.close()


# ========================================
# ЗАКРИТТЯ ПІДКЛЮЧЕННЯ
# ========================================
async def close_db() -> None:
    """
    Закриває підключення до БД

    Викликається при зупинці бота

    Що робить:
    - Закриває всі активні з'єднання
    - Очищає pool з'єднань

    Приклад:
        await close_db()
    """
    global engine

    if engine:
        logger.info("👋 Закриваю підключення до БД...")
        await engine.dispose()
        logger.info("✅ Підключення до БД закрито")


# ========================================
# ПРИКЛАДИ ВИКОРИСТАННЯ
# ========================================
"""
В bot/main.py при запуску бота:

    from bot.database import init_db, close_db

    async def main():
        # Ініціалізація БД
        await init_db()

        try:
            # Запуск бота
            await dp.start_polling(bot)
        finally:
            # Закриття БД при зупинці
            await close_db()

В обробниках (handlers):

    from bot.database import get_session
    from bot.models import User

    async def cmd_start(message: Message):
        # Отримуємо сесію
        async with get_session() as session:
            # Шукаємо користувача
            user = await session.get(User, message.from_user.id)

            if not user:
                # Створюємо нового користувача
                user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                )
                session.add(user)
                await session.commit()

        await message.answer("Привіт!")

Переваги цього підходу:
✅ Async (працює з aiogram)
✅ Автоматичне закриття сесій (через context manager)
✅ Pool з'єднань (ефективне використання ресурсів)
✅ Відстеження помилок та rollback
✅ Легко перейти з SQLite на PostgreSQL (просто змінити DATABASE_URL)
"""
