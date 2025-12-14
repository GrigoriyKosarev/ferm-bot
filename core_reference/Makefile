.PHONY: help setup install run dev test lint format clean docker-build docker-run

help:
	@echo "🌾 FERM Telegram Bot - Доступні команди:"
	@echo ""
	@echo "  make setup        - Повне налаштування проекту"
	@echo "  make install      - Встановити залежності"
	@echo "  make run          - Запустити бота"
	@echo "  make dev          - Запустити в режимі розробки"
	@echo "  make test         - Запустити тести"
	@echo "  make lint         - Перевірити код"
	@echo "  make format       - Відформатувати код"
	@echo "  make clean        - Очистити тимчасові файли"
	@echo "  make docker-build - Зібрати Docker образ"
	@echo "  make docker-run   - Запустити в Docker"
	@echo ""

setup:
	@echo "⚙️  Налаштування проекту..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Створено .env файл"; \
		echo "⚠️  ВАЖЛИВО: Відредагуйте .env та додайте BOT_TOKEN!"; \
	fi
	@make install
	@echo "✅ Налаштування завершено!"
	@echo ""
	@echo "📋 Наступні кроки:"
	@echo "1. Відкрийте .env: nano .env"
	@echo "2. Додайте BOT_TOKEN від @BotFather"
	@echo "3. Запустіть бота: make run"

install:
	@echo "📦 Встановлення залежностей..."
	poetry install
	@echo "✅ Залежності встановлено!"

run:
	@echo "🚀 Запуск FERM Bot..."
	poetry run python -m core.bot

dev:
	@echo "🔧 Запуск в режимі розробки (DEBUG=True)..."
	DEBUG=True poetry run python -m core.bot

test:
	@echo "🧪 Запуск тестів..."
	poetry run pytest tests/ -v --cov=core

lint:
	@echo "🔍 Перевірка коду..."
	poetry run flake8 core/
	poetry run mypy core/ --ignore-missing-imports
	@echo "✅ Перевірка завершена!"

format:
	@echo "🎨 Форматування коду..."
	poetry run black core/
	poetry run isort core/
	@echo "✅ Код відформатовано!"

clean:
	@echo "🧹 Очищення тимчасових файлів..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f ferm_bot.db
	rm -rf logs/*.log
	@echo "✅ Очищення завершено!"

docker-build:
	@echo "🐳 Збірка Docker образу..."
	docker build -t ferm-telegram-bot:latest .
	@echo "✅ Образ зібрано!"

docker-run:
	@echo "🐳 Запуск Docker контейнера..."
	docker-compose up -d
	@echo "✅ Контейнер запущено!"
	@echo "📊 Логи: docker-compose logs -f bot"

docker-stop:
	@echo "⏹️  Зупинка контейнера..."
	docker-compose down
	@echo "✅ Контейнер зупинено!"

docker-logs:
	@echo "📊 Логи бота..."
	docker-compose logs -f bot

db-init:
	@echo "💾 Ініціалізація бази даних..."
	poetry run python -c "import asyncio; from core.database.database import init_db; asyncio.run(init_db())"
	@echo "✅ База даних ініціалізована!"

db-reset:
	@echo "⚠️  Скидання бази даних..."
	rm -f ferm_bot.db
	@make db-init
	@echo "✅ База даних скинута!"