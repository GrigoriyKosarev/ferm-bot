"""
Middleware для перевірки наявності номера телефону

Блокує доступ до всіх функцій бота якщо користувач не поділився номером телефону
"""
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.database import get_session
from bot.models import User
from bot.logger import logger
from bot.keyboards.phone import get_phone_keyboard


class PhoneCheckMiddleware(BaseMiddleware):
    """
    Middleware для перевірки наявності номера телефону користувача

    Пропускає тільки:
    - Команду /start
    - Обробник контактів (для збереження номера)

    Блокує всі інші запити якщо користувач не поділився номером телефону
    """

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """
        Виконується перед кожним handler

        Args:
            handler: Наступний handler в ланцюжку
            event: Повідомлення або callback
            data: Додаткові дані

        Returns:
            Результат виконання handler або None якщо доступ заблоковано
        """
        # Визначаємо тип події та user_id
        if isinstance(event, Message):
            user_id = event.from_user.id
            message = event
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            message = event.message
        else:
            # Невідомий тип події - пропускаємо
            return await handler(event, data)

        # ========================================
        # ДОЗВОЛЯЄМО БЕЗ ПЕРЕВІРКИ:
        # ========================================

        # 1. Команда /start - потрібна для реєстрації
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # 2. Контакт - потрібен для збереження номера
        if isinstance(event, Message) and event.contact:
            return await handler(event, data)

        # ========================================
        # ПЕРЕВІРЯЄМО НАЯВНІСТЬ НОМЕРА ТЕЛЕФОНУ
        # ========================================

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(User.phone_number).where(User.user_id == user_id)
                )
                phone_number = result.scalar_one_or_none()

            # Якщо номер телефону є - пропускаємо далі
            if phone_number:
                return await handler(event, data)

            # ========================================
            # БЛОКУЄМО ДОСТУП - НЕМАЄ НОМЕРА ТЕЛЕФОНУ
            # ========================================

            logger.warning(
                f"Користувач {user_id} спробував отримати доступ без номера телефону. "
                f"Тип події: {type(event).__name__}"
            )

            # Повідомлення про необхідність поділитися номером
            await message.answer(
                "⛔️ <b>Доступ обмежено</b>\n\n"
                "Для використання бота необхідно поділитися номером телефону.\n\n"
                "Натисніть /start щоб почати реєстрацію.",
                parse_mode="HTML",
                reply_markup=get_phone_keyboard()
            )

            # Якщо це callback - відповідаємо на нього
            if isinstance(event, CallbackQuery):
                await event.answer("⛔️ Спочатку поділіться номером телефону", show_alert=True)

            # Блокуємо виконання handler
            return None

        except Exception as e:
            logger.error(f"Помилка в PhoneCheckMiddleware для користувача {user_id}: {e}")
            # У разі помилки БД - пропускаємо далі (щоб не блокувати бота)
            return await handler(event, data)
