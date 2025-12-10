# core/weather/service.py
from typing import Optional, Dict, Any, List
from core.services.weather.accuweather_client import accu_client
from core.services.weather.recommendations import agro_indicators_from_current, build_day_summary
from loguru import logger

class WeatherService:
    def __init__(self, client=accu_client):
        self.client = client

    async def search_location(self, query: str) -> Optional[Dict]:
        return await self.client.search_location(query)

    async def get_current(self, location_key: str) -> Optional[Dict]:
        return await self.client.get_current_conditions(location_key)

    async def get_forecast(self, location_key: str, days: int = 5) -> Optional[Dict]:
        return await self.client.get_daily_forecast(location_key, days)

    async def get_agro_report(self, location_key: str, days: int = 5) -> Optional[Dict]:
        """
        Returns combined report:
        {
            "current": {...},
            "recommendations": [...],
            "forecast": [day_summary,...]
        }
        """
        current = await self.get_current(location_key)
        forecast_raw = await self.get_forecast(location_key, days=days)
        forecast = []
        if forecast_raw and "DailyForecasts" in forecast_raw:
            forecast = [build_day_summary(d) for d in forecast_raw["DailyForecasts"]]

        recommendations = agro_indicators_from_current(current) if current else ["Немає даних для рекомендацій"]
        return {
            "current": current,
            "recommendations": recommendations,
            "forecast": forecast
        }

weather_service = WeatherService()
