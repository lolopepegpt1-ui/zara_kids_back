from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin, TabularInline

from .models import AppSettings, Product, ProductSize, Store, Transaction, TransactionItem


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    pass


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin, ModelAdmin):
    pass


@admin.register(Store)
class StoreAdmin(ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    search_fields = ('code', 'name')


@admin.register(AppSettings)
class AppSettingsAdmin(ModelAdmin):
    list_display = ('id', 'updated_at')


class ProductSizeInline(TabularInline):
    model = ProductSize
    extra = 0


@admin.register(ProductSize)
class ProductSizeAdmin(ModelAdmin):
    list_display = ('product', 'size', 'stock')
    list_filter = ('product__category',)
    search_fields = ('product__name', 'product__barcode', 'size')


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'barcode', 'category', 'cost_price', 'retail_price', 'is_active')
    list_display_links = ('name',)
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'barcode')
    inlines = [ProductSizeInline]


class TransactionItemInline(TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ('product_name', 'size', 'price', 'cost', 'quantity')
    can_delete = False


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('number', 'type', 'store', 'cashier_name', 'total_amount', 'payment_method', 'created_at')
    list_filter = ('type', 'store', 'payment_method', 'created_at')
    search_fields = ('number', 'cashier_name')
    readonly_fields = ('number', 'created_at')
    inlines = [TransactionItemInline]

# Register your models here.
