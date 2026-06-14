from django.contrib import admin
from .models import Product, Supplier, Category, StockMovement

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'supplier', 'current_stock', 'minimum_stock', 'price')
    search_fields = ('name',)
    list_filter = ('category', 'supplier')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'type', 'quantity', 'timestamp')
    list_filter = ('type', 'timestamp')