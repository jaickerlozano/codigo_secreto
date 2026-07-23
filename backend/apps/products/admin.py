# backend/apps/products/admin.py
from django.contrib import admin
from .models import Product, Supplier, Category, StockMovement, ProductImage # 💡 Agregamos ProductImage
from django.utils.html import format_html

# 💡 ESTA ES LA CLAVE: Define las casillas de carga masiva en línea para la galería
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Genera 3 filas vacías por defecto en el panel para subir fotos al mismo tiempo
    fields = ['image']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'parent', 'description_short')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    ordering = ('parent_id', 'name')

    def description_short(self, obj):
        if obj.description and len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description or "-"
    description_short.short_description = "Descripción"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contact', 'email', 'phone')
    search_fields = ('name', 'contact', 'email')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'name', 'category', 'supplier', 'badge', 'experience_level', 'stock_status', 'minimum_stock', 'price_clp', 'created_at', 'updated_at')
    list_filter = ('category', 'supplier', 'badge', 'experience_level')
    search_fields = ('name', 'description', 'sku')
    ordering = ('name',)
    readonly_fields = ('current_stock', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'category', 'supplier', 'price', 'current_stock', 'minimum_stock', 'image', 'sku')
        }),
        ('UI Config', {
            'fields': ('icon', 'gradient', 'experience_level', 'features', 'badge'),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    # 💡 INYECTAMOS LA GALERÍA AQUÍ: Esto dibuja las filas de carga justo debajo de los fieldsets
    inlines = [ProductImageInline]

    def price_clp(self, obj):
        return f"${obj.price:,}".replace(",", ".")
    price_clp.short_description = "Precio"

    def stock_status(self, obj):
        if obj.current_stock == 0:
            return format_html('<b style="color: red;">{0}</b>', "⚠️ SIN STOCK (0)")
        elif obj.current_stock <= obj.minimum_stock:
            return format_html('<b style="color: orange;">🟨 Stock Bajo ({0})</b>', obj.current_stock)
        return format_html('<span style="color: green;">🟩 {0} Unidades</span>', obj.current_stock)
    stock_status.short_description = "Estado del Stock"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'get_type_badge', 'quantity', 'timestamp')
    list_display_links = ('id', 'product') 
    list_filter = ('movement_type', 'timestamp', 'product')
    search_fields = ('product__name',)
    ordering = ('-timestamp',)
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_type_badge(self, obj):
        if obj.movement_type == 'IN':
            return format_html('<span style="background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "ENTRADA")
        return format_html('<span style="background: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "SALIDA")
    get_type_badge.short_description = "Tipo"
