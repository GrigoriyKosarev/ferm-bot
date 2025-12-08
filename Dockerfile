# Базовий образ з Python 3.11
FROM python:3.11-slim as base

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Встановлення Poetry
RUN curl -sSL https://install.python.poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Налаштування Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Робоча директорія
WORKDIR /app

# Копіювання файлів залежностей
COPY pyproject.toml poetry.lock ./

# Встановлення залежностей
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --no-root --no-dev --no-interaction --no-ansi

# Копіювання коду проекту
COPY . .

# Створення директорій
RUN mkdir -p /app/logs /app/data

# Змінні середовища
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Порт (якщо використовується webhook)
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Запуск бота
CMD ["python", "-m", "core.bot"]