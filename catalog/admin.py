from django.contrib import admin
from .models import *


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    pass


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основное', {'fields': ('name', )}),
        ('Дополнительное', {'fields': ('description', 'image')}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'category', 'gender', 'brand', 'price']
    list_filter = ['category', 'gender', 'brand']


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    pass


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    class ProductInstanceInline(admin.TabularInline):
        model = ProductInstance

    inlines = [ProductInstanceInline]


@admin.register(ProductInstanceStatus)
class ProductInstanceStatusAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductInstance)
class ProductInstanceAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'size', 'invoice', 'purchase_price', 'quantity', 'status']
    list_filter = ['product', 'invoice', 'status']
    fieldsets = (
        ('Товар', {'fields': ('product', 'size', 'quantity', 'status')}),
        ('Закупка', {'fields': ('invoice', 'purchase_price')}),
    )

    class OrderItemInline(admin.TabularInline):
        model = OrderItem

    inlines = [OrderItemInline]


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'status']
    list_filter = ['status']
    fieldsets = (
        ('Информация о заказе', {'fields': ('user', 'status')}),
        ('Информация о доставке', {'fields': ('details', 'delivery_price')}),
    )

    class OrderItemInline(admin.TabularInline):
        model = OrderItem

    inlines = [OrderItemInline]
