"""
Обробники для роботи з каталогом товарів
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database import get_session
from bot.queries import get_subcategories, get_category_by_id, get_products_by_category
from bot.keyboards.inline import get_categories_keyboard_from_db, get_products_keyboard

router = Router(name="catalog")


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """
    Повернення до головного меню каталогу (показ кореневих категорій)
    """
    from bot.queries import get_root_categories

    async with get_session() as session:
        categories = await get_root_categories(session)

        text = "📦 <b>Каталог товарів</b>\n\n"
        text += "Оберіть категорію для перегляду товарів:"

        keyboard = get_categories_keyboard_from_db(categories)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def callback_category(callback: CallbackQuery):
    """
    Обробник натискання на категорію.
    Показує підкатегорії якщо вони є, або товари якщо підкатегорій немає.
    """
    # Отримуємо ID категорії з callback_data (формат: "category:123")
    category_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        # Отримуємо інформацію про категорію
        category = await get_category_by_id(session, category_id)

        if not category:
            await callback.answer("❌ Категорію не знайдено", show_alert=True)
            return

        # Перевіряємо чи є підкатегорії
        subcategories = await get_subcategories(session, category_id)

        if subcategories:
            # Є підкатегорії - показуємо їх
            text = f"📁 <b>{category.name}</b>\n\nОберіть підкатегорію:"
            # Передаємо parent_id для кнопки "Назад"
            keyboard = get_categories_keyboard_from_db(subcategories, parent_id=category.parent_id)

            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Немає підкатегорій - показуємо товари
            products = await get_products_by_category(session, category_id, limit=10)

            if products:
                text = f"📦 <b>{category.name}</b>\n\n"
                text += f"Знайдено товарів: {len(products)}\n\n"
                text += "Оберіть товар для перегляду деталей:"

                # Клавіатура з товарами та кнопкою "Назад"
                keyboard = get_products_keyboard(products, category_parent_id=category.parent_id)

                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                text = f"📦 <b>{category.name}</b>\n\n"
                text += "У цій категорії поки немає товарів."

                # Клавіатура тільки з кнопкою "Назад"
                keyboard = get_products_keyboard([], category_parent_id=category.parent_id)

                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )

    await callback.answer()
