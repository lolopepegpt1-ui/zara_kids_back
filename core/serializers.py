from rest_framework import serializers

from .models import Product, ProductSize, Store, Transaction, TransactionItem


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['code', 'name']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'size', 'stock']


class ProductSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'barcode',
            'category',
            'cost_price',
            'retail_price',
            'image',
            'image_url',
            'is_active',
            'sizes',
        ]
        extra_kwargs = {'image': {'write_only': True, 'required': False}}

    def get_image_url(self, obj):
        if not obj.image:
            return ''
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    def create(self, validated_data):
        sizes = validated_data.pop('sizes', [])
        product = Product.objects.create(**validated_data)
        for size in sizes:
            ProductSize.objects.create(product=product, **size)
        return product

    def update(self, instance, validated_data):
        sizes = validated_data.pop('sizes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if sizes is not None:
            instance.sizes.all().delete()
            for size in sizes:
                ProductSize.objects.create(product=instance, **size)
        return instance


class TransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionItem
        fields = ['product', 'product_name', 'size', 'price', 'cost', 'quantity', 'line_total', 'line_cost']


class TransactionSerializer(serializers.ModelSerializer):
    items = TransactionItemSerializer(many=True, read_only=True)
    store_code = serializers.CharField(source='store.code', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    related_transaction_number = serializers.CharField(source='related_transaction.number', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'number',
            'store_code',
            'store_name',
            'type',
            'cashier_name',
            'total_amount',
            'total_cost',
            'payment_method',
            'related_transaction',
            'related_transaction_number',
            'authorized_by',
            'created_at',
            'items',
        ]


class SettingsSerializer(serializers.Serializer):
    store = StoreSerializer()

    @classmethod
    def build(cls):
        store, _ = Store.objects.get_or_create(code='main', defaults={'name': 'ZARA KIDS'})
        return {
            'store': StoreSerializer(store).data,
        }
