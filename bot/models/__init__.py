"""
Моделі бази даних

Цей файл експортує всі моделі для зручного імпорту:

    from bot.models import User

замість:

    from bot.models.user import User
"""

from bot.models.user import User

__all__ = [
    "User",
]
