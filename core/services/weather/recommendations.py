# core/weather/recommendations.py
from typing import List, Dict, Optional
from loguru import logger

# Simple rule-based agro recommendations.
# If OPENAI is set and you want richer text, you can extend with core/services/ai_service.py

def _emoji_for_condition(text: str) -> str:
    txt = text.lower()
    if "sun" in txt or "clear" in txt:
        return "☀️"
    if "cloud" in txt:
        return "☁️"
    if "rain" in txt or "shower" in txt or "drizzle" in txt:
        return "🌧️"
    if "snow" in txt or "flurr" in txt:
        return "❄️"
    if "wind" in txt or "breez" in txt:
        return "🌬️"
    return "🌤️"


def agro_indicators_from_current(current: Dict) -> List[str]:
    """
    Return short list of agro recommendations based on current conditions dict from AccuWeather.
    current example keys: Temperature, RelativeHumidity, Wind, PrecipitationSummary, RealFeelTemperature
    """
    recs = []

    try:
        temp = current.get("Temperature", {}).get("Metric", {}).get("Value")
        humidity = current.get("RelativeHumidity")
        wind_speed = current.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value", 0)
        precip = 0
        ps = current.get("PrecipitationSummary", {})
        # AccuWeather nested structure; check likely keys
        for k in ("PastHour", "Past3Hours", "PastDay"):
            if k in ps:
                precip = ps[k].get("Metric", {}).get("Value", 0) or precip

        # Rules:
        if temp is not None and temp <= 2:
            recs.append("🚜 Низька температура — краще відкласти обробку ґрунту (ризик заморозків).")
        if humidity is not None and humidity >= 85:
            recs.append("💧 Висока вологість — не рекомендується обприскування.")
        if precip and precip > 0:
            recs.append("🌧 Опади — врахуйте ризики затоплення / відтермінування робіт.")
        if wind_speed and wind_speed >= 10:  # m/s ~ strong; adjust as needed
            recs.append("🌬 Сильний вітер — обприскування не рекомендується.")
        # Favorable for sowing heuristic:
        if temp is not None and 10 <= temp <= 25 and (precip == 0 or precip < 2) and (humidity is None or humidity < 80):
            recs.append("🌱 Сьогодні сприятливий день для сівби.")
        # Fertilizer application heuristic:
        if temp is not None and 8 <= temp <= 30 and (precip == 0 or precip < 1) and (wind_speed is not None and wind_speed < 5):
            recs.append("🌾 Оптимальні умови для внесення добрив.")
    except Exception as e:
        logger.exception("Error in agro_indicators_from_current: %s", e)

    # fallback
    if not recs:
        recs.append("✅ Умови стабільні — конкретних заборон не виявлено.")
    return recs


def build_day_summary(day_forecast: Dict) -> Dict:
    """
    Convert daily forecast element to friendly dict:
    expects 'Temperature': {'Minimum': {'Value':..}, 'Maximum':{'Value':..}}, 'Day', 'Night', 'Day' contains IconPhrase
    """
    temp_min = day_forecast.get("Temperature", {}).get("Minimum", {}).get("Value")
    temp_max = day_forecast.get("Temperature", {}).get("Maximum", {}).get("Value")
    day_phrase = day_forecast.get("Day", {}).get("IconPhrase", "")
    night_phrase = day_forecast.get("Night", {}).get("IconPhrase", "")
    precip_prob = day_forecast.get("Day", {}).get("PrecipitationProbability", 0)
    # determine emoji
    emoji = _emoji_for_condition(day_phrase)
    return {
        "date": day_forecast.get("Date"),
        "temp_min": temp_min,
        "temp_max": temp_max,
        "day_phrase": day_phrase,
        "night_phrase": night_phrase,
        "precip_prob": precip_prob,
        "emoji": emoji
    }
