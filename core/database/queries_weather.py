from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import UserWeather, User


async def save_user_location(session: AsyncSession, user_id: int, location_key: str, name: str, lat: float, lon: float):
    stmt = (
        update(User)
        .where(User.user_id == user_id)
        .values(saved_location=name, location_key=location_key, latitude=lat, longitude=lon)
    )
    await session.execute(stmt)
    await session.commit()

async def get_user_location(session: AsyncSession, user_id: int):
    """Повертає запис з локацією користувача"""
    stmt = select(UserWeather).where(UserWeather.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def set_user_location(session: AsyncSession, user_id: int, city: str, lat: float, lon: float, key: str):
    """Зберігає або оновлює локацію користувача"""
    existing = await get_user_location(session, user_id)

    if existing:
        existing.saved_location = city
        existing.latitude = lat
        existing.longitude = lon
        existing.location_key = key
    else:
        new_loc = UserWeather(
            user_id=user_id,
            saved_location=city,
            latitude=lat,
            longitude=lon,
            location_key=key,
        )
        session.add(new_loc)

    await session.commit()


async def set_weather_subscription(session: AsyncSession, user_id: int, status: bool):
    """Увімкнути/вимкнути підписку на щоденну погоду"""
    loc = await get_user_location(session, user_id)

    if not loc:
        return False

    loc.subscription_enabled = status
    await session.commit()
    return True


async def get_subscribed_users(session: AsyncSession):
    """Отримує всіх, хто підписаний на агропогоду"""
    stmt = select(UserWeather).where(UserWeather.subscription_enabled == True)
    result = await session.execute(stmt)
    return result.scalars().all()

