"""
КРОК 6: Модель User для користувачів бота

Зберігає інформацію про користувачів Telegram
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from bot.database import Base


class User(Base):
    """
    Модель користувача Telegram

    Зберігає базову інформацію про користувача
    """

    __tablename__ = "users"

    # Первинний ключ (автоінкремент)
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Внутрішній ID",
    )

    # Telegram ID (унікальний)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Telegram ID користувача",
    )

    # Username в Telegram
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Username (@username)",
    )

    # Ім'я
    first_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Ім'я користувача",
    )

    # Прізвище
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Прізвище користувача",
    )

    # Дата створення
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Дата реєстрації",
    )

    # Остання активність
    last_active: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
        comment="Остання активність",
    )

    # Чи заблокований
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Чи заблокований користувач",
    )

    def __repr__(self) -> str:
        """Строкове представлення"""
        return (
            f"<User(id={self.id}, user_id={self.user_id}, "
            f"username={self.username})>"
        )

    def full_name(self) -> str:
        """Повне ім'я користувача"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.user_id}"
