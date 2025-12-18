"""
Обробники подій (handlers)

Експортуємо роутери для підключення до диспетчера
"""

from bot.handlers.start import router as start_router
from bot.handlers.menu import router as menu_router
from bot.handlers.catalog import router as catalog_router
from bot.handlers.ai_consultation import router as ai_consultation_router

__all__ = [
    "start_router",
    "menu_router",
    "catalog_router",
    "ai_consultation_router",
]
