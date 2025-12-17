"""
Middlewares для бота

Middleware - це проміжні обробники, які виконуються перед основними handlers
"""
from .phone_check import PhoneCheckMiddleware

__all__ = ["PhoneCheckMiddleware"]
