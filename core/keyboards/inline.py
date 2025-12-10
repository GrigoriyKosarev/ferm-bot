"""
Inline клавіатури (кнопки в повідомленнях)

Використовуються для:
- Навігації по каталогу
- Дій з товарами
- Вибору опцій
- Пагінації
"""
from typing import List, Optional, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============= КАТАЛОГ З БД =============

def get_categories_keyboard_from_db(categories: List) -> InlineKeyboardMarkup:
    """
    Клавіатура з головними категоріями з БД

    Args:
        categories: List[Category] з бази даних

    Returns:
        InlineKeyboardMarkup: Кнопки категорій
    """
    builder = InlineKeyboardBuilder()

    for category in categories:
        # Емодзі для категорій
        emoji_map = {
            "Добрива": "🧪",
            "Засоби захисту рослин (ЗЗР)": "🛡",
            "Насіння": "🌾"
        }
        emoji = emoji_map.get(category.name, "📦")

        builder.button(
            text=f"{emoji} {category.name}",
            callback_data=f"category:{category.id}"
        )

    builder.adjust(1)  # По 1 кнопці в ряд
    return builder.as_markup()

def get_subcategories_keyboard_from_db(
        subcategories: List,
        parent_id: int
) -> InlineKeyboardMarkup:
    """
    Клавіатура з підкатегоріями

    Args:
        subcategories: List[Category] підкатегорії
        parent_id: ID батьківської категорії

    Returns:
        InlineKeyboardMarkup: Кнопки підкатегорій
    """
    builder = InlineKeyboardBuilder()

    for subcat in subcategories:
        builder.button(
            text=subcat.name,
            callback_data=f"products:{subcat.id}:1"
        )

    # Кнопка назад
    builder.button(
        text="◀️ Назад до категорій",
        callback_data="back_to_catalog"
    )

    builder.adjust(2)  # По 2 кнопки в ряд
    return builder.as_markup()

def get_products_keyboard_from_db(
        products: List,
        category_id: int,
        page: int = 1,
        total_pages: int = 1
) -> InlineKeyboardMarkup:
    """
    Клавіатура зі списком товарів

    Args:
        products: List[Product] товари
        category_id: ID категорії
        page: Поточна сторінка
        total_pages: Загальна кількість сторінок

    Returns:
        InlineKeyboardMarkup: Кнопки товарів + пагінація
    """
    builder = InlineKeyboardBuilder()

    # Кнопки товарів
    for product in products:
        # Показуємо ціну якщо є
        price_text = f" | {product.price} грн" if product.price else ""
        button_text = f"{product.name[:35]}...{price_text}" if len(product.name) > 35 else f"{product.name}{price_text}"

        builder.button(
            text=button_text,
            callback_data=f"product:{product.id}"
        )

    # Пагінація
    if total_pages > 1:
        pagination_buttons = []

        # Попередня сторінка
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Попередня",
                    callback_data=f"page:{category_id}:{page - 1}"
                )
            )

        # Поточна сторінка
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {page}/{total_pages}",
                callback_data="current_page"
            )
        )

        # Наступна сторінка
        if page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="Наступна ➡️",
                    callback_data=f"page:{category_id}:{page + 1}"
                )
            )

        builder.row(*pagination_buttons)

    # Кнопка назад до категорій
    builder.button(
        text="◀️ Назад",
        callback_data=f"category:{category_id}"
    )

    builder.adjust(1)  # По 1 товару в ряд
    return builder.as_markup()

def get_product_actions_keyboard(
        product_id: int,
        category_id: int,
        in_cart: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавіатура дій з товаром

    Args:
        product_id: ID товару
        category_id: ID категорії товару
        in_cart: Чи товар вже в кошику

    Returns:
        InlineKeyboardMarkup: Кнопки дій
    """
    builder = InlineKeyboardBuilder()

    # Кнопка додавання до кошика
    if not in_cart:
        builder.button(
            text="🛒 Додати до кошика",
            callback_data=f"add_to_cart:{product_id}"
        )
    else:
        builder.button(
            text="✅ Товар у кошику",
            callback_data=f"already_in_cart:{product_id}"
        )

    # Кнопка переходу на сайт
    builder.button(
        text="🌐 Перейти на сайт",
        url=f"https://ferm.in.ua/product/{product_id}"
    )

    # Кнопка назад до списку товарів
    builder.button(
        text="◀️ Назад до товарів",
        callback_data=f"products:{category_id}:1"
    )

    builder.adjust(1)  # По 1 кнопці в ряд
    return builder.as_markup()


# ============= КОШИК =============

def get_cart_actions_keyboard() -> InlineKeyboardMarkup:
    """
    Клавіатура дій з кошиком

    Returns:
        InlineKeyboardMarkup: Дії з кошиком
    """
    builder = InlineKeyboardBuilder()

    # Завершити покупку на сайті
    builder.button(
        text="🌐 Завершити покупку на сайті",
        url="https://ferm.in.ua/cart"
    )

    # Редагувати кошик
    builder.button(
        text="✏️ Редагувати кошик",
        callback_data="cart:edit"
    )

    # Очистити кошик
    builder.button(
        text="🗑 Очистити кошик",
        callback_data="cart:clear"
    )

    # Продовжити покупки
    builder.button(
        text="◀️ Продовжити покупки",
        callback_data="back:categories"
    )

    builder.adjust(1)

    return builder.as_markup()


def get_cart_item_actions(cart_item_id: int) -> InlineKeyboardMarkup:
    """
    Клавіатура дій з товаром у кошику

    Args:
        cart_item_id: ID запису в кошику

    Returns:
        InlineKeyboardMarkup: Дії з товаром
    """
    builder = InlineKeyboardBuilder()

    # Змінити кількість
    builder.button(
        text="➖ Зменшити",
        callback_data=f"cart:decrease:{cart_item_id}"
    )

    builder.button(
        text="➕ Збільшити",
        callback_data=f"cart:increase:{cart_item_id}"
    )

    # Видалити товар
    builder.button(
        text="🗑 Видалити",
        callback_data=f"cart:remove:{cart_item_id}"
    )

    builder.adjust(2, 1)

    return builder.as_markup()


# ============= АКЦІЇ =============

def get_promotions_keyboard(promotions: List[Dict]) -> InlineKeyboardMarkup:
    """
    Клавіатура зі списком акцій

    Args:
        promotions: Список акцій

    Returns:
        InlineKeyboardMarkup: Список акцій
    """
    builder = InlineKeyboardBuilder()

    for promo in promotions:
        builder.button(
            text=f"🔥 {promo['title']}",
            callback_data=f"promo:{promo['id']}"
        )

    # Назад до категорій
    builder.button(
        text="◀️ Назад до категорій",
        callback_data="back:categories"
    )

    builder.adjust(1)

    return builder.as_markup()


def get_promotion_actions(promo_id: int, product_ids: List[int]) -> InlineKeyboardMarkup:
    """
    Клавіатура дій з акцією

    Args:
        promo_id: ID акції
        product_ids: Список ID товарів в акції

    Returns:
        InlineKeyboardMarkup: Дії з акцією
    """
    builder = InlineKeyboardBuilder()

    # Переглянути товари акції
    builder.button(
        text="🛒 Переглянути товари",
        callback_data=f"promo:products:{promo_id}"
    )

    # Перейти на сайт
    builder.button(
        text="🌐 Детальніше на сайті",
        url=f"https://ferm.in.ua/promotions/{promo_id}"
    )

    # Назад до акцій
    builder.button(
        text="◀️ Назад до акцій",
        callback_data="promotions"
    )

    builder.adjust(1)

    return builder.as_markup()


"""
Inline клавіатури (продовження)
Гранти, Техніка, Погода, Консультації
"""


# ============= АГРОГРАНТИ =============

def get_grants_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Головне меню АгроГрантів

    Returns:
        InlineKeyboardMarkup: Опції грантів
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Подати заявку на грант",
        callback_data="grant:apply"
    )

    builder.button(
        text="📊 Актуальні програми",
        callback_data="grant:programs"
    )

    builder.button(
        text="💼 Консультація",
        callback_data="grant:consultation"
    )

    builder.button(
        text="🔔 Підписатися на новини",
        callback_data="grant:subscribe"
    )

    builder.button(
        text="📜 Мої заявки",
        callback_data="grant:my_applications"
    )

    builder.adjust(1)

    return builder.as_markup()


def get_grant_programs_keyboard(programs: List[Dict]) -> InlineKeyboardMarkup:
    """
    Клавіатура з грантовими програмами

    Args:
        programs: Список програм

    Returns:
        InlineKeyboardMarkup: Список програм
    """
    builder = InlineKeyboardBuilder()

    for program in programs:
        builder.button(
            text=f"💰 {program['name']}",
            callback_data=f"grant:program:{program['id']}"
        )

    builder.button(
        text="◀️ Назад до меню грантів",
        callback_data="grant:menu"
    )

    builder.adjust(1)

    return builder.as_markup()


def get_grant_application_confirm() -> InlineKeyboardMarkup:
    """
    Підтвердження відправки заявки на грант

    Returns:
        InlineKeyboardMarkup: Підтвердження
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Підтвердити та відправити",
        callback_data="grant:confirm"
    )

    builder.button(
        text="✏️ Редагувати",
        callback_data="grant:edit"
    )

    builder.button(
        text="❌ Скасувати",
        callback_data="grant:cancel"
    )

    builder.adjust(1)

    return builder.as_markup()


# ============= АГРОУКЛОН (ОРЕНДА ТЕХНІКИ) =============

def get_equipment_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Головне меню АгроУклон

    Returns:
        InlineKeyboardMarkup: Опції оренди техніки
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🚜 Каталог техніки",
        callback_data="equipment:catalog"
    )

    builder.button(
        text="📋 Подати заявку",
        callback_data="equipment:request"
    )

    builder.button(
        text="💰 Розрахувати вартість",
        callback_data="equipment:calculate"
    )

    builder.button(
        text="📜 Мої заявки",
        callback_data="equipment:my_requests"
    )

    builder.adjust(2, 1, 1)

    return builder.as_markup()


def get_equipment_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Категорії техніки

    Returns:
        InlineKeyboardMarkup: Категорії
    """
    builder = InlineKeyboardBuilder()

    categories = [
        ("🚜 Трактори", "equipment:cat:tractors"),
        ("🌾 Комбайни", "equipment:cat:combines"),
        ("💧 Обприскувачі", "equipment:cat:sprayers"),
        ("🌱 Сівалки", "equipment:cat:seeders"),
        ("🔧 Інше обладнання", "equipment:cat:other"),
    ]

    for text, callback in categories:
        builder.button(text=text, callback_data=callback)

    builder.button(
        text="◀️ Назад до меню",
        callback_data="equipment:menu"
    )

    builder.adjust(2)

    return builder.as_markup()


def get_equipment_item_actions(equipment_id: int) -> InlineKeyboardMarkup:
    """
    Дії з одиницею техніки

    Args:
        equipment_id: ID техніки

    Returns:
        InlineKeyboardMarkup: Дії
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Оформити заявку",
        callback_data=f"equipment:book:{equipment_id}"
    )

    builder.button(
        text="📊 Характеристики",
        callback_data=f"equipment:specs:{equipment_id}"
    )

    builder.button(
        text="💰 Ціна оренди",
        callback_data=f"equipment:price:{equipment_id}"
    )

    builder.button(
        text="🌐 Детальніше на сайті",
        url=f"https://machinery.ferm.in.ua/equipment/{equipment_id}"
    )

    builder.button(
        text="◀️ Назад до каталогу",
        callback_data="equipment:catalog"
    )

    builder.adjust(1, 2, 1, 1)

    return builder.as_markup()


# ============= АГРОПОГОДА =============

def get_weather_actions_keyboard(has_location: bool = False) -> InlineKeyboardMarkup:
    """
    Дії з погодою

    Args:
        has_location: Чи збережена локація користувача

    Returns:
        InlineKeyboardMarkup: Дії з погодою
    """
    builder = InlineKeyboardBuilder()

    if has_location:
        builder.button(
            text="🔄 Оновити погоду",
            callback_data="weather:refresh"
        )

        builder.button(
            text="📅 Прогноз на 5 днів",
            callback_data="weather:forecast"
        )

        builder.button(
            text="🌾 Агрорекомендації",
            callback_data="weather:recommendations"
        )

        builder.button(
            text="📍 Змінити локацію",
            callback_data="weather:change_location"
        )

        builder.button(
            text="🔔 Підписка на розсилки",
            callback_data="weather:subscription"
        )
    else:
        builder.button(
            text="📍 Встановити локацію",
            callback_data="weather:set_location"
        )

    builder.adjust(2)

    return builder.as_markup()


def get_weather_subscription_keyboard(is_subscribed: bool) -> InlineKeyboardMarkup:
    """
    Управління підпискою на погоду

    Args:
        is_subscribed: Чи підписаний користувач

    Returns:
        InlineKeyboardMarkup: Управління підпискою
    """
    builder = InlineKeyboardBuilder()

    if is_subscribed:
        builder.button(
            text="🔕 Відписатися",
            callback_data="weather:unsubscribe"
        )
    else:
        builder.button(
            text="🔔 Підписатися",
            callback_data="weather:subscribe"
        )

    builder.button(
        text="⏰ Налаштувати час розсилки",
        callback_data="weather:set_time"
    )

    builder.button(
        text="◀️ Назад до погоди",
        callback_data="weather:menu"
    )

    builder.adjust(1)

    return builder.as_markup()


# ============= КОНСУЛЬТАЦІЇ ШІ =============

def get_consultation_quick_questions() -> InlineKeyboardMarkup:
    """
    Швидкі питання для консультацій

    Returns:
        InlineKeyboardMarkup: Швидкі питання
    """
    builder = InlineKeyboardBuilder()

    questions = [
        ("🌾 Підбір насіння", "consult:quick:seeds"),
        ("🧪 Вибір добрив", "consult:quick:fertilizers"),
        ("🛡 ЗЗР для культури", "consult:quick:protection"),
        ("📊 Розрахунок норм", "consult:quick:calculate"),
        ("🌱 Технологія вирощування", "consult:quick:technology"),
        ("🐛 Боротьба з шкідниками", "consult:quick:pests"),
    ]

    for text, callback in questions:
        builder.button(text=text, callback_data=callback)

    builder.button(
        text="💬 Задати своє питання",
        callback_data="consult:custom"
    )

    builder.adjust(2)

    return builder.as_markup()


def get_consultation_actions(
        has_products: bool = False,
        consultation_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """
    Дії після отримання консультації

    Args:
        has_products: Чи є рекомендовані товари
        consultation_id: ID консультації

    Returns:
        InlineKeyboardMarkup: Дії
    """
    builder = InlineKeyboardBuilder()

    if has_products:
        builder.button(
            text="🛒 Переглянути рекомендовані товари",
            callback_data=f"consult:products:{consultation_id}"
        )

    builder.button(
        text="🔄 Уточнити питання",
        callback_data=f"consult:clarify:{consultation_id}"
    )

    builder.button(
        text="📝 Нове питання",
        callback_data="consult:new"
    )

    builder.button(
        text="📚 Історія консультацій",
        callback_data="consult:history"
    )

    builder.adjust(1)

    return builder.as_markup()


# ============= ЗАГАЛЬНІ КЛАВІАТУРИ =============

def get_pagination_keyboard(
        callback_prefix: str,
        page: int,
        total_pages: int,
        back_callback: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Універсальна пагінація

    Args:
        callback_prefix: Префікс для callback (напр. "products")
        page: Поточна сторінка
        total_pages: Загальна кількість сторінок
        back_callback: Callback для кнопки "Назад"

    Returns:
        InlineKeyboardMarkup: Пагінація
    """
    builder = InlineKeyboardBuilder()

    buttons = []

    # Попередня сторінка
    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"{callback_prefix}:page:{page - 1}"
            )
        )

    # Поточна сторінка
    buttons.append(
        InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data="current_page"
        )
    )

    # Наступна сторінка
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"{callback_prefix}:page:{page + 1}"
            )
        )

    builder.row(*buttons)

    # Кнопка назад (якщо вказана)
    if back_callback:
        builder.button(
            text="◀️ Назад",
            callback_data=back_callback
        )

    return builder.as_markup()


def get_yes_no_keyboard(
        yes_callback: str,
        no_callback: str,
        yes_text: str = "✅ Так",
        no_text: str = "❌ Ні"
) -> InlineKeyboardMarkup:
    """
    Універсальна клавіатура Так/Ні

    Args:
        yes_callback: Callback для "Так"
        no_callback: Callback для "Ні"
        yes_text: Текст кнопки "Так"
        no_text: Текст кнопки "Ні"

    Returns:
        InlineKeyboardMarkup: Так/Ні
    """
    builder = InlineKeyboardBuilder()

    builder.button(text=yes_text, callback_data=yes_callback)
    builder.button(text=no_text, callback_data=no_callback)

    builder.adjust(2)

    return builder.as_markup()