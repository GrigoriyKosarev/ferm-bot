"""
Скрипт для додавання норм застосування до існуючих товарів

Запуск: python add_application_rates.py
"""
import asyncio
from bot.database import get_session, init_db
from bot.models import Product
from sqlalchemy import select


async def add_rates():
    """Додає норми застосування до товарів"""

    # Ініціалізуємо БД
    await init_db()

    async with get_session() as session:
        # Отримуємо всі товари
        result = await session.execute(select(Product))
        products = result.scalars().all()

        print(f"\n📦 Знайдено {len(products)} товарів\n")

        # Норми застосування для мікродобрив (кг/га або л/га)
        rates = {
            # Мікродобрива (зазвичай 2-5 кг/га для гранульованих, 1-3 л/га для рідких)
            "UltraStart": 3.0,           # Мікрогранульоване - 3 кг/га
            "Інтермаг Олійні": 2.0,      # Рідке - 2 л/га
            "Avangard Crystalmax": 1.5,  # Водорозчинне - 1.5 кг/га

            # Основні мінеральні добрива (50-200 кг/га)
            "NPK": 150.0,                # Стартове - 150 кг/га
            "Карбамід": 100.0,           # Азотне - 100 кг/га
            "КАС": 200.0,                # Рідке азотне - 200 л/га

            # ЗЗР - гербіциди (1-3 л/га)
            "МаксПро": 2.5,              # Гербіцид - 2.5 л/га
            "СейфГроу": 1.5,             # Фунгіцид - 1.5 л/га
            "Бласт": 1.0,                # Інсектицид - 1.0 л/га
        }

        updated = 0

        for product in products:
            # Шукаємо підходящу норму за ключовими словами в назві
            for keyword, rate in rates.items():
                if keyword.lower() in product.name.lower():
                    old_rate = product.application_rate
                    product.application_rate = rate

                    if old_rate != rate:
                        updated += 1
                        print(f"✅ {product.name[:50]}...")
                        print(f"   Норма: {rate} {'кг/га' if 'л' not in product.name.lower() else 'л/га'}")
                        print()
                    break

        # Зберігаємо зміни
        await session.commit()

        print(f"\n✅ Оновлено {updated} товарів")
        print(f"📊 Товарів з нормами: {sum(1 for p in products if p.application_rate)}")

        # Показуємо товари без норм
        no_rate = [p for p in products if not p.application_rate]
        if no_rate:
            print(f"\n⚠️  Товари без норм застосування ({len(no_rate)}):")
            for p in no_rate[:5]:
                print(f"   • {p.name[:60]}")
            if len(no_rate) > 5:
                print(f"   ... і ще {len(no_rate) - 5}")


if __name__ == "__main__":
    asyncio.run(add_rates())
