from django.db import models


class Store(models.Model):
    code = models.CharField('Код', max_length=16, unique=True)
    name = models.CharField('Название', max_length=80)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазин'
        ordering = ['code']

    def __str__(self):
        return self.name


class AppSettings(models.Model):
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'

    def __str__(self):
        return 'Настройки ZARA KIDS'

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Category(models.Model):
    name = models.CharField('Название', max_length=32, unique=True)
    is_active = models.BooleanField('Активна', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=100)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_JACKETS = 'Куртки'
    CATEGORY_KNIT = 'Трикотаж'
    CATEGORY_PANTS = 'Брюки'
    CATEGORY_SHOES = 'Обувь'

    CATEGORY_CHOICES = [
        (CATEGORY_JACKETS, CATEGORY_JACKETS),
        (CATEGORY_KNIT, CATEGORY_KNIT),
        (CATEGORY_PANTS, CATEGORY_PANTS),
        (CATEGORY_SHOES, CATEGORY_SHOES),
    ]

    name = models.CharField('Название', max_length=180)
    barcode = models.CharField('Штрих-код', max_length=64, unique=True)
    category = models.CharField('Категория', max_length=32)
    cost_price = models.PositiveIntegerField('Закупочная цена', default=0)
    retail_price = models.PositiveIntegerField('Цена продажи', default=0)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField('Размер', max_length=80)
    stock = models.IntegerField('Остаток', default=0)

    class Meta:
        verbose_name = 'Размер и остаток'
        verbose_name_plural = 'Размеры и остатки'
        unique_together = [('product', 'size')]
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} / {self.size}'

    def has_stock(self, quantity):
        return self.stock >= quantity

    def add_stock(self, quantity):
        self.stock += quantity


class Transaction(models.Model):
    TYPE_SALE = 'sale'
    TYPE_REFUND = 'refund'
    TYPE_CHOICES = [
        (TYPE_SALE, 'Продажа'),
        (TYPE_REFUND, 'Возврат'),
    ]

    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_QR = 'qr'
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Наличные'),
        (PAYMENT_CARD, 'Банковская карта'),
        (PAYMENT_QR, 'QR-код'),
    ]

    number = models.CharField('Номер', max_length=32, unique=True)
    store = models.ForeignKey(Store, verbose_name='Магазин', on_delete=models.PROTECT)
    type = models.CharField('Тип', max_length=16, choices=TYPE_CHOICES)
    cashier_name = models.CharField('Кассир', max_length=120)
    total_amount = models.PositiveIntegerField('Сумма', default=0)
    total_cost = models.PositiveIntegerField('Себестоимость', default=0)
    payment_method = models.CharField('Способ оплаты', max_length=16, choices=PAYMENT_CHOICES)
    related_transaction = models.OneToOneField(
        'self',
        blank=True,
        null=True,
        related_name='refund',
        on_delete=models.PROTECT,
    )
    authorized_by = models.CharField('Авторизовал', max_length=120, blank=True)
    created_at = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.number


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, verbose_name='Операция', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Товар', blank=True, null=True, on_delete=models.SET_NULL)
    product_name = models.CharField('Название товара', max_length=180)
    size = models.CharField('Размер', max_length=80)
    price = models.PositiveIntegerField('Цена')
    cost = models.PositiveIntegerField('Себестоимость')
    quantity = models.PositiveIntegerField('Количество')

    class Meta:
        verbose_name = 'Позиция операции'
        verbose_name_plural = 'Позиции операций'

    @property
    def line_total(self):
        return self.price * self.quantity

    @property
    def line_cost(self):
        return self.cost * self.quantity
