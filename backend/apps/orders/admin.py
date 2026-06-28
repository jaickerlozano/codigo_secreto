from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Los productos de una orden procesada no se deben editar a mano por el operario
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Mostramos los datos de contacto chilenos, la comuna, los montos y el estado operacional
    list_display = ('id', 'buyer_display', 'phone', 'comuna', 'total_clp', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'comuna__region')
    search_fields = ('id', 'guest_email', 'guest_name', 'user__email', 'phone')
    ordering = ('-created_at',)
    
    # Enlazamos los productos comprados dentro de la misma ficha del pedido
    inlines = [OrderItemInline]
    
    # Solo permitimos que el administrador altere el ESTADO del pedido (Ej: pasarlo de PENDING a SHIPPED)
    # Bloqueamos la edición manual de los montos de dinero para proteger la contabilidad
    readonly_fields = ('user', 'guest_email', 'guest_name', 'phone', 'comuna', 'shipping_address', 'apartment_office', 'subtotal', 'shipping_cost', 'total', 'created_at', 'updated_at')

    def buyer_display(self, obj):
        # Muestra el nombre real ya sea que compre un cliente registrado o un invitado
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.guest_name or "Invitado sin nombre"
    buyer_display.short_description = "Comprador"

    def total_clp(self, obj):
        return f"${obj.total:,}".replace(",", ".")
    total_clp.short_description = "Total"
