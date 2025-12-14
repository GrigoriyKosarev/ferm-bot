# core/weather/scheduler.py
import asyncio
from datetime import datetime, time as dt_time, timedelta
from loguru import logger
from core.database.queries_weather import get_subscribed_users
from core.services.weather.service import weather_service
from aiogram import Bot
from core.config import settings

# Countermeasure: не використовувати blocking sleeps for long times in production.
# Use APScheduler or a task queue (Celery) for robust production scheduling.

async def _send_report(bot: Bot, user_id: int, location_key: str, location_name: str):
    report = await weather_service.get_agro_report(location_key, days=3)
    if not report:
        await bot.send_message(user_id, "Не вдалося отримати погодні дані сьогодні.")
        return
    current = report["current"]
    recs = report["recommendations"]
    forecast = report["forecast"]
    temp = current.get("Temperature", {}).get("Metric", {}).get("Value")
    cond = current.get("WeatherText")
    text = f"🌤 *Щоденна агропогода для {location_name}*\n"
    text += f"Стан: {cond}, {temp}°C\n\n"
    text += "*Агрорекомендації:*\n" + "\n".join(f"- {r}" for r in recs)
    await bot.send_message(user_id, text, parse_mode="Markdown")

async def start_daily_scheduler(bot: Bot, stop_event: asyncio.Event):
    """
    Loop: fetch subscribed users and send report at their notification_time.
    stop_event should be set on shutdown to stop the loop.
    """
    logger.info("Weather scheduler started")
    while not stop_event.is_set():
        users = await get_subscribed_users()
        now = datetime.now()
        for u in users:
            try:
                if not u.get("location_key"):
                    continue
                notif = u.get("notification_time") or "08:00"
                hh, mm = map(int, notif.split(":"))
                target_time = datetime.combine(now.date(), dt_time(hh, mm))
                # If already passed today, send next day
                if target_time.date() < now.date() or (now - target_time) > timedelta(minutes=10):
                    # schedule for next day
                    target_time = target_time + timedelta(days=1)
                delay = (target_time - now).total_seconds()
                # schedule a task to send after delay
                asyncio.create_task(_delayed_send(bot, u["user_id"], u["location_key"], u["saved_location"], delay))
            except Exception as e:
                logger.exception("Error scheduling user %s: %s", u, e)
        # Sleep 60 seconds and re-evaluate (lightweight)
        await asyncio.sleep(60)
    logger.info("Weather scheduler stopped")

async def _delayed_send(bot: Bot, user_id: int, location_key: str, location_name: str, delay: float):
    await asyncio.sleep(delay)
    try:
        await _send_report(bot, user_id, location_key, location_name)
    except Exception:
        logger.exception("Failed to send daily weather")
