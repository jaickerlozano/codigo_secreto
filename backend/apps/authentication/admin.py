from django.contrib import admin
from django.utils.html import format_html
from apps.products.models import Product, Supplier, Category, StockMovement

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
    # CORRECCIÓN: Cambiamos 'price' por 'price_clp' para usar nuestro método personalizado
    list_display = ('id', 'name', 'category', 'supplier', 'stock_status', 'minimum_stock', 'price_clp', 'created_at', 'updated_at')
    list_filter = ('category', 'supplier')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('current_stock', 'created_at', 'updated_at')

    # CORRECCIÓN: Renombrado a price_clp para no chocar con el campo del modelo
    def price_clp(self, obj):
        return f"${obj.price:,}".replace(",", ".")
    price_clp.short_description = "Precio"

    def stock_status(self, obj):
        if obj.current_stock == 0:
            # Django 6 exige marcar de forma segura strings fijos o usar marcadores de posición
            return format_html('<b style="color: red;">{0}</b>', "⚠️ SIN STOCK (0)")
        
        elif obj.current_stock <= obj.minimum_stock:
            return format_html('<b style="color: orange;">🟨 Stock Bajo ({0})</b>', obj.current_stock)
        
        return format_html('<span style="color: green;">🟩 {0} Unidades</span>', obj.current_stock)
    stock_status.short_description = "Estado del Stock"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'get_type_badge', 'quantity', 'timestamp')
    list_filter = ('movement_type', 'timestamp', 'product')
    search_fields = ('product__name',)
    ordering = ('-timestamp',)
    
    # Bloquea la edición de movimientos existentes en el Admin
    def has_change_permission(self, request, obj=None):
        return False

    # Bloquea la eliminación de movimientos existentes en el Admin
    def has_delete_permission(self, request, obj=None):
        return False

    def get_type_badge(self, obj):
        # CORRECCIÓN: Añadimos marcadores {0} para cumplir la regla estricta de Django 6
        if obj.movement_type == 'IN':
            return format_html('<span style="background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "ENTRADA")
        return format_html('<span style="background: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "SALIDA")
    get_type_badge.short_description = "Tipo"