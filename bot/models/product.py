"""
КРОК 6: Модель Product для товарів

Товари прив'язані до категорій
Приклад: Мікродобриво "UltraStart" → категорія "Мікродобрива"
"""

from typing import Optional

from sqlalchemy import Integer, String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base


class Product(Base):
    """
    Модель товару

    Зберігає інформацію про товар в каталозі:
    - Назва, опис, ціна
    - Зображення
    - Доступність
    - Категорія
    """

    __tablename__ = "products"

    # Первинний ключ
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID товару",
    )

    # Назва товару
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="Назва товару",
    )

    # Опис товару
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Детальний опис товару",
    )

    # Ціна
    price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Ціна в гривнях",
    )

    # Доступність
    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Чи є товар в наявності",
    )

    # URL зображення
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL зображення товару",
    )

    # ========================================
    # FOREIGN KEYS
    # ========================================

    # Категорія товару (обов'язково)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID категорії",
    )

    # ========================================
    # RELATIONSHIPS
    # ========================================

    # Категорія (many-to-one)
    category: Mapped["Category"] = relationship(  # type: ignore
        "Category",
        back_populates="products",
    )

    def __repr__(self) -> str:
        """Строкове представлення"""
        price_str = f", price={self.price}" if self.price else ""
        return f"<Product(id={self.id}, name='{self.name}'{price_str})>"

    def price_formatted(self) -> str:
        """Форматована ціна для відображення"""
        if self.price:
            return f"{self.price:.2f} грн"
        return "Ціна не вказана"
