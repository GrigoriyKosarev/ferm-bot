"""
Клієнт для роботи з API сайту FERM

Функції:
- Отримання категорій та підкатегорій
- Отримання списку товарів
- Отримання деталей товару
- Отримання акцій
- Пошук товарів
- Рекомендації супутніх товарів
"""
import httpx
from typing import List, Optional, Dict, Any
from loguru import logger

from core.config import settings


class FermAPIError(Exception):
    """Помилка при роботі з API FERM"""
    pass


class FermAPI:
    """
    Клас для взаємодії з API сайту FERM

    Підтримує кешування для зменшення навантаження на API
    """

    def __init__(self):
        """Ініціалізація клієнта"""
        self.base_url = settings.FERM_API_URL.rstrip('/')
        self.api_key = settings.FERM_API_KEY

        # Налаштування headers
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "FERM-Telegram-Bot/1.0"
        }

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # HTTP клієнт з timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True
        )

        logger.info(f"FERM API клієнт ініціалізовано: {self.base_url}")

    async def _request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """
        Базовий метод для HTTP запитів

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Endpoint API (без base_url)
            params: Query параметри
            data: Body для POST/PUT

        Returns:
            Dict: Відповідь від API

        Raises:
            FermAPIError: При помилці запиту
        """
        url = f"{endpoint}"

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data
            )

            # Перевірка статусу
            response.raise_for_status()

            # Парсинг JSON
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP помилка {e.response.status_code}: {url}")
            raise FermAPIError(f"API помилка: {e.response.status_code}")

        except httpx.RequestError as e:
            logger.error(f"Помилка запиту: {e}")
            raise FermAPIError(f"Помилка з'єднання з API: {str(e)}")

        except Exception as e:
            logger.error(f"Несподівана помилка API: {e}")
            raise FermAPIError(f"Помилка API: {str(e)}")

    # ============= КАТЕГОРІЇ =============

    async def get_categories(self) -> List[Dict]:
        """
        Отримати список всіх категорій

        Returns:
            List[Dict]: Список категорій

        Example response:
            [
                {"id": 1, "name": "Насіння", "slug": "seeds"},
                {"id": 2, "name": "Добрива", "slug": "fertilizers"},
                ...
            ]
        """
        try:
            response = await self._request("GET", "/api/v1/categories")
            return response.get('categories', [])
        except FermAPIError:
            # Повертаємо заглушку якщо API недоступний
            logger.warning("API недоступний, використовується заглушка категорій")
            return self._get_mock_categories()

    async def get_subcategories(self, category_slug: str) -> List[Dict]:
        """
        Отримати підкатегорії категорії

        Args:
            category_slug: Slug категорії (seeds, fertilizers, plant_protection)

        Returns:
            List[Dict]: Список підкатегорій
        """
        try:
            response = await self._request(
                "GET",
                f"/api/v1/categories/{category_slug}/subcategories"
            )
            return response.get('subcategories', [])
        except FermAPIError:
            return self._get_mock_subcategories(category_slug)

    # ============= ТОВАРИ =============

    async def get_products(
            self,
            category: Optional[str] = None,
            subcategory: Optional[str] = None,
            page: int = 1,
            per_page: int = 10,
            search: Optional[str] = None,
            in_stock_only: bool = False
    ) -> Dict:
        """
        Отримати список товарів з фільтрами

        Args:
            category: Фільтр по категорії
            subcategory: Фільтр по підкатегорії
            page: Номер сторінки
            per_page: Товарів на сторінку
            search: Пошуковий запит
            in_stock_only: Тільки товари в наявності

        Returns:
            Dict: {
                'products': List[Dict],
                'total': int,
                'page': int,
                'pages': int
            }
        """
        params = {
            'page': page,
            'per_page': per_page
        }

        if category:
            params['category'] = category
        if subcategory:
            params['subcategory'] = subcategory
        if search:
            params['search'] = search
        if in_stock_only:
            params['in_stock'] = 'true'

        try:
            response = await self._request("GET", "/api/v1/products", params=params)
            return response
        except FermAPIError:
            return self._get_mock_products(category, subcategory, page, per_page)

    async def get_product(self, product_id: int) -> Dict:
        """
        Отримати детальну інформацію про товар

        Args:
            product_id: ID товару

        Returns:
            Dict: Детальна інформація про товар

        Example response:
            {
                'id': 101,
                'name': 'Насіння пшениці',
                'price': 1250.00,
                'unit': 'кг',
                'description': '...',
                'in_stock': True,
                'images': ['url1', 'url2'],
                'category': 'seeds',
                'subcategory': 'cereals',
                'attributes': {...},
                'application_rate': 2.5,  # Норма застосування
                'package_size': 25  # Розмір упаковки
            }
        """
        try:
            response = await self._request("GET", f"/api/v1/products/{product_id}")
            return response.get('product', {})
        except FermAPIError:
            return self._get_mock_product(product_id)

    async def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Пошук товарів за запитом

        Args:
            query: Пошуковий запит
            limit: Максимальна кількість результатів

        Returns:
            List[Dict]: Знайдені товари
        """
        try:
            params = {'q': query, 'limit': limit}
            response = await self._request("GET", "/api/v1/search", params=params)
            return response.get('results', [])
        except FermAPIError:
            return []

    # ============= АКЦІЇ =============

    async def get_promotions(
            self,
            category: Optional[str] = None,
            limit: int = 10
    ) -> List[Dict]:
        """
        Отримати список акцій

        Args:
            category: Фільтр по категорії
            limit: Максимальна кількість акцій

        Returns:
            List[Dict]: Список акцій
        """
        params = {'limit': limit}
        if category:
            params['category'] = category

        try:
            response = await self._request("GET", "/api/v1/promotions", params=params)
            return response.get('promotions', [])
        except FermAPIError:
            return self._get_mock_promotions()

    # ============= РЕКОМЕНДАЦІЇ =============

    async def get_related_products(self, product_id: int) -> List[Dict]:
        """
        Отримати супутні товари (рекомендації)

        Args:
            product_id: ID товару

        Returns:
            List[Dict]: Список супутніх товарів
        """
        try:
            response = await self._request(
                "GET",
                f"/api/v1/products/{product_id}/related"
            )
            return response.get('related', [])
        except FermAPIError:
            return self._get_mock_related_products(product_id)

    # ============= ЗАГЛУШКИ (MOCK DATA) =============
    # Використовуються коли API недоступний

    def _get_mock_categories(self) -> List[Dict]:
        """Заглушка для категорій"""
        return [
            {"id": 1, "name": "Насіння", "slug": "seeds"},
            {"id": 2, "name": "Добрива", "slug": "fertilizers"},
            {"id": 3, "name": "ЗЗР", "slug": "plant_protection"},
        ]

    def _get_mock_subcategories(self, category: str) -> List[Dict]:
        """Заглушка для підкатегорій"""
        mock_data = {
            "seeds": [
                {"id": 11, "name": "Бобові", "slug": "legumes"},
                {"id": 12, "name": "Зернові", "slug": "cereals"},
                {"id": 13, "name": "Олійні", "slug": "oilseeds"},
            ],
            "fertilizers": [
                {"id": 21, "name": "Мікродобрива", "slug": "micro"},
                {"id": 22, "name": "Органічні", "slug": "organic"},
            ],
            "plant_protection": [
                {"id": 31, "name": "Інсектициди", "slug": "insecticides"},
                {"id": 32, "name": "Гербіциди", "slug": "herbicides"},
            ]
        }
        return mock_data.get(category, [])

    def _get_mock_products(
            self,
            category: Optional[str],
            subcategory: Optional[str],
            page: int,
            per_page: int
    ) -> Dict:
        """Заглушка для списку товарів"""
        mock_products = [
            {
                "id": 101,
                "name": "Насіння пшениці озимої 'Мудрість'",
                "price": 1250.00,
                "unit": "кг",
                "in_stock": True,
                "short_description": "Високоврожайний сорт",
                "category": "seeds",
                "subcategory": "cereals"
            },
            {
                "id": 102,
                "name": "Добриво NPK 16-16-16",
                "price": 18500.00,
                "unit": "т",
                "in_stock": True,
                "short_description": "Комплексне мінеральне добриво",
                "category": "fertilizers",
                "subcategory": "mineral"
            },
            {
                "id": 103,
                "name": "Гербіцид 'Раундап'",
                "price": 850.00,
                "unit": "л",
                "in_stock": True,
                "short_description": "Суцільної дії",
                "category": "plant_protection",
                "subcategory": "herbicides"
            }
        ]

        # Фільтрація по категорії
        if category:
            mock_products = [p for p in mock_products if p.get('category') == category]
        if subcategory:
            mock_products = [p for p in mock_products if p.get('subcategory') == subcategory]

        return {
            'products': mock_products,
            'total': len(mock_products),
            'page': page,
            'pages': 1
        }

    def _get_mock_product(self, product_id: int) -> Dict:
        """Заглушка для деталей товару"""
        return {
            "id": product_id,
            "name": "Насіння пшениці озимої 'Мудрість'",
            "price": 1250.00,
            "unit": "кг",
            "description": "Високоврожайний сорт озимої пшениці з відмінними хлібопекарськими якостями",
            "in_stock": True,
            "stock_quantity": 500,
            "images": ["https://placehold.co/400x400/png?text=Wheat"],
            "category": "seeds",
            "subcategory": "cereals",
            "attributes": {
                "Урожайність": "8-9 т/га",
                "Стійкість до хвороб": "висока",
                "Норма висіву": "4-5 млн/га"
            },
            "application_rate": 4.5,  # млн/га
            "package_size": 25  # кг
        }

    def _get_mock_promotions(self) -> List[Dict]:
        """Заглушка для акцій"""
        return [
            {
                "id": 1,
                "title": "Знижка на насіння озимої пшениці",
                "description": "Спеціальна пропозиція на весь асортимент",
                "discount": 15,
                "products": [101, 103, 105],
                "valid_until": "2025-01-31"
            }
        ]

    def _get_mock_related_products(self, product_id: int) -> List[Dict]:
        """Заглушка для супутніх товарів"""
        return [
            {
                "id": 201,
                "name": "Стимулятор росту 'Агростимул'",
                "price": 350.00,
                "short_description": "Покращує схожість"
            },
            {
                "id": 202,
                "name": "Протруйник 'Максим'",
                "price": 890.00,
                "short_description": "Захист від хвороб"
            }
        ]

    async def close(self):
        """Закрити HTTP клієнт"""
        await self.client.aclose()
        logger.info("FERM API клієнт закрито")