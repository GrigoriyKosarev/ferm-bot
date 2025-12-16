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
    REDIS_TTL: int = 3600

    # AccuWeather
    ACCUWEATHER_API_KEY: Optional[str] = None

    # OpenAI для ШІ-консультацій
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 1000

    # Email для заявок
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ADMIN_EMAIL: str = "admin@ferm.in.ua"

    # Налаштування
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    MAX_CART_ITEMS: int = 50
    PRODUCTS_PER_PAGE: int = 5

    # Webhook (для продакшену)
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8080

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Дозволити додаткові поля (щоб не було помилки)
        extra = "ignore"


# Категорії товарів
CATEGORIES = {
    "seeds": {
        "name": "🌾 Насіння",
        "subcategories": {
            "legumes": "Бобові",
            "cereals": "Зернові",
            "oilseeds": "Олійні",
            "vegetables": "Овочеві"
        }
    },
    "fertilizers": {
        "name": "🧪 Добрива",
        "subcategories": {
            "micro": "Мікродобрива",
            "organic": "Органічні",
            "mineral": "Мінеральні",
            "complex": "Комплексні"
        }
    },
    "plant_protection": {
        "name": "🛡 ЗЗР",
        "subcategories": {
            "insecticides": "Інсектициди",
            "herbicides": "Гербіциди",
            "fungicides": "Фунгіциди",
            "growth_regulators": "Регулятори росту"
        }
    }
}

settings = Settings()