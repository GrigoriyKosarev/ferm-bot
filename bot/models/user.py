"""
КРОК 4: Модель User для бази даних

Що таке модель?
- Python клас що представляє таблицю в БД
- Кожен об'єкт класу = один рядок в таблиці
- Атрибути класу = колонки таблиці

Приклад:
    class User:
        telegram_id: int    # Колонка telegram_id типу INTEGER
        username: str       # Колонка username типу VARCHAR
        created_at: datetime  # Колонка created_at типу TIMESTAMP

    user = User(telegram_id=123, username="john")
    # Це створить рядок в таблиці users
"""

from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from bot.database import Base


# ========================================
# МОДЕЛЬ USER
# ========================================
class User(Base):
    """
    Модель користувача Telegram

    Зберігає інформацію про користувачів бота:
    - ID з Telegram
    - Ім'я користувача
    - Username
    - Дата реєстрації
    - Статус активності

    Таблиця в БД: users
    """

    # Назва таблиці в базі даних
    __tablename__ = "users"

    # ========================================
    # КОЛОНКИ ТАБЛИЦІ
    # ========================================

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,           # Тип: BIGINT (велике число, ID в Telegram великі)
        primary_key=True,     # Первинний ключ (унікальний ідентифікатор)
        autoincrement=False,  # НЕ автоінкремент (використовуємо ID з Telegram)
        comment="Telegram ID користувача",
    )
    """
    ID користувача з Telegram

    Чому BigInteger?
    - ID в Telegram можуть бути дуже великі (більше 2 млрд)
    - Integer (32-bit) не підходить
    - BigInteger (64-bit) підходить

    Чому primary_key=True?
    - Кожен користувач унікальний по telegram_id
    - Немає двох користувачів з однаковим ID

    Чому autoincrement=False?
    - Ми використовуємо ID з Telegram
    - Не генеруємо свої ID
    """

    username: Mapped[str | None] = mapped_column(
        String(64),          # Тип: VARCHAR(64) - текст до 64 символів
        nullable=True,       # Може бути NULL (не всі мають username)
        comment="Username в Telegram (@username)",
    )
    """
    Username користувача (@john_doe)

    Може бути None якщо:
    - Користувач не встановив username
    - Користувач видалив username
    """

    first_name: Mapped[str] = mapped_column(
        String(128),         # Тип: VARCHAR(128)
        nullable=False,      # Обов'язкове поле (в Telegram завжди є)
        comment="Ім'я користувача",
    )
    """
    Ім'я користувача

    nullable=False - ЗАВЖДИ має бути заповнене
    В Telegram обов'язково треба мати ім'я
    """

    last_name: Mapped[str | None] = mapped_column(
        String(128),         # Тип: VARCHAR(128)
        nullable=True,       # Може бути NULL
        comment="Прізвище користувача",
    )
    """
    Прізвище користувача

    Опціональне - не всі вказують прізвище
    """

    is_active: Mapped[bool] = mapped_column(
        Boolean,             # Тип: BOOLEAN (True/False)
        default=True,        # За замовчуванням = True
        nullable=False,
        comment="Чи активний користувач",
    )
    """
    Чи активний користувач

    True - користувач активний (може користуватись ботом)
    False - користувач заблокований/деактивований
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,            # Тип: DATETIME/TIMESTAMP
        default=datetime.utcnow,  # За замовчуванням = поточний час
        nullable=False,
        comment="Дата реєстрації",
    )
    """
    Дата і час коли користувач вперше запустив бота

    datetime.utcnow - UTC час (універсальний, без часових поясів)
    """

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,  # Оновлюється при кожній зміні
        nullable=False,
        comment="Дата останнього оновлення",
    )
    """
    Дата і час останнього оновлення запису

    onupdate=datetime.utcnow - автоматично оновлюється при UPDATE
    """

    # ========================================
    # МЕТОДИ МОДЕЛІ
    # ========================================

    def __repr__(self) -> str:
        """
        Строкове представлення об'єкта

        Використовується для відображення в консолі/логах

        Приклад:
            user = User(telegram_id=123, first_name="John")
            print(user)  # User(telegram_id=123, username=None, first_name='John')
        """
        return (
            f"User("
            f"telegram_id={self.telegram_id}, "
            f"username={self.username}, "
            f"first_name='{self.first_name}'"
            f")"
        )

    def full_name(self) -> str:
        """
        Повне ім'я користувача (ім'я + прізвище)

        Returns:
            str: "Ім'я Прізвище" або просто "Ім'я" якщо прізвища немає

        Приклад:
            user.full_name()  # "John Doe"
        """
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


# ========================================
# ПРИКЛАДИ ВИКОРИСТАННЯ
# ========================================
"""
Створення нового користувача:

    from bot.database import get_session
    from bot.models import User

    async with get_session() as session:
        # Створюємо об'єкт
        user = User(
            telegram_id=123456789,
            username="john_doe",
            first_name="John",
            last_name="Doe",
        )

        # Додаємо в сесію
        session.add(user)

        # Зберігаємо в БД
        await session.commit()

Пошук користувача:

    async with get_session() as session:
        # По telegram_id (первинний ключ)
        user = await session.get(User, 123456789)

        if user:
            print(f"Знайдено: {user.full_name()}")
        else:
            print("Користувача не знайдено")

Оновлення користувача:

    async with get_session() as session:
        user = await session.get(User, 123456789)

        if user:
            user.first_name = "Нове ім'я"
            user.is_active = False
            await session.commit()

Видалення користувача:

    async with get_session() as session:
        user = await session.get(User, 123456789)

        if user:
            await session.delete(user)
            await session.commit()

Запити SELECT:

    from sqlalchemy import select

    async with get_session() as session:
        # Всі активні користувачі
        result = await session.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()

        for user in users:
            print(user.full_name())

Переваги моделей:
✅ Типобезпека (IDE підказує поля)
✅ Автоматичне створення таблиць
✅ Зручна робота з даними (об'єкти замість SQL)
✅ Валідація даних (типи, nullable, тощо)
✅ Міграції (зміни структури БД)
"""
