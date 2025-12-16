"""
КРОК 6: Модель Category для каталогу товарів

Ієрархічна структура категорій (дерево):
- Корінь: Добрива, ЗЗР, Насіння
- Підкатегорії: Мікродобрива, Інсектициди, Бобові тощо
"""

from typing import List, Optional

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base


class Category(Base):
    """
    Модель категорії товарів

    Підтримує ієрархічну структуру (parent-children)
    Приклад: Добрива → Мікродобрива → [товари]
    """

    __tablename__ = "categories"

    # Первинний ключ
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="ID категорії",
    )

    # Назва категорії
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Назва категорії (унікальна)",
    )

    # Батьківська категорія (для підкатегорій)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        comment="ID батьківської категорії (NULL для кореневих)",
    )

    # ========================================
    # RELATIONSHIPS (зв'язки)
    # ========================================

    # Батьківська категорія (one-to-one)
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="children",
        remote_side=[id],  # Вказує що це батьківська сторона
    )

    # Дочірні категорії (one-to-many)
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    # Товари в категорії (one-to-many)
    # Імпорт Product буде в runtime щоб уникнути циклічних імпортів
    products: Mapped[List["Product"]] = relationship(  # type: ignore
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Строкове представлення"""
        parent_info = f", parent_id={self.parent_id}" if self.parent_id else ""
        return f"<Category(id={self.id}, name='{self.name}'{parent_info})>"
