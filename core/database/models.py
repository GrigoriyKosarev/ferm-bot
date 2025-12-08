"""
Моделі бази даних для FERM Bot

Таблиці:
- users: користувачі бота
- cart_items: товари в кошику
- grant_applications: заявки на гранти
- equipment_requests: заявки на оренду техніки
- consultation_history: історія ШІ-консультацій
- user_preferences: налаштування користувача
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """
    Модель користувача бота

    Зберігає інформацію про користувача Telegram,
    його локацію для погоди, підписки тощо
    """
    __tablename__ = "users"

    # Первинний ключ
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Telegram дані (user_id - унікальний)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Контактна інформація
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # Локація для погоди (зберігається після першого запиту)
    saved_location = Column(String(255), nullable=True)  # Назва міста
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_key = Column(String(50), nullable=True)  # AccuWeather location key

    # Підписки на розсилки
    weather_subscription = Column(Boolean, default=False)  # АгроПогода щоденно
    grants_subscription = Column(Boolean, default=False)  # Новини про гранти
    promotions_subscription = Column(Boolean, default=True)  # Акції (за замовчуванням)

    # Налаштування сповіщень
    notification_time = Column(String(5), default="08:00")  # Час розсилки (HH:MM)

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)  # Чи заблокував бота

    # Зв'язки з іншими таблицями
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    grant_applications = relationship("GrantApplication", back_populates="user")
    equipment_requests = relationship("EquipmentRequest", back_populates="user")
    consultations = relationship("ConsultationHistory", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"


class CartItem(Base):
    """
    Товар у кошику користувача

    Зберігає товари, які користувач додав до кошика.
    Дані синхронізуються перед переходом на сайт.
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    # Інформація про товар (з FERM API)
    product_id = Column(Integer, nullable=False, index=True)  # ID товару на сайті
    product_name = Column(String(500), nullable=False)
    product_price = Column(Float, nullable=False)
    product_image = Column(String(500), nullable=True)  # URL зображення

    # Кількість та одиниці
    quantity = Column(Float, default=1.0, nullable=False)  # Може бути дробове (кг, л)
    unit = Column(String(50), default="шт")  # шт, кг, л, т

    # Категорія (для аналітики та рекомендацій)
    category = Column(String(50), nullable=True)  # seeds, fertilizers, plant_protection
    subcategory = Column(String(50), nullable=True)

    # Метадані
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Зв'язок з користувачем
    user = relationship("User", back_populates="cart_items")

    # Індекс для швидкого пошуку товарів користувача
    __table_args__ = (
        Index('idx_user_product', 'user_id', 'product_id'),
    )

    def __repr__(self):
        return f"<CartItem(user_id={self.user_id}, product={self.product_name})>"


class GrantApplication(Base):
    """
    Заявка на грант (АгроГранти)

    Зберігає заявки користувачів на отримання грантів
    для фінансування сільськогосподарської діяльності
    """
    __tablename__ = "grant_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Контактні дані заявника
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)

    # Інформація про господарство
    farm_size = Column(Float, nullable=True)  # Розмір у гектарах
    farm_type = Column(String(255), nullable=True)  # Тип: рослинництво, тваринництво
    region = Column(String(255), nullable=True)  # Область/регіон
    district = Column(String(255), nullable=True)  # Район

    # Деталі заявки
    grant_program = Column(String(500), nullable=True)  # Назва програми гранту
    requested_amount = Column(Float, nullable=True)  # Запитувана сума
    purpose = Column(Text, nullable=True)  # Мета отримання гранту
    description = Column(Text, nullable=True)  # Опис проекту

    # Статус обробки
    status = Column(String(50), default="pending")  # pending, processing, approved, rejected
    admin_notes = Column(Text, nullable=True)  # Коментарі адміністратора

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Зв'язок
    user = relationship("User", back_populates="grant_applications")

    def __repr__(self):
        return f"<GrantApplication(id={self.id}, user_id={self.user_id}, status={self.status})>"


class EquipmentRequest(Base):
    """
    Заявка на оренду техніки (АгроУклон)

    Зберігає запити на оренду сільськогосподарської техніки
    """
    __tablename__ = "equipment_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Контактні дані
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)

    # Деталі техніки
    equipment_type = Column(String(255), nullable=False)  # Трактор, комбайн тощо
    equipment_id = Column(Integer, nullable=True)  # ID з каталогу machinery.ferm.in.ua
    equipment_model = Column(String(255), nullable=True)  # Модель техніки

    # Параметри оренди
    rental_start_date = Column(DateTime, nullable=True)  # Бажана дата початку
    rental_duration = Column(Integer, nullable=True)  # Тривалість у днях
    rental_area = Column(Float, nullable=True)  # Площа для обробки (га)

    # Локація
    location = Column(String(255), nullable=True)  # Місце використання
    delivery_needed = Column(Boolean, default=False)  # Чи потрібна доставка

    # Додаткова інформація
    notes = Column(Text, nullable=True)  # Коментарі, побажання

    # Статус
    status = Column(String(50), default="pending")  # pending, confirmed, completed, cancelled

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Зв'язок
    user = relationship("User", back_populates="equipment_requests")

    def __repr__(self):
        return f"<EquipmentRequest(id={self.id}, equipment={self.equipment_type})>"


class ConsultationHistory(Base):
    """
    Історія ШІ-консультацій

    Зберігає діалоги користувача з ШІ-консультантом
    для покращення рекомендацій та аналітики
    """
    __tablename__ = "consultation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    # Діалог
    user_message = Column(Text, nullable=False)  # Питання користувача
    ai_response = Column(Text, nullable=False)  # Відповідь ШІ

    # Контекст консультації
    category = Column(String(100), nullable=True)  # seeds, fertilizers, plant_protection
    intent = Column(String(100), nullable=True)  # selection, calculation, problem

    # Рекомендовані товари (якщо є)
    recommended_products = Column(JSON, nullable=True)  # [{"id": 1, "name": "..."}, ...]

    # Метадані
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tokens_used = Column(Integer, nullable=True)  # Для моніторингу витрат API

    # Зв'язок
    user = relationship("User", back_populates="consultations")

    # Індекс для швидкого пошуку історії користувача
    __table_args__ = (
        Index('idx_user_consultations', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ConsultationHistory(id={self.id}, user_id={self.user_id})>"


class ProductView(Base):
    """
    Статистика переглядів товарів

    Для аналітики популярності товарів та персоналізації
    """
    __tablename__ = "product_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)

    # Контекст перегляду
    category = Column(String(50), nullable=True)
    source = Column(String(50), nullable=True)  # catalog, search, recommendation

    # Метадані
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Індекси для аналітики
    __table_args__ = (
        Index('idx_product_popularity', 'product_id', 'viewed_at'),
        Index('idx_user_preferences', 'user_id', 'category'),
    )

    def __repr__(self):
        return f"<ProductView(user_id={self.user_id}, product_id={self.product_id})>"