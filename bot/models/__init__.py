"""
КРОК 6: Моделі бази даних

Експортуємо всі моделі для зручного імпорту:
    from bot.models import User, Category, Product

Моделі:
- User - користувачі Telegram
- Category - категорії товарів (ієрархія)
- Product - товари в каталозі
"""

from bot.models.user import User
from bot.models.category import Category
from bot.models.product import Product

__all__ = [
    "User",
    "Category",
    "Product",
]
