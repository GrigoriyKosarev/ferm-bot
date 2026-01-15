# 🌾 FERM Bot - Telegram бот для агротехнологічної платформи

> Telegram бот для інтернет-магазину агротоварів FERM з каталогом продукції, кошиком та AI-консультаціями

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Aiogram 3.13](https://img.shields.io/badge/aiogram-3.13-green.svg)](https://docs.aiogram.dev/)
[![Poetry](https://img.shields.io/badge/poetry-dependency%20management-blue.svg)](https://python-poetry.org/)

---

## 🎯 Про проект

Telegram бот для платформи [FERM](https://ferm.in.ua) - онлайн агромагазину з добривами, засобами захисту рослин та агропрепаратами.

### ✨ Основні функції

- 📦 **Каталог товарів** - перегляд продукції по категоріях
- 🛒 **Кошик покупок** - додавання товарів, зміна кількості
- 🤖 **AI-консультант** - консультації по товарах через OpenAI GPT (опціонально)
- 📱 **Захист доступу** - middleware для перевірки номера телефону
- 🔗 **Інтеграція з сайтом** - оформлення замовлень через сайт FERM
- 💬 **Зручний інтерфейс** - reply та inline клавіатури

---

## 🚀 Швидкий старт

### Вимоги

- Python 3.10+
- Poetry (менеджер залежностей)
- Telegram Bot Token від [@BotFather](https://t.me/BotFather)
- OpenAI API Key (опціонально, для AI-консультацій)

### Встановлення

```bash
# 1. Клонувати репозиторій
git clone <repository-url>
cd ferm-bot

# 2. Встановити Poetry (якщо немає)
curl -sSL https://install.python-poetry.org | python3 -

# 3. Встановити залежності проекту
poetry install
# Це встановить ~71 пакет: aiogram, sqlalchemy, openai та інші
# Займає 1-2 хвилини при першому запуску

# 4. Створити .env файл
cp .env.example .env

# 5. Відредагувати .env та додати BOT_TOKEN
nano .env
```

### Конфігурація

Відредагуйте `.env` файл:

```bash
# Обов'язково
BOT_TOKEN=your_telegram_bot_token_from_botfather

# Опціонально
OPENAI_API_KEY=sk-...          # Для AI-консультацій
OPENAI_MODEL=gpt-4o-mini       # За замовчуванням gpt-4o-mini
DEBUG=False                     # Режим відладки
LOG_LEVEL=INFO                  # Рівень логування
LOG_TO_FILE=True               # Зберігати логи у файл
DATABASE_URL=sqlite+aiosqlite:///ferm_bot.db  # URL бази даних
```

### Встановлення залежностей

**Перед першим запуском** потрібно встановити всі залежності проекту:

```bash
# Встановити залежності (aiogram, sqlalchemy, openai та ін.)
poetry install

# Це створить віртуальне середовище та встановить ~71 пакет
# Займає 1-2 хвилини при першому запуску
```

### Запуск

```bash
# Рекомендований спосіб (Poetry 2.0+):
poetry run python -m bot.main

# Альтернативно - активувати середовище:
eval $(poetry env activate)
python -m bot.main
```

**Примітка:** У Poetry 2.0+ команда `poetry shell` вимагає окремий плагін. Найпростіше використовувати `poetry run`.

---

## 📂 Структура проекту

```
ferm-bot/
├── bot/                           # Основний пакет бота
│   ├── handlers/                  # Обробники подій
│   │   ├── start.py              # Команда /start, запит номера
│   │   ├── menu.py               # Головне меню
│   │   ├── catalog.py            # Каталог товарів
│   │   └── ai_consultation.py    # AI-консультації
│   ├── keyboards/                 # Клавіатури
│   │   ├── reply.py              # Reply клавіатури (меню)
│   │   ├── inline.py             # Inline кнопки (товари)
│   │   └── phone.py              # Запит номера телефону
│   ├── middlewares/               # Middleware
│   │   └── phone_check.py        # Перевірка номера телефону
│   ├── models/                    # Моделі БД (SQLAlchemy)
│   │   ├── user.py               # Модель користувача
│   │   ├── category.py           # Категорії товарів
│   │   ├── product.py            # Товари
│   │   └── cart_item.py          # Позиції кошика
│   ├── repositories/              # Репозиторії (query patterns)
│   │   └── product_repo.py       # Запити до товарів
│   ├── config.py                  # Конфігурація (Pydantic Settings)
│   ├── database.py                # Підключення до БД
│   ├── logger.py                  # Налаштування логування
│   ├── queries.py                 # Допоміжні запити
│   ├── states.py                  # FSM стани
│   └── main.py                    # Точка входу
├── logs/                          # Логи (створюється автоматично)
├── .env                           # Конфігурація (не в Git!)
├── .env.example                   # Приклад конфігурації
├── pyproject.toml                 # Poetry конфігурація
├── poetry.lock                    # Залежності (точні версії)
└── README.md                      # Ця документація
```

---

## 🛠 Технології

### Core

- **[Aiogram 3.13](https://docs.aiogram.dev/)** - async фреймворк для Telegram ботів
- **[SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)** - async ORM для роботи з БД
- **[Pydantic 2.9](https://docs.pydantic.dev/)** - валідація даних та налаштувань
- **[Poetry](https://python-poetry.org/)** - управління залежностями

### Integrations

- **[OpenAI](https://platform.openai.com/)** - AI-консультації по товарах (GPT-4o-mini)
- **[FERM API](https://ferm.in.ua)** - інтеграція з сайтом (оформлення замовлень)

### Database

- **SQLite** (розробка) - `sqlite+aiosqlite://`
- **PostgreSQL** (продакшн) - `postgresql+asyncpg://`

### Infrastructure

- **Docker** - контейнеризація (готово до розгортання)
- **Loguru** - структуроване логування з ротацією

---

## 📖 Використання

### Для користувачів

1. Запустити бота в Telegram
2. Натиснути **"Поділитися номером телефону"** (обов'язково)
3. Використовувати меню:
   - **📦 Каталог** - перегляд товарів по категоріях
   - **🛒 Кошик** - перегляд та редагування кошика
4. На сторінці товару:
   - **➕/➖** - змінити кількість
   - **🛒 Додати до кошика** - додати товар
   - **🔗 Перейти на сайт** - переглянути на сайті
   - **🤖 Консультація з ШІ** - задати питання про товар (якщо увімкнено)
5. В кошику:
   - **📦 Оформити замовлення** - перейти на сайт для оформлення

### Для розробників

#### База даних

```python
# Приклад роботи з БД
from bot.database import get_session
from bot.queries import get_product_by_id

async with get_session() as session:
    product = await get_product_by_id(session, product_id=1)
    print(product.name)
```

#### Додавання нового обробника

1. Створити файл в `bot/handlers/`
2. Створити Router
3. Зареєструвати в `bot/handlers/__init__.py`
4. Підключити в `bot/main.py`

#### Міграції БД

```bash
# Створити нову міграцію
alembic revision --autogenerate -m "Add new field"

# Застосувати міграції
alembic upgrade head
```

---

## 🐳 Docker розгортання

### Локально

```bash
# Збірка образу
docker build -t ferm-bot .

# Запуск контейнера
docker run -d \
  --name ferm-bot \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  ferm-bot
```

### Docker Compose (рекомендовано)

```bash
# Запуск з PostgreSQL
docker-compose up -d

# Переглянути логи
docker-compose logs -f bot

# Зупинити
docker-compose down
```

**Примітка:** Створіть `docker-compose.yml` та `Dockerfile` за потребою. База вже готова до роботи з PostgreSQL.

---

## 🧪 Тестування

```bash
# Запустити тести
poetry run pytest

# З покриттям
poetry run pytest --cov=bot --cov-report=html

# Лінтинг
poetry run black bot/
poetry run isort bot/
poetry run flake8 bot/
poetry run mypy bot/
```

---

## 📝 Розробка

### Pre-commit hooks

```bash
# Встановити pre-commit hooks
poetry run pre-commit install

# Запустити вручну
poetry run pre-commit run --all-files
```

### Coding Style

- **Black** (форматування) - line length 100
- **isort** (сортування імпортів) - profile "black"
- **flake8** (лінтинг)
- **mypy** (type checking)

---

## 🔐 Безпека

- ❌ **НІКОЛИ** не комітьте `.env` файл в Git
- ✅ Використовуйте `.env.example` як шаблон
- ✅ Middleware для перевірки доступу (телефон)
- ✅ Валідація даних через Pydantic
- ✅ Prepared statements (SQLAlchemy) - захист від SQL injection

---

## 📞 Підтримка

- **Питання по коду:** Дивіться коментарі в файлах
- **Документація Aiogram:** https://docs.aiogram.dev/
- **Telegram Bot API:** https://core.telegram.org/bots/api

---

## 🗺 Roadmap

- [ ] Переклад на англійську мову
- [ ] Адмін-панель (керування товарами)
- [ ] Історія замовлень
- [ ] Push-повідомлення про акції
- [ ] Інтеграція з платіжними системами
- [ ] Telegram Mini App для розширеного UI

---

## 📄 Ліцензія

MIT License

---

## 🤝 Contributing

Pull requests are welcome! Для значних змін спочатку відкрийте issue для обговорення.

---

**Зроблено з ❤️ для аграріїв України 🇺🇦**

---

## 📚 Додаткова інформація

### Структура БД

```
User (користувачі)
├── id (PK)
├── telegram_id (unique)
├── username
├── first_name
├── last_name
├── phone_number
└── created_at

Category (категорії товарів)
├── id (PK)
├── name
└── products (relationship)

Product (товари)
├── id (PK)
├── name
├── description
├── price
├── available
├── category_id (FK)
└── product_url

CartItem (позиції кошика)
├── id (PK)
├── user_id (FK)
├── product_id (FK)
├── quantity
└── added_at
```

### AI-консультації

Система використовує OpenAI GPT-4o-mini для надання консультацій по товарах:

- Контекст товару (назва, опис, ціна, категорія)
- Історія діалогу (останні 10 повідомлень)
- Роль агронома-консультанта
- Відповіді українською мовою

Для вимкнення AI-консультацій просто не вказуйте `OPENAI_API_KEY` в `.env`.

---

### FAQ

**Q: Як отримати Telegram Bot Token?**
A: Telegram → [@BotFather](https://t.me/BotFather) → /newbot → слідуйте інструкціям

**Q: Як змінити мову бота?**
A: Всі тексти зараз хардкоднуті українською. Для i18n треба додати систему перекладів (наприклад, через aiogram i18n middleware)

**Q: Чи можна використовувати без AI-консультацій?**
A: Так! Просто не вказуйте `OPENAI_API_KEY` в `.env` - кнопка AI не буде показуватись

**Q: Як перейти з SQLite на PostgreSQL?**
A: Змініть `DATABASE_URL` в `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/ferm_bot
```

**Q: Де дивитись логи?**
A: В директорії `logs/bot.log` (якщо `LOG_TO_FILE=True`) або в консолі

