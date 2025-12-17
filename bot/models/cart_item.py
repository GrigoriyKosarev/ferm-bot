"""
Модель CartItem для кошика покупців

Зберігає товари, які користувач додав у кошик
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base

if TYPE_CHECKING:
    from bot.models.user import User
    from bot.models.product import Product


class CartItem(Base):
    """
    Модель елемента кошика

    Зберігає інформацію про товар у кошику користувача:
    - Користувач (user_id)
    - Товар (product_id)
    - Кількість (quantity)
    - Час додавання (created_at)
    """

    __tablename__ = "cart_items"

    # Первинний ключ
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID запису",
    )

    # Користувач (FK до users.user_id, не до users.id!)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="Telegram ID користувача",
    )

    # Товар
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID товару",
    )

    # Кількість
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Кількість товару",
    )

    # Час додавання
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Час додавання в кошик",
    )

    # ========================================
    # RELATIONSHIPS
    # ========================================

    # Товар (many-to-one)
    product: Mapped["Product"] = relationship(  # type: ignore
        "Product",
        lazy="joined",  # Завантажуємо товар разом з кошиком
    )

    def __repr__(self) -> str:
        """Строкове представлення"""
        return f"<CartItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>"

    def total_price(self) -> float:
        """Загальна ціна за цей товар (ціна * кількість)"""
        if self.product and self.product.price:
            return self.product.price * self.quantity
        return 0.0
