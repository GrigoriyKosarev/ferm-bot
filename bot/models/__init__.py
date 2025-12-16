"""
Моделі бази даних

КРОК 6: Використовуємо моделі з core/database/models.py
Це дозволяє мати всі моделі (User, Category, Product, CartItem тощо) в одному місці

Цей файл експортує моделі для зручного імпорту:

    from bot.models import User, Category, Product

замість:

    from core.database.models import User, Category, Product
"""

# КРОК 6: Імпортуємо всі моделі з core/
from core.database.models import (
    User,
    Category,
    Product,
    CartItem,
    GrantApplication,
    EquipmentRequest,
    ConsultationHistory,
    ProductView,
)

__all__ = [
    "User",
    "Category",
    "Product",
    "CartItem",
    "GrantApplication",
    "EquipmentRequest",
    "ConsultationHistory",
    "ProductView",
]
