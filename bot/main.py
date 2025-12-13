import asyncio

import logger

# ============= ТОЧКА ВХОДУ =============

if __name__ == '__main__':
    """
    Запуск бота

    Команда: python -m bot.main
    або: poetry run python -m bot.main
    або: make run
    """
    try:
        # Запуск через asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("⚠️ Отримано KeyboardInterrupt, зупинка...")
    except Exception as e:
        logger.critical(f"💥 Критична помилка при запуску: {e}")
        sys.exit(1)