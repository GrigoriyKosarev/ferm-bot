# core/handlers/weather.py
from aiogram import Router, types
from aiogram.filters import Command
from core.services.weather.service import weather_service
# from core.database.queries_weather import save_user_location, get_user_location, set_weather_subscription, get_subscribed_users
from core.services.weather.recommendations import _emoji_for_condition
from core.config import settings

router = Router()


@router.message(Command("weather"))
async def cmd_weather_start(message: types.Message):
    await message.answer("🌍 Введіть назву населеного пункту (наприклад: Київ або Lviv):")


@router.message()
async def on_text(message: types.Message):
    """General handler — only used when expecting location after /weather.
    If your bot has many handlers, implement FSM to restrict this handler scope.
    """
    query = message.text.strip()
    loc = await weather_service.search_location(query)
    if not loc:
        return await message.answer("❌ Локацію не знайдено. Спробуйте іншу назву.")

    location_key = loc.get("Key")
    name = f"{loc.get('LocalizedName')}, {loc.get('Country', {}).get('LocalizedName', '')}"
    lat = loc.get("GeoPosition", {}).get("Latitude")
    lon = loc.get("GeoPosition", {}).get("Longitude")

    # Save to DB
    # await save_user_location(message.from_user.id, location_key, name, lat, lon)

    # Get report
    report = await weather_service.get_agro_report(location_key, days=5)
    current = report["current"]
    recs = report["recommendations"]
    forecast = report["forecast"]

    # Friendly current weather text
    temp = current.get("Temperature", {}).get("Metric", {}).get("Value")
    humidity = current.get("RelativeHumidity")
    wind = current.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value")
    cond = current.get("WeatherText")
    emoji = _emoji_for_condition(cond or "")

    text = (
        f"🌤 *Погода для:* {name}\n"
        f"{emoji} *{cond}*\n"
        f"🌡 Температура: *{temp}°C*\n"
        f"💧 Вологість: *{humidity}%*\n"
        f"🌬 Вітер: *{wind} м/с*\n\n"
        f"🌾 *Агрорекомендації:*\n" + "\n".join(f"- {r}" for r in recs) + "\n\n"
        f"📅 *Прогноз на {len(forecast)} днів:*\n"
    )

    for day in forecast:
        date = day.get("date")
        tmin = day.get("temp_min")
        tmax = day.get("temp_max")
        phrase = day.get("day_phrase")
        em = day.get("emoji")
        text += f"{em} {date[:10]} — {phrase}. {tmin}…{tmax}°C\n"

    # Quick action buttons
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(text="📌 Підписатися на щоденну агропогоду", callback_data="weather_sub_on"))
    kb.add(types.InlineKeyboardButton(text="🔁 Переглянути інший регіон", callback_data="weather_change"))

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)
