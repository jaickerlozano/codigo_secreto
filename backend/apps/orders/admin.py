from django.contrib import admin
from django.utils import timezone

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer_display', 'phone', 'comuna', 'total_clp', 'status', 'guest_access_status', 'created_at')
    list_filter = ('status', 'created_at', 'guest_access_revoked_at', 'comuna__region')
    search_fields = ('id', 'guest_email', 'guest_name', 'user__email', 'phone')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    readonly_fields = (
        'user', 'guest_email', 'guest_name', 'phone', 'comuna', 'shipping_address', 'apartment_office',
        'subtotal', 'shipping_cost', 'total', 'created_at', 'updated_at',
        'guest_access_digest', 'guest_access_issued_at', 'guest_access_expires_at',
        'guest_access_revoked_at', 'guest_access_version',
    )
    actions = ('revoke_guest_access', 'rotate_guest_access')

    def guest_access_status(self, obj):
        if obj.guest_access_revoked_at:
            return "Revocado"
        if obj.guest_access_expires_at and obj.guest_access_expires_at < timezone.now():
            return "Expirado"
        if obj.guest_access_digest:
            return "Activo"
        return "Sin capacidad"
    guest_access_status.short_description = "Acceso de invitado"

    @admin.action(description="Revocar acceso de invitado")
    def revoke_guest_access(self, request, queryset):
        count = 0
        for order in queryset:
            order.revoke_guest_access()
            count += 1
        self.message_user(request, f"{count} pedido(s) revocado(s) correctamente.")

    @admin.action(description="Rotar acceso de invitado")
    def rotate_guest_access(self, request, queryset):
        links = []
        for order in queryset:
            raw = order.rotate_guest_access()
            links.append(f"{order.order_number}: {raw}")
        if links:
            self.message_user(
                request,
                "Nuevos enlaces de acceso generados. Compártelos de forma segura; "
                "esta es la única vez que se mostrarán:\n" + "\n".join(links),
            )
        else:
            self.message_user(request, "No se seleccionaron pedidos.")

    def buyer_display(self, obj):
        # Muestra el nombre real ya sea que compre un cliente registrado o un invitado
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.guest_name or "Invitado sin nombre"
    buyer_display.short_description = "Comprador"

    def total_clp(self, obj):
        return f"${obj.total:,}".replace(",", ".")
    total_clp.short_description = "Total"
