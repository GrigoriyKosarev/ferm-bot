"""
КРОК 6: Запити до бази даних

CRUD операції для Category та Product
"""

from typing import List, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Category, Product, CartItem


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
    from sqlalchemy.orm import joinedload

    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(joinedload(Product.category))  # Eager load category
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def search_products(
        session: AsyncSession,
        query: str,
        limit: int = 10,
        offset: int = 0
) -> List[Product]:
    """
    Пошук товарів по назві та опису

    Args:
        query: Пошуковий запит
        limit: Кількість товарів на сторінку
        offset: Зміщення (для пагінації)

    Returns:
        List[Product]: Список знайдених товарів
    """
    search_pattern = f"%{query}%"
    stmt = (
        select(Product)
        .where(Product.available == True)
        .where(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )
        .order_by(Product.name)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_search_results(
        session: AsyncSession,
        query: str
) -> int:
    """
    Підрахунок кількості результатів пошуку

    Args:
        query: Пошуковий запит

    Returns:
        int: Кількість знайдених товарів
    """
    search_pattern = f"%{query}%"
    stmt = (
        select(func.count(Product.id))
        .where(Product.available == True)
        .where(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def count_products_by_category(
        session: AsyncSession,
        category_id: int
) -> int:
    """
    Підрахунок кількості товарів в категорії

    Args:
        category_id: ID категорії

    Returns:
        int: Кількість товарів
    """
    stmt = (
        select(func.count(Product.id))
        .where(Product.category_id == category_id)
        .where(Product.available == True)
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


# ============= КОШИК =============

async def add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        quantity: int = 1
) -> CartItem:
    """
    Додати товар в кошик або оновити кількість якщо вже є

    Args:
        user_id: Telegram ID користувача
        product_id: ID товару
        quantity: Кількість для додавання

    Returns:
        CartItem: Елемент кошика
    """
    # Перевіряємо чи товар вже є в кошику
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .where(CartItem.product_id == product_id)
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        # Товар вже є - збільшуємо кількість
        cart_item.quantity += quantity
    else:
        # Нового товару немає - створюємо
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
        session.add(cart_item)

    await session.commit()
    await session.refresh(cart_item)
    return cart_item


async def get_cart(
        session: AsyncSession,
        user_id: int
) -> List[CartItem]:
    """
    Отримати всі товари з кошика користувача

    Args:
        user_id: Telegram ID користувача

    Returns:
        List[CartItem]: Список товарів в кошику
    """
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.created_at)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def remove_from_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> bool:
    """
    Видалити товар з кошика

    Args:
        user_id: Telegram ID користувача
        product_id: ID товару

    Returns:
        bool: True якщо видалено, False якщо товару не було
    """
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .where(CartItem.product_id == product_id)
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        await session.delete(cart_item)
        await session.commit()
        return True
    return False


async def clear_cart(
        session: AsyncSession,
        user_id: int
) -> int:
    """
    Очистити весь кошик користувача

    Args:
        user_id: Telegram ID користувача

    Returns:
        int: Кількість видалених товарів
    """
    stmt = select(CartItem).where(CartItem.user_id == user_id)
    result = await session.execute(stmt)
    cart_items = result.scalars().all()

    count = len(list(cart_items))
    for item in cart_items:
        await session.delete(item)

    await session.commit()
    return count


async def update_cart_quantity(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        quantity: int
) -> Optional[CartItem]:
    """
    Оновити кількість товару в кошику

    Args:
        user_id: Telegram ID користувача
        product_id: ID товару
        quantity: Нова кількість

    Returns:
        CartItem або None якщо товару немає в кошику
    """
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .where(CartItem.product_id == product_id)
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        if quantity <= 0:
            # Якщо кількість 0 або менше - видаляємо товар
            await session.delete(cart_item)
        else:
            cart_item.quantity = quantity
        await session.commit()
        return cart_item if quantity > 0 else None
    return None
