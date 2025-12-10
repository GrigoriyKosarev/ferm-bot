"""
Async Database Engine & Session (SQLAlchemy 2.0)
"""
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from loguru import logger

from core.config import settings
from core.database.models import Category, Product

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator yielding DB session.
    Usage:
        async for session in get_session(): ...
        or as dependency in frameworks.

    Example:
        async with get_session() as session:
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Перевірка — чи таблиця порожня
        result = await session.execute(select(Category))
        exists = result.scalars().first()

        if exists:
            return  # Дані вже є, нічого не робимо

        # Категорії додаємо
        cats = []

        root1 = Category(name="Добрива")
        cats.append(root1)
        md = Category(name="Мікродобрива", parent=root1)
        cats.append(md)
        od = Category(name="Органічні добрива", parent=root1)
        cats.append(od)
        cats.append(Category(name="Основні мінеральні добрива", parent=root1))

        root2 = Category(name="Засоби захисту рослин (ЗЗР)")
        cats.append(root2)
        cats.append(Category(name="Інокулянти", parent=root2))
        cats.append(Category(name="Біопрепарати", parent=root2))
        cats.append(Category(name="Інсектициди", parent=root2))
        cats.append(Category(name="Ад’юванти", parent=root2))
        cats.append(Category(name="Гербіциди", parent=root2))
        cats.append(Category(name="Протруйники", parent=root2))
        cats.append(Category(name="Фунгіциди", parent=root2))

        root3 = Category(name="Насіння")
        cats.append(root3)
        cats.append(Category(name="Бобові", parent=root3))
        cats.append(Category(name="Зернові", parent=root3))
        cats.append(Category(name="Оліійні", parent=root3))
        cats.append(Category(name="Насіння овочів", parent=root3))
        cats.append(Category(name="Насіння прямих та зелених культур", parent=root3))
        cats.append(Category(name="Нішеві культури", parent=root3))

        session.add_all(cats)
        await session.commit()

        data = []
        data.append(Product(
            name="Мікродобриво UltraStart (УльтраСтарт) марка А, 20 кг (Квадрат)",
            description="Мікродобриво UltraStart марка А — мікрогранульоване стартове добриво для локального внесення під час сівби. Забезпечує культури збалансованим живленням з першого дня, покращує розвиток коренів, проростання і стійкість до стресу. Працює за технологією POP-UP.",
            price=2320,
            image_url="https://ferm.in.ua/getimage/products/au3l-a2kasi_5r1(1).webp",
            category_id=md.id,
        ))
        data.append(Product(
            name="Мікродобриво Інтермаг Олійні, 20 л",
            description="Мікродобриво Інтермаг Олійні - рідке мікродобриво для позакореневого підживлення соняшника, ріпаку, гірчиці, льону та інших олійних культур. Містить збалансований набір поживних речовин, які підтримують рослину на всіх ключових етапах розвитку.",
            price=3950,
            image_url="https://ferm.in.ua/getimage/products/lb89ubuyxb4pqmn(1).webp",
            category_id=md.id,
        ))
        data.append(Product(
            name="Мікродобриво Avangard Crystalmax B-21 (Авангард Кристалмакс), 10 кг (Ukravit Science Park)",
            description="Avangard Crystalmax B-21 – водорозчинне мікродобриво з високим вмістом бору (20,8%), спеціально розроблене для підживлення соняшника. Сприяє формуванню квіток і плодів, підвищує врожайність та якість насіння, зміцнює імунітет рослин і знижує чутливість до стресів.",
            price=1950,
            image_url="https://ferm.in.ua/getimage/products/xiql7fcsy1x2zqb(1).webp",
            category_id=md.id,
        ))
        session.add_all(data)
        await session.commit()

async def init_db() -> None:
    """
    Initialize DB (create tables).
    Call once on startup.
    """
    from core.database.models import Base  # local import to avoid circular deps

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_data()
        logger.info("✅ База даних успішно ініціалізована")
    except Exception as e:
        logger.exception(f"❌ Помилка ініціалізації бази даних: {e}")
        raise


async def close_db() -> None:
    """
    Dispose engine on shutdown.
    """
    await engine.dispose()
    logger.info("🔌 З'єднання з базою даних закрито")
