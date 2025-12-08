"""
Пакет handlers - обробники подій Telegram бота

Містить роутери для різних розділів бота:
- start: Команди /start, /help, головне меню
- catalog: Каталог товарів, категорії, підкатегорії
- cart: Кошик користувача
- weather: АгроПогода з рекомендаціями
- grants: АгроГранти - заявки на гранти
- consultation: ШІ-консультант
"""

# Імпорт роутерів для зручності
from .start import router as start_router
from .catalog import router as catalog_router
from .cart import router as cart_router
# from .weather import router as weather_router
# from .grants import router as grants_router
# from .consultation import router as consultation_router

__all__ = [
    "start_router",
    "catalog_router",
    "cart_router",
    # "weather_router",
    # "grants_router",
    # "consultation_router",
]