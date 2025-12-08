"""
Конфігурація бота
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Налаштування бота з .env файлу"""

    # Telegram
    BOT_TOKEN: str

    # FERM API
    FERM_API_URL: str = "https://api.ferm.in.ua"
    FERM_API_KEY: Optional[str] = None

    # База даних
    DATABASE_URL: str = "sqlite+aiosqlite:///./ferm_bot.db"

    # Redis (для кешування)
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    # AccuWeather
    ACCUWEATHER_API_KEY: Optional[str] = None

    # OpenAI для ШІ-консультацій
    OPENAI_API_KEY: Optional[str] = None

    # Email для заявок
    ADMIN_EMAIL: str = "admin@ferm.in.ua"

    # Налаштування
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

CATEGORIES = [
        {"id": "seeds", "title": "Насіння"},
        {"id": "fertilizers", "title": "Добрива"},
        {"id": "pesticides", "title": "ЗЗР"},
    ]

settings = Settings()