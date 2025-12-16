# core/weather/accuweather_client.py
import aiohttp
from loguru import logger
from typing import Optional, Any, Dict, List
from core.config import settings

BASE = "https://dataservice.accuweather.com"


class AccuWeatherClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ACCUWEATHER_API_KEY
        if not self.api_key:
            logger.warning("ACCUWEATHER_API_KEY not set — weather client will not work with real API")

    async def _get(self, path: str, params: Dict[str, Any] = None) -> Any:
        params = params or {}
        params["apikey"] = self.api_key
        url = f"{BASE}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"AccuWeather API error {resp.status} {text}")
                    return None
                return await resp.json()

    async def search_location(self, query: str) -> Optional[Dict]:
        """Search city by name -> returns first matching location dict or None."""
        res = await self._get("/locations/v1/cities/search", {"q": query})
        if not res:
            return None
        # return first result
        return res[0]

    async def get_current_conditions(self, location_key: str) -> Optional[Dict]:
        """Returns currentconditions/v1/{location_key} (first element)"""
        res = await self._get(f"/currentconditions/v1/{location_key}", {"details": "true"})
        if not res:
            return None
        return res[0] if isinstance(res, list) and len(res) > 0 else None

    async def get_daily_forecast(self, location_key: str, days: int = 5) -> Optional[Dict]:
        """Returns daily forecast N days (metric units)"""
        res = await self._get(f"/forecasts/v1/daily/{days}day/{location_key}", {"details": "true", "metric": "true"})
        return res

# singleton
accu_client = AccuWeatherClient()
