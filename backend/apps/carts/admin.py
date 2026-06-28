from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ('product',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items_count', 'total_clp', 'updated_at')
    search_fields = ('user__email', 'user__first_name')
    ordering = ('-updated_at',)
    inlines = [CartItemInline]

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Variedad de Productos"

    def total_clp(self, obj):
        # Usamos la propiedad dinámica que escribimos en el serializador para sumar en el admin
        total = sum(item.subtotal for item in obj.items.all())
        return f"${total:,}".replace(",", ".")
    total_clp.short_description = "Monto Estimado"
