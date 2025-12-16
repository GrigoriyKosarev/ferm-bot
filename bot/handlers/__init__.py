"""
Обробники подій (handlers)

Експортуємо роутери для підключення до диспетчера
"""

from bot.handlers.start import router as start_router

__all__ = [
    "start_router",
]
