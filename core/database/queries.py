"""
CRUD операції у стилі SQLAlchemy 2.0 (async).
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from sqlalchemy import select, delete, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from loguru import logger

from core.database.models import (
    User, CartItem, GrantApplication, EquipmentRequest,
    ConsultationHistory, ProductView, Category, Product
)


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


async def get_category_by_name(
        session: AsyncSession,
        name: str
) -> Optional[Category]:
    """
    Отримати категорію за назвою

    Args:
        name: Назва категорії

    Returns:
        Category або None
    """
    stmt = select(Category).where(Category.name == name)
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


async def get_products_count_by_category(
        session: AsyncSession,
        category_id: int
) -> int:
    """
    Підрахунок товарів у категорії (для пагінації)

    Args:
        category_id: ID категорії

    Returns:
        int: Кількість товарів
    """
    from sqlalchemy import func

    stmt = (
        select(func.count(Product.id))
        .where(Product.category_id == category_id)
        .where(Product.available == True)
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_product_by_id(
        session: AsyncSession,
        product_id: int
) -> Optional[Product]:
    """
    Отримати товар за ID з інформацією про категорію

    Args:
        product_id: ID товару

    Returns:
        Product або None
    """
    stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def search_products(
        session: AsyncSession,
        query: str,
        limit: int = 10
) -> List[Product]:
    """
    Пошук товарів за назвою

    Args:
        query: Пошуковий запит
        limit: Максимальна кількість результатів

    Returns:
        List[Product]: Знайдені товари
    """
    search_pattern = f"%{query}%"

    stmt = (
        select(Product)
        .where(Product.name.ilike(search_pattern))
        .where(Product.available == True)
        .order_by(Product.name)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_all_products(
        session: AsyncSession,
        limit: int = 100
) -> List[Product]:
    """
    Отримати всі доступні товари

    Args:
        limit: Максимальна кількість

    Returns:
        List[Product]: Список товарів
    """
    stmt = (
        select(Product)
        .where(Product.available == True)
        .order_by(Product.category_id, Product.name)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ============= BREADCRUMBS (Навігація) =============

async def get_category_path(
        session: AsyncSession,
        category_id: int
) -> List[Category]:
    """
    Отримати повний шлях категорії (breadcrumbs)
    Наприклад: Добрива → Мікродобрива

    Args:
        category_id: ID категорії

    Returns:
        List[Category]: Список від кореня до поточної категорії
    """
    path = []
    current_id = category_id

    while current_id:
        category = await get_category_by_id(session, current_id)
        if not category:
            break
        path.insert(0, category)  # Вставляємо на початок
        current_id = category.parent_id

    return path

# ============= КОРИСТУВАЧІ =============

async def create_or_update_user(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
) -> User:
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.last_active = datetime.utcnow()
        logger.debug(f"Оновлено користувача: {user_id}")
    else:
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        logger.info(f"Створено нового користувача: {user_id}")

    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_location(
        session: AsyncSession,
        user_id: int,
        location: str,
        latitude: float,
        longitude: float,
        location_key: Optional[str] = None
) -> None:
    stmt = (
        update(User)
        .where(User.user_id == user_id)
        .values(
            saved_location=location,
            latitude=latitude,
            longitude=longitude,
            location_key=location_key
        )
    )
    await session.execute(stmt)
    await session.commit()
    logger.debug(f"Оновлено локацію користувача {user_id}: {location}")


async def update_user_subscriptions(
        session: AsyncSession,
        user_id: int,
        weather: Optional[bool] = None,
        grants: Optional[bool] = None,
        promotions: Optional[bool] = None
) -> None:
    values = {}
    if weather is not None:
        values['weather_subscription'] = weather
    if grants is not None:
        values['grants_subscription'] = grants
    if promotions is not None:
        values['promotions_subscription'] = promotions

    if values:
        stmt = update(User).where(User.user_id == user_id).values(**values)
        await session.execute(stmt)
        await session.commit()
        logger.debug(f"Оновлено підписки користувача {user_id}")


async def get_users_with_subscription(
        session: AsyncSession,
        subscription_type: str
) -> List[User]:
    field_map = {
        'weather': User.weather_subscription,
        'grants': User.grants_subscription,
        'promotions': User.promotions_subscription
    }

    if subscription_type not in field_map:
        return []

    stmt = select(User).where(
        and_(
            field_map[subscription_type] == True,
            User.is_blocked == False
        )
    )
    result = await session.execute(stmt)
    return result.scalars().all()


# ============= КОШИК =============

async def add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        product_name: str,
        product_price: float,
        quantity: float = 1.0,
        unit: str = "шт",
        product_image: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None
) -> CartItem:
    stmt = select(CartItem).where(
        and_(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id
        )
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        cart_item.quantity += quantity
        logger.debug(f"Збільшено кількість товару {product_id} до {cart_item.quantity}")
    else:
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            product_name=product_name,
            product_price=product_price,
            quantity=quantity,
            unit=unit,
            product_image=product_image,
            category=category,
            subcategory=subcategory
        )
        session.add(cart_item)
        logger.info(f"Додано товар {product_id} до кошика користувача {user_id}")

    await session.commit()
    await session.refresh(cart_item)
    return cart_item


async def get_cart_items(
        session: AsyncSession,
        user_id: int
) -> List[CartItem]:
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.added_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_cart_item_quantity(
        session: AsyncSession,
        cart_item_id: int,
        quantity: float
) -> None:
    stmt = (
        update(CartItem)
        .where(CartItem.id == cart_item_id)
        .values(quantity=quantity)
    )
    await session.execute(stmt)
    await session.commit()
    logger.debug(f"Оновлено кількість товару {cart_item_id}: {quantity}")


async def remove_from_cart(
        session: AsyncSession,
        cart_item_id: int,
        user_id: int
) -> None:
    stmt = delete(CartItem).where(
        and_(
            CartItem.id == cart_item_id,
            CartItem.user_id == user_id
        )
    )
    await session.execute(stmt)
    await session.commit()
    logger.debug(f"Видалено товар {cart_item_id} з кошика користувача {user_id}")


async def clear_cart(session: AsyncSession, user_id: int) -> None:
    stmt = delete(CartItem).where(CartItem.user_id == user_id)
    result = await session.execute(stmt)
    await session.commit()
    logger.info(f"Очищено кошик користувача {user_id}")


async def get_cart_summary(
        session: AsyncSession,
        user_id: int
) -> Dict:
    items = await get_cart_items(session, user_id)
    total_price = sum(item.product_price * item.quantity for item in items) if items else 0.0

    return {
        'total_items': len(items),
        'total_price': round(total_price, 2),
        'items': items
    }


# ============= ЗАЯВКИ НА ГРАНТИ =============

async def create_grant_application(
        session: AsyncSession,
        user_id: int,
        full_name: str,
        phone: str,
        email: Optional[str] = None,
        farm_size: Optional[float] = None,
        farm_type: Optional[str] = None,
        region: Optional[str] = None,
        district: Optional[str] = None,
        grant_program: Optional[str] = None,
        requested_amount: Optional[float] = None,
        purpose: Optional[str] = None,
        description: Optional[str] = None
) -> GrantApplication:
    application = GrantApplication(
        user_id=user_id,
        full_name=full_name,
        phone=phone,
        email=email,
        farm_size=farm_size,
        farm_type=farm_type,
        region=region,
        district=district,
        grant_program=grant_program,
        requested_amount=requested_amount,
        purpose=purpose,
        description=description
    )

    session.add(application)
    await session.commit()
    await session.refresh(application)

    logger.info(f"Створено заявку на грант #{application.id} від користувача {user_id}")
    return application


async def get_user_grant_applications(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
) -> List[GrantApplication]:
    stmt = (
        select(GrantApplication)
        .where(GrantApplication.user_id == user_id)
        .order_by(GrantApplication.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_grant_application_status(
        session: AsyncSession,
        application_id: int,
        status: str,
        admin_notes: Optional[str] = None
) -> None:
    stmt = (
        update(GrantApplication)
        .where(GrantApplication.id == application_id)
        .values(
            status=status,
            admin_notes=admin_notes,
            processed_at=datetime.utcnow()
        )
    )
    await session.execute(stmt)
    await session.commit()
    logger.info(f"Оновлено статус заявки #{application_id}: {status}")


# ============= ЗАЯВКИ НА ОРЕНДУ ТЕХНІКИ =============

async def create_equipment_request(
        session: AsyncSession,
        user_id: int,
        full_name: str,
        phone: str,
        equipment_type: str,
        email: Optional[str] = None,
        equipment_id: Optional[int] = None,
        equipment_model: Optional[str] = None,
        rental_start_date: Optional[datetime] = None,
        rental_duration: Optional[int] = None,
        rental_area: Optional[float] = None,
        location: Optional[str] = None,
        delivery_needed: bool = False,
        notes: Optional[str] = None
) -> EquipmentRequest:
    request = EquipmentRequest(
        user_id=user_id,
        full_name=full_name,
        phone=phone,
        email=email,
        equipment_type=equipment_type,
        equipment_id=equipment_id,
        equipment_model=equipment_model,
        rental_start_date=rental_start_date,
        rental_duration=rental_duration,
        rental_area=rental_area,
        location=location,
        delivery_needed=delivery_needed,
        notes=notes
    )

    session.add(request)
    await session.commit()
    await session.refresh(request)

    logger.info(f"Створено заявку на техніку #{request.id} від користувача {user_id}")
    return request


async def get_user_equipment_requests(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
) -> List[EquipmentRequest]:
    stmt = (
        select(EquipmentRequest)
        .where(EquipmentRequest.user_id == user_id)
        .order_by(EquipmentRequest.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


# ============= ІСТОРІЯ КОНСУЛЬТАЦІЙ =============

async def save_consultation(
        session: AsyncSession,
        user_id: int,
        user_message: str,
        ai_response: str,
        category: Optional[str] = None,
        intent: Optional[str] = None,
        recommended_products: Optional[List[Dict]] = None,
        tokens_used: Optional[int] = None
) -> ConsultationHistory:
    consultation = ConsultationHistory(
        user_id=user_id,
        user_message=user_message,
        ai_response=ai_response,
        category=category,
        intent=intent,
        recommended_products=recommended_products,
        tokens_used=tokens_used
    )

    session.add(consultation)
    await session.commit()
    await session.refresh(consultation)

    logger.debug(f"Збережено консультацію для користувача {user_id}")
    return consultation


async def get_user_consultations(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
) -> List[ConsultationHistory]:
    stmt = (
        select(ConsultationHistory)
        .where(ConsultationHistory.user_id == user_id)
        .order_by(ConsultationHistory.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


# ============= СТАТИСТИКА ПЕРЕГЛЯДІВ =============

async def track_product_view(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        category: Optional[str] = None,
        source: str = "catalog"
) -> None:
    view = ProductView(
        user_id=user_id,
        product_id=product_id,
        category=category,
        source=source
    )

    session.add(view)
    await session.commit()


async def get_popular_products(
        session: AsyncSession,
        category: Optional[str] = None,
        days: int = 30,
        limit: int = 10
) -> List[Dict]:
    date_threshold = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(
            ProductView.product_id,
            func.count(ProductView.id).label('views')
        )
        .where(ProductView.viewed_at >= date_threshold)
    )

    if category:
        stmt = stmt.where(ProductView.category == category)

    stmt = (
        stmt
        .group_by(ProductView.product_id)
        .order_by(func.count(ProductView.id).desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()
    return [{'product_id': row.product_id, 'views': row.views} for row in rows]


async def get_user_preferences(
        session: AsyncSession,
        user_id: int
) -> Dict[str, int]:
    stmt = (
        select(
            ProductView.category,
            func.count(ProductView.id).label('count')
        )
        .where(ProductView.user_id == user_id)
        .where(ProductView.category.isnot(None))
        .group_by(ProductView.category)
    )

    result = await session.execute(stmt)
    return {row.category: row.count for row in result}


# ============= ДОПОМІЖНІ ФУНКЦІЇ =============

async def get_statistics(session: AsyncSession) -> Dict:
    total_users = await session.scalar(select(func.count(User.id)))
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = await session.scalar(
        select(func.count(User.id)).where(User.last_active >= week_ago)
    )
    total_cart_items = await session.scalar(select(func.count(CartItem.id)))
    total_grants = await session.scalar(select(func.count(GrantApplication.id)))
    total_equipment = await session.scalar(select(func.count(EquipmentRequest.id)))

    return {
        'total_users': total_users or 0,
        'active_users': active_users or 0,
        'cart_items': total_cart_items or 0,
        'grant_applications': total_grants or 0,
        'equipment_requests': total_equipment or 0
    }
