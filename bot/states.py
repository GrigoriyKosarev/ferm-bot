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


class AIConsultationStates(StatesGroup):
    """
    Стани для AI-консультації по товару
    """
    chatting = State()  # Активний діалог з AI про товар
