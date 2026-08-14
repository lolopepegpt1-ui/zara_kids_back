from datetime import UTC, datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import AppSettings, Category, Product, ProductSize, Store, Transaction, TransactionItem


PRODUCTS = [
    {
        'name': 'Куртка стеганая с капюшоном',
        'barcode': '20010045',
        'category': 'Куртки',
        'cost_price': 1800,
        'retail_price': 3200,
        'sizes': [
            ('92 (2 года)', 8),
            ('98 (3 года)', 6),
            ('104 (4 года)', 3),
            ('110 (5 лет)', 5),
            ('116 (6 лет)', 0),
        ],
    },
    {
        'name': 'Свитшот хлопковый Zara Basic',
        'barcode': '20020056',
        'category': 'Трикотаж',
        'cost_price': 600,
        'retail_price': 1200,
        'sizes': [
            ('98 (3 года)', 18),
            ('104 (4 года)', 4),
            ('110 (5 лет)', 1),
            ('116 (6 лет)', 27),
        ],
    },
    {
        'name': 'Джинсы зауженные Denim Cole',
        'barcode': '20030078',
        'category': 'Брюки',
        'cost_price': 900,
        'retail_price': 1900,
        'sizes': [
            ('104 (4 года)', 9),
            ('110 (5 лет)', 1),
            ('116 (6 лет)', 10),
            ('122 (7 лет)', 18),
        ],
    },
    {
        'name': 'Кеды кожаные на липучках',
        'barcode': '20040012',
        'category': 'Обувь',
        'cost_price': 1100,
        'retail_price': 2400,
        'sizes': [
            ('25 (2-3 года)', 5),
            ('26 (3-4 года)', 3),
            ('27 (4-5 лет)', 4),
            ('28 (5-6 лет)', 4),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed demo ZARA KIDS data'

    def handle(self, *args, **options):
        Transaction.objects.update(related_transaction=None)
        TransactionItem.objects.all().delete()
        Transaction.objects.all().delete()
        Product.objects.all().delete()

        Store.objects.all().delete()
        Store.objects.update_or_create(code='main', defaults={'name': 'ZARA KIDS'})
        AppSettings.current()
        for index, category_name in enumerate(['Куртки', 'Трикотаж', 'Брюки', 'Обувь'], start=1):
            Category.objects.update_or_create(
                name=category_name,
                defaults={'sort_order': index * 10, 'is_active': True},
            )

        product_map = {}
        for item in PRODUCTS:
            sizes = item.pop('sizes')
            product = Product.objects.create(**item)
            product_map[product.barcode] = product
            for size, stock in sizes:
                ProductSize.objects.create(
                    product=product,
                    size=size,
                    stock=stock,
                )

        self._sale(
            number='tx-101',
            date='2026-06-25T11:20:00+00:00',
            cashier='Кассир',
            payment='cash',
            lines=[('20010045', '92 (2 года)', 1), ('20020056', '98 (3 года)', 2)],
        )
        self._sale(
            number='tx-102',
            date='2026-06-26T14:45:00+00:00',
            cashier='Кассир',
            payment='card',
            lines=[('20030078', '116 (6 лет)', 1)],
        )
        self._sale(
            number='tx-103',
            date='2026-06-27T17:10:00+00:00',
            cashier='Кассир',
            payment='qr',
            lines=[('20010045', '104 (4 года)', 2)],
        )
        self._sale(
            number='tx-104',
            date='2026-06-28T12:00:00+00:00',
            cashier='Кассир',
            payment='card',
            lines=[('20040012', '26 (3-4 года)', 1), ('20020056', '104 (4 года)', 1)],
        )

        self.stdout.write(self.style.SUCCESS('Demo data seeded'))

    def _sale(self, number, date, cashier, payment, lines):
        store = Store.objects.get(code='main')
        total_amount = 0
        total_cost = 0
        parsed_date = datetime.fromisoformat(date)

        tx = Transaction.objects.create(
            number=number,
            store=store,
            type=Transaction.TYPE_SALE,
            cashier_name=cashier,
            total_amount=0,
            total_cost=0,
            payment_method=payment,
        )

        for barcode, size_name, qty in lines:
            product = Product.objects.get(barcode=barcode)
            total_amount += product.retail_price * qty
            total_cost += product.cost_price * qty
            TransactionItem.objects.create(
                transaction=tx,
                product=product,
                product_name=product.name,
                size=size_name,
                price=product.retail_price,
                cost=product.cost_price,
                quantity=qty,
            )

        tx.total_amount = total_amount
        tx.total_cost = total_cost
        tx.created_at = timezone.make_aware(parsed_date.replace(tzinfo=None), UTC)
        tx.save(update_fields=['total_amount', 'total_cost', 'created_at'])
