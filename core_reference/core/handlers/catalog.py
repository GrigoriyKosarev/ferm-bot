"""
Обробник каталогу товарів (версія з БД)

Етап 2: Каталог товарів
- Відображення категорій з БД
- Відображення підкатегорій
- Перегляд товарів з пагінацією
- Детальна інформація про товар
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from loguru import logger
from math import ceil

from core.keyboards.inline import (
    get_categories_keyboard_from_db,
    get_subcategories_keyboard_from_db,
    get_products_keyboard_from_db,
    get_product_actions_keyboard
)
from core.database.database import AsyncSessionLocal
from core.database.queries import (
    get_root_categories,
    get_subcategories,
    get_category_by_id,
    get_products_by_category,
    get_products_count_by_category,
    get_product_by_id,
    add_to_cart,
    get_cart_items,
    track_product_view,
    get_category_path
)

router = Router(name="catalog")

PRODUCTS_PER_PAGE = 5  # Товарів на сторінку


# ============= КАТЕГОРІЇ =============

@router.callback_query(F.data == "show_catalog")
async def show_catalog(callback: CallbackQuery):
    """
    Показати головні категорії з БД
    """
    async with AsyncSessionLocal() as session:
        categories = await get_root_categories(session)

        if not categories:
            await callback.message.edit_text(
                "😔 <b>Категорії не знайдені</b>\n\n"
                "База даних порожня. Запустіть seed_data()."
            )
            return

        text = (
            "<b>🛒 Каталог товарів FERM</b>\n\n"
            "Оберіть категорію для перегляду товарів:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_categories_keyboard_from_db(categories)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_subcategories(callback: CallbackQuery):
    """
    Показати підкатегорії
    Callback format: category:{category_id}
    """
    category_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        # Отримати категорію
        category = await get_category_by_id(session, category_id)
        if not category:
            await callback.answer("❌ Категорія не знайдена", show_alert=True)
            return

        # Отримати підкатегорії
        subcategories = await get_subcategories(session, category_id)

        if not subcategories:
            # Якщо немає підкатегорій - показати товари одразу
            await show_products_in_category(callback, category_id, page=1)
            return

        # Є підкатегорії - показати їх
        text = (
            f"<b>{category.name}</b>\n\n"
            f"Оберіть підкатегорію:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_subcategories_keyboard_from_db(
                subcategories,
                parent_id=category_id
            )
        )

    await callback.answer()


# ============= ТОВАРИ =============

async def show_products_in_category(
    callback: CallbackQuery,
    category_id: int,
    page: int = 1
):
    """
    Показати товари з категорії з пагінацією
    """
    async with AsyncSessionLocal() as session:
        # Отримати категорію
        category = await get_category_by_id(session, category_id)
        if not category:
            await callback.answer("❌ Категорія не знайдена", show_alert=True)
            return

        # Підрахунок сторінок
        total_products = await get_products_count_by_category(session, category_id)
        total_pages = ceil(total_products / PRODUCTS_PER_PAGE) if total_products > 0 else 1

        # Отримати товари для поточної сторінки
        offset = (page - 1) * PRODUCTS_PER_PAGE
        products = await get_products_by_category(
            session,
            category_id,
            limit=PRODUCTS_PER_PAGE,
            offset=offset
        )

        if not products:
            text = (
                f"<b>{category.name}</b>\n\n"
                f"😔 Товари в цій категорії поки відсутні."
            )
            await callback.message.edit_text(text)
            await callback.answer()
            return

        # Breadcrumbs (навігація)
        path = await get_category_path(session, category_id)
        breadcrumbs = " → ".join([c.name for c in path])

        # Формування списку товарів
        text = f"<b>📦 {breadcrumbs}</b>\n\n"

        for idx, product in enumerate(products, start=1):
            availability = "✅" if product.available else "❌"
            price_text = f"{product.price} грн" if product.price else "Ціна не вказана"

            text += (
                f"{idx}. <b>{product.name}</b>\n"
                f"   💰 {price_text} | {availability}\n\n"
            )

        text += f"━━━━━━━━━━━━━━━━━\n"
        text += f"<i>Сторінка {page}/{total_pages} • Всього товарів: {total_products}</i>"

        await callback.message.edit_text(
            text,
            reply_markup=get_products_keyboard_from_db(
                products=products,
                category_id=category_id,
                page=page,
                total_pages=total_pages
            )
        )

    await callback.answer()


@router.callback_query(F.data.startswith("products:"))
async def handle_products_callback(callback: CallbackQuery):
    """
    Обробка переходу до товарів категорії
    Callback format: products:{category_id}:{page}
    """
    parts = callback.data.split(":")
    category_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 1

    await show_products_in_category(callback, category_id, page)


@router.callback_query(F.data.startswith("page:"))
async def change_page(callback: CallbackQuery):
    """
    Пагінація товарів
    Callback format: page:{category_id}:{page_num}
    """
    parts = callback.data.split(":")
    category_id = int(parts[1])
    page = int(parts[2])

    await show_products_in_category(callback, category_id, page)


# ============= ДЕТАЛІ ТОВАРУ =============

@router.callback_query(F.data.startswith("product:"))
async def show_product_details(callback: CallbackQuery):
    """
    Детальна інформація про товар
    Callback format: product:{product_id}
    """
    product_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        # Отримати товар
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        # Реєстрація перегляду
        await track_product_view(
            session=session,
            user_id=callback.from_user.id,
            product_id=product_id,
            category=product.category.name if product.category else None,
            source="catalog"
        )

        # Перевірка чи товар в кошику
        cart_items = await get_cart_items(session, callback.from_user.id)
        in_cart = any(item.product_id == product_id for item in cart_items)

        # Breadcrumbs
        path = await get_category_path(session, product.category_id)
        breadcrumbs = " → ".join([c.name for c in path])

        # Формування тексту
        availability = "✅ <b>В наявності</b>" if product.available else "❌ <b>Немає в наявності</b>"
        price_text = f"{product.price} грн" if product.price else "Ціна не вказана"

        text = (
            f"<b>{product.name}</b>\n\n"
            f"📂 <i>{breadcrumbs}</i>\n\n"
            f"💰 <b>Ціна:</b> {price_text}\n"
            f"📦 <b>Наявність:</b> {availability}\n\n"
        )

        if product.description:
            text += f"<b>📝 Опис:</b>\n{product.description}\n\n"

        # Якщо є фото - відправляємо з фото
        if product.image_url:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=product.image_url,
                caption=text,
                reply_markup=get_product_actions_keyboard(
                    product_id=product_id,
                    category_id=product.category_id,
                    in_cart=in_cart
                )
            )
        else:
            # Без фото
            await callback.message.edit_text(
                text,
                reply_markup=get_product_actions_keyboard(
                    product_id=product_id,
                    category_id=product.category_id,
                    in_cart=in_cart
                )
            )

    await callback.answer()


# ============= ДОДАВАННЯ ДО КОШИКА =============

@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_product_to_cart(callback: CallbackQuery):
    """
    Додавання товару до кошика
    Callback format: add_to_cart:{product_id}
    """
    product_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        # Отримати товар
        product = await get_product_by_id(session, product_id)

        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return

        if not product.available:
            await callback.answer("❌ Товар недоступний", show_alert=True)
            return

        # Додати до кошика
        await add_to_cart(
            session=session,
            user_id=callback.from_user.id,
            product_id=product_id,
            product_name=product.name,
            product_price=product.price or 0.0,
            quantity=1.0,
            unit="шт",
            product_image=product.image_url,
            category=product.category.name if product.category else None
        )

        logger.info(f"Товар {product_id} додано до кошика користувача {callback.from_user.id}")

        # Оновити клавіатуру
        await callback.message.edit_reply_markup(
            reply_markup=get_product_actions_keyboard(
                product_id=product_id,
                category_id=product.category_id,
                in_cart=True
            )
        )

        await callback.answer(
            f"✅ {product.name} додано до кошика!",
            show_alert=False
        )


@router.callback_query(F.data.startswith("already_in_cart:"))
async def already_in_cart(callback: CallbackQuery):
    """Товар вже в кошику"""
    await callback.answer(
        "ℹ️ Цей товар вже у вашому кошику",
        show_alert=False
    )


# ============= НАВІГАЦІЯ НАЗАД =============

@router.callback_query(F.data.startswith("back_to_category:"))
async def back_to_category(callback: CallbackQuery):
    """
    Повернутися до категорії
    Callback format: back_to_category:{category_id}
    """
    category_id = int(callback.data.split(":")[1])
    await show_subcategories(
        CallbackQuery(
            id=callback.id,
            from_user=callback.from_user,
            message=callback.message,
            data=f"category:{category_id}",
            chat_instance=callback.chat_instance
        )
    )


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Повернутися до головних категорій"""
    await show_catalog(callback)