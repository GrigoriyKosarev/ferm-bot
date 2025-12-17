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


class NormCalculationStates(StatesGroup):
    """
    Стани для розрахунку норм застосування
    """
    waiting_for_area = State()  # Очікування введення площі в гектарах
