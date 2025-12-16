"""
КРОК 6: Запити до бази даних

CRUD операції для Category та Product
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Category, Product


# ============= КАТЕГОРІЇ =============

async def get_root_categories(session: AsyncSession) -> List[Category]:
    """
    Отримати всі кореневі категорії (без parent_id)

    Returns:
        List[Category]: Список головних категорій (Добрива, ЗЗР, Насіння)
    """
    stmt = (
        select(Category)
        .where(Category.parent_id.is_(None))
        .order_by(Category.name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_subcategories(
        session: AsyncSession,
        parent_id: int
) -> List[Category]:
    """
    Отримати підкатегорії для батьківської категорії

    Args:
        parent_id: ID батьківської категорії

    Returns:
        List[Category]: Список підкатегорій
    """
    stmt = (
        select(Category)
        .where(Category.parent_id == parent_id)
        .order_by(Category.name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_category_by_id(
        session: AsyncSession,
        category_id: int
) -> Optional[Category]:
    """
    Отримати категорію за ID

    Args:
        category_id: ID категорії

    Returns:
        Category або None
    """
    stmt = select(Category).where(Category.id == category_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# ============= ТОВАРИ =============

async def get_products_by_category(
        session: AsyncSession,
        category_id: int,
        limit: int = 10,
        offset: int = 0
) -> List[Product]:
    """
    Отримати товари з категорії з пагінацією

    Args:
        category_id: ID категорії
        limit: Кількість товарів на сторінку
        offset: Зміщення (для пагінації)

    Returns:
        List[Product]: Список товарів
    """
    stmt = (
        select(Product)
        .where(Product.category_id == category_id)
        .where(Product.available == True)
        .order_by(Product.name)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_product_by_id(
        session: AsyncSession,
        product_id: int
) -> Optional[Product]:
    """
    Отримати товар за ID

    Args:
        product_id: ID товару

    Returns:
        Product або None
    """
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
