import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import AppSettings, Category, Product, ProductSize, Store


ASSET_DIR = Path(__file__).resolve().parent / 'mock_images'

PRODUCTS = [
    {
        'name': 'Куртка Ocean Mini',
        'barcode': '30010001',
        'category': Product.CATEGORY_JACKETS,
        'cost_price': 1450,
        'retail_price': 2890,
        'image': 'navy_jacket.png',
        'sizes': [
            ('92 (2 года)', 4),
            ('98 (3 года)', 6),
            ('104 (4 года)', 3),
        ],
    },
    {
        'name': 'Свитшот Sage Kids',
        'barcode': '30020002',
        'category': Product.CATEGORY_KNIT,
        'cost_price': 520,
        'retail_price': 1190,
        'image': 'sage_sweatshirt.png',
        'sizes': [
            ('98 (3 года)', 8),
            ('104 (4 года)', 5),
            ('110 (5 лет)', 7),
        ],
    },
    {
        'name': 'Кеды Velcro Milk',
        'barcode': '30040003',
        'category': Product.CATEGORY_SHOES,
        'cost_price': 980,
        'retail_price': 2190,
        'image': 'velcro_sneakers.png',
        'sizes': [
            ('25', 3),
            ('26', 5),
            ('27', 4),
            ('28', 2),
        ],
    },
]


class Command(BaseCommand):
    help = 'Create three mock products with photos for production smoke testing.'

    def handle(self, *args, **options):
        Store.objects.update_or_create(code='main', defaults={'name': 'ZARA KIDS'})
        AppSettings.current()
        for index, category_name in enumerate(['Куртки', 'Трикотаж', 'Брюки', 'Обувь'], start=1):
            Category.objects.update_or_create(
                name=category_name,
                defaults={'sort_order': index * 10, 'is_active': True},
            )

        media_dir = Path(settings.MEDIA_ROOT) / 'products'
        media_dir.mkdir(parents=True, exist_ok=True)

        for item in PRODUCTS:
            image_name = item['image']
            target_name = f"mock_{image_name}"
            source = ASSET_DIR / image_name
            target = media_dir / target_name
            shutil.copyfile(source, target)

            product, _ = Product.objects.update_or_create(
                barcode=item['barcode'],
                defaults={
                    'name': item['name'],
                    'category': item['category'],
                    'cost_price': item['cost_price'],
                    'retail_price': item['retail_price'],
                    'image': f'products/{target_name}',
                    'is_active': True,
                },
            )
            product.sizes.all().delete()
            for size, stock in item['sizes']:
                ProductSize.objects.create(product=product, size=size, stock=stock)

        self.stdout.write(self.style.SUCCESS('Mock products seeded: 3'))
