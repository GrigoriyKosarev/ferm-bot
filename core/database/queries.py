"""
CRUD операції для роботи з базою даних

Функції для створення, читання, оновлення та видалення даних.
Всі функції асинхронні та використовують AsyncSession.
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, delete, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.database.models import (
    User, CartItem, GrantApplication, EquipmentRequest,
    ConsultationHistory, ProductView
)


# ============= КОРИСТУВАЧІ =============

async def create_or_update_user(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
) -> User:
    """
    Створити нового користувача або оновити існуючого

    Args:
        session: Сесія БД
        user_id: Telegram ID користувача
        username: Telegram username
        first_name: Ім'я
        last_name: Прізвище

    Returns:
        User: Об'єкт користувача
    """
    # Спробувати знайти існуючого
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Оновити дані
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.last_active = datetime.utcnow()
        logger.debug(f"Оновлено користувача: {user_id}")
    else:
        # Створити нового
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
    """
    Отримати користувача за ID

    Args:
        session: Сесія БД
        user_id: Telegram ID користувача

    Returns:
        User або None
    """
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
    """
    Оновити локацію користувача для погоди

    Args:
        session: Сесія БД
        user_id: ID користувача
        location: Назва локації (місто)
        latitude: Широта
        longitude: Довгота
        location_key: Ключ локації AccuWeather
    """
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
    """
    Оновити підписки користувача на розсилки

    Args:
        session: Сесія БД
        user_id: ID користувача
        weather: Підписка на погоду
        grants: Підписка на гранти
        promotions: Підписка на акції
    """
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
    """
    Отримати всіх користувачів з певною підпискою

    Args:
        session: Сесія БД
        subscription_type: 'weather', 'grants', або 'promotions'

    Returns:
        List[User]: Список користувачів
    """
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
    return list(result.scalars().all())


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
    """
    Додати товар до кошика або збільшити кількість

    Args:
        session: Сесія БД
        user_id: ID користувача
        product_id: ID товару
        product_name: Назва товару
        product_price: Ціна
        quantity: Кількість
        unit: Одиниця виміру
        product_image: URL зображення
        category: Категорія
        subcategory: Підкатегорія

    Returns:
        CartItem: Товар у кошику
    """
    # Перевірити, чи товар вже в кошику
    stmt = select(CartItem).where(
        and_(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id
        )
    )
    result = await session.execute(stmt)
    cart_item = result.scalar_one_or_none()

    if cart_item:
        # Збільшити кількість
        cart_item.quantity += quantity
        logger.debug(f"Збільшено кількість товару {product_id} до {cart_item.quantity}")
    else:
        # Додати новий товар
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
    """
    Отримати всі товари з кошика користувача

    Args:
        session: Сесія БД
        user_id: ID користувача

    Returns:
        List[CartItem]: Список товарів
    """
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.added_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_cart_item_quantity(
        session: AsyncSession,
        cart_item_id: int,
        quantity: float
) -> None:
    """
    Оновити кількість товару в кошику

    Args:
        session: Сесія БД
        cart_item_id: ID запису в кошику
        quantity: Нова кількість
    """
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
    """
    Видалити товар з кошика

    Args:
        session: Сесія БД
        cart_item_id: ID запису в кошику
        user_id: ID користувача (для безпеки)
    """
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
    """
    Очистити весь кошик користувача

    Args:
        session: Сесія БД
        user_id: ID користувача
    """
    stmt = delete(CartItem).where(CartItem.user_id == user_id)
    result = await session.execute(stmt)
    await session.commit()
    logger.info(f"Очищено кошик користувача {user_id}, видалено {result.rowcount} товарів")


async def get_cart_summary(
        session: AsyncSession,
        user_id: int
) -> Dict:
    """
    Отримати підсумок кошика (кількість товарів та загальна сума)

    Args:
        session: Сесія БД
        user_id: ID користувача

    Returns:
        Dict: {
            'total_items': int,
            'total_price': float,
            'items': List[CartItem]
        }
    """
    items = await get_cart_items(session, user_id)

    total_price = sum(item.product_price * item.quantity for item in items)

    return {
        'total_items': len(items),
        'total_price': round(total_price, 2),
        'items': items
    }


"""
CRUD операції (продовження)
Гранти, Техніка, Консультації, Статистика
"""


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
    """
    Створити заявку на грант

    Args:
        session: Сесія БД
        user_id: ID користувача
        full_name: ПІБ заявника
        phone: Телефон
        email: Email (опціонально)
        farm_size: Розмір господарства (га)
        farm_type: Тип господарства
        region: Регіон
        district: Район
        grant_program: Програма гранту
        requested_amount: Запитувана сума
        purpose: Мета гранту
        description: Опис проекту

    Returns:
        GrantApplication: Створена заявка
    """
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
    """
    Отримати всі заявки користувача на гранти

    Args:
        session: Сесія БД
        user_id: ID користувача
        limit: Максимальна кількість заявок

    Returns:
        List[GrantApplication]: Список заявок
    """
    stmt = (
        select(GrantApplication)
        .where(GrantApplication.user_id == user_id)
        .order_by(GrantApplication.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_grant_application_status(
        session: AsyncSession,
        application_id: int,
        status: str,
        admin_notes: Optional[str] = None
) -> None:
    """
    Оновити статус заявки на грант (для адмінів)

    Args:
        session: Сесія БД
        application_id: ID заявки
        status: Новий статус (pending, processing, approved, rejected)
        admin_notes: Коментарі адміністратора
    """
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
    """
    Створити заявку на оренду техніки

    Args:
        session: Сесія БД
        user_id: ID користувача
        full_name: ПІБ
        phone: Телефон
        equipment_type: Тип техніки
        email: Email
        equipment_id: ID техніки з каталогу
        equipment_model: Модель
        rental_start_date: Дата початку
        rental_duration: Тривалість (днів)
        rental_area: Площа обробки (га)
        location: Локація
        delivery_needed: Чи потрібна доставка
        notes: Додаткові коментарі

    Returns:
        EquipmentRequest: Створена заявка
    """
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
    """
    Отримати всі заявки користувача на техніку

    Args:
        session: Сесія БД
        user_id: ID користувача
        limit: Максимальна кількість

    Returns:
        List[EquipmentRequest]: Список заявок
    """
    stmt = (
        select(EquipmentRequest)
        .where(EquipmentRequest.user_id == user_id)
        .order_by(EquipmentRequest.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


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
    """
    Зберегти консультацію з ШІ

    Args:
        session: Сесія БД
        user_id: ID користувача
        user_message: Питання користувача
        ai_response: Відповідь ШІ
        category: Категорія (seeds, fertilizers, plant_protection)
        intent: Намір (selection, calculation, problem)
        recommended_products: Рекомендовані товари
        tokens_used: Використано токенів API

    Returns:
        ConsultationHistory: Збережена консультація
    """
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
    """
    Отримати історію консультацій користувача

    Args:
        session: Сесія БД
        user_id: ID користувача
        limit: Максимальна кількість

    Returns:
        List[ConsultationHistory]: Список консультацій
    """
    stmt = (
        select(ConsultationHistory)
        .where(ConsultationHistory.user_id == user_id)
        .order_by(ConsultationHistory.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ============= СТАТИСТИКА ПЕРЕГЛЯДІВ =============

async def track_product_view(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        category: Optional[str] = None,
        source: str = "catalog"
) -> None:
    """
    Зареєструвати перегляд товару (для аналітики)

    Args:
        session: Сесія БД
        user_id: ID користувача
        product_id: ID товару
        category: Категорія товару
        source: Джерело перегляду (catalog, search, recommendation)
    """
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
    """
    Отримати найпопулярніші товари за кількістю переглядів

    Args:
        session: Сесія БД
        category: Фільтр по категорії (опціонально)
        days: За скільки днів аналізувати
        limit: Максимальна кількість товарів

    Returns:
        List[Dict]: [{product_id: int, views: int}, ...]
    """
    from datetime import timedelta

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
    return [
        {'product_id': row.product_id, 'views': row.views}
        for row in result
    ]


async def get_user_preferences(
        session: AsyncSession,
        user_id: int
) -> Dict[str, int]:
    """
    Визначити переваги користувача на основі історії переглядів

    Args:
        session: Сесія БД
        user_id: ID користувача

    Returns:
        Dict: {'seeds': 10, 'fertilizers': 5, ...} - кількість переглядів по категоріям
    """
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
    """
    Отримати загальну статистику по боту

    Returns:
        Dict: Статистика користувачів, кошиків, заявок
    """
    # Загальна кількість користувачів
    total_users = await session.scalar(select(func.count(User.id)))

    # Активні користувачі (за останній тиждень)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = await session.scalar(
        select(func.count(User.id)).where(User.last_active >= week_ago)
    )

    # Товарів у кошиках
    total_cart_items = await session.scalar(select(func.count(CartItem.id)))

    # Заявок на гранти
    total_grants = await session.scalar(select(func.count(GrantApplication.id)))

    # Заявок на техніку
    total_equipment = await session.scalar(select(func.count(EquipmentRequest.id)))

    return {
        'total_users': total_users or 0,
        'active_users': active_users or 0,
        'cart_items': total_cart_items or 0,
        'grant_applications': total_grants or 0,
        'equipment_requests': total_equipment or 0
    }