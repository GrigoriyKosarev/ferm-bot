"""
SQLAlchemy 2.0 declarative models (async-ready)
All tables and relationships ported from your original models.py
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import (
    Integer, BigInteger, String, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import (
    relationship,
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


# -------------------------
# User
# -------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Telegram data
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Location for weather
    saved_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Subscriptions
    weather_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    grants_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    promotions_subscription: Mapped[bool] = mapped_column(Boolean, default=True)

    # Notification time
    notification_time: Mapped[str] = mapped_column(String(5), default="08:00")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    grant_applications: Mapped[List["GrantApplication"]] = relationship(
        "GrantApplication",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    equipment_requests: Mapped[List["EquipmentRequest"]] = relationship(
        "EquipmentRequest",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    consultations: Mapped[List["ConsultationHistory"]] = relationship(
        "ConsultationHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id} user_id={self.user_id} username={self.username})>"


# -------------------------
# CartItem
# -------------------------
class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # FK uses users.user_id (telegram id) per original design
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_price: Mapped[float] = mapped_column(Float, nullable=False)
    product_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="шт")

    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="cart_items")

    __table_args__ = (
        Index('idx_user_product', 'user_id', 'product_id'),
    )

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id} user_id={self.user_id} product_id={self.product_id})>"


# -------------------------
# GrantApplication
# -------------------------
class GrantApplication(Base):
    __tablename__ = "grant_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    farm_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    farm_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    grant_program: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    requested_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="grant_applications")

    def __repr__(self) -> str:
        return f"<GrantApplication(id={self.id} user_id={self.user_id} status={self.status})>"


# -------------------------
# EquipmentRequest
# -------------------------
class EquipmentRequest(Base):
    __tablename__ = "equipment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    equipment_type: Mapped[str] = mapped_column(String(255), nullable=False)
    equipment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    equipment_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    rental_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rental_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rental_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_needed: Mapped[bool] = mapped_column(Boolean, default=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="equipment_requests")

    def __repr__(self) -> str:
        return f"<EquipmentRequest(id={self.id} equipment_type={self.equipment_type})>"


# -------------------------
# ConsultationHistory
# -------------------------
class ConsultationHistory(Base):
    __tablename__ = "consultation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    recommended_products: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="consultations")

    __table_args__ = (
        Index('idx_user_consultations', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ConsultationHistory(id={self.id} user_id={self.user_id})>"


# -------------------------
# ProductView
# -------------------------
class ProductView(Base):
    __tablename__ = "product_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_product_popularity', 'product_id', 'viewed_at'),
        Index('idx_user_preferences', 'user_id', 'category'),
    )

    def __repr__(self) -> str:
        return f"<ProductView(user_id={self.user_id} product_id={self.product_id})>"


# -------------------------
# Category
# -------------------------
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    # Parent relationship (one parent)
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="children",
        remote_side=[id],  # правильне місце
    )

    # Children relationship (many children)
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,  # обов’язково для delete-orphan
    )

    # Products in category
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


# -------------------------
# Product
# -------------------------
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    category: Mapped["Category"] = relationship("Category", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product(id={self.id} name={self.name} price={self.price})>"

class UserWeather(Base):
    __tablename__ = "user_weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    humidity: Mapped[float] = mapped_column(Float, nullable=True)
    condition: Mapped[str] = mapped_column(String(100), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Опціонально: зв'язок з таблицею користувачів
    user = relationship("User", back_populates="weather_records")

    def __repr__(self) -> str:
        return (
            f"<UserWeather(user_id={self.user_id}, "
            f"temperature={self.temperature}, "
            f"condition={self.condition}, "
            f"recorded_at={self.recorded_at})>"
        )
