"""
Стани FSM (Finite State Machine) для бота

Використовуються для діалогів, які потребують декілька кроків
"""
from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    """
    Стани для пошуку товарів
    """
    waiting_for_query = State()  # Очікування пошукового запиту від користувача


class OrderStates(StatesGroup):
    """
    Стани для оформлення замовлення
    """
    waiting_for_address = State()  # Очікування адреси доставки
    waiting_for_comment = State()  # Очікування коментаря до замовлення
