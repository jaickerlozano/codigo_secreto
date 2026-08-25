from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils import timezone

from .models import NotificationDelivery, Order, OrderItem
from .notifications import retry_delivery
from .services import InvalidFulfillmentError, fulfill_dispatch


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False

    @admin.display(description='Subtotal')
    def subtotal(self, obj):
        return obj.subtotal if obj.subtotal is not None else 'No disponible'

class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"
        error_messages = {
            "carrier": {"required": "El transportista es obligatorio."},
        }

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = "admin/orders/order/change_form.html"
    form = OrderAdminForm
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
        # Campos de ciclo de vida: solo cambian mediante la acción de despacho
        'status', 'dispatched_at',
    )
    actions = ('revoke_guest_access', 'rotate_guest_access', 'dispatch_orders')

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["show_save_and_dispatch"] = bool(
            change
            and obj
            and obj.status == "PAID"
            and self.has_change_permission(request, obj)
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_change(self, request, obj):
        if "_save_and_dispatch" not in request.POST:
            return super().response_change(request, obj)

        try:
            fulfill_dispatch(
                order=obj,
                carrier=obj.carrier,
                estimated_delivery_date=obj.estimated_delivery_date,
                tracking_number=obj.tracking_number,
            )
        except InvalidFulfillmentError as error:
            self.message_user(
                request,
                f"No se pudo despachar {obj.order_number}: {error}",
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                f"Pedido {obj.order_number} guardado y despachado correctamente.",
                level=messages.SUCCESS,
            )
        return HttpResponseRedirect(request.path)

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

    @admin.action(description="Despachar pedidos seleccionados")
    def dispatch_orders(self, request, queryset):
        """Dispatch each selected PAID order with its recorded carrier/date."""
        dispatched = 0
        for order in queryset:
            try:
                fulfill_dispatch(order=order, carrier=order.carrier, estimated_delivery_date=order.estimated_delivery_date, tracking_number=order.tracking_number)
                dispatched += 1
            except InvalidFulfillmentError as error:
                self.message_user(request, f"No se pudo despachar {order.order_number}: {error}",
                                  level=messages.ERROR)
        if dispatched:
            self.message_user(request, f"{dispatched} pedido(s) despachado(s) correctamente.")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'event', 'status', 'attempts', 'next_retry_at', 'sent_at')
    list_filter = ('status', 'event')
    readonly_fields = ('order', 'event', 'status', 'attempts', 'last_error', 'next_retry_at', 'sent_at', 'created_at', 'updated_at')
    actions = ('retry_failed',)

    @admin.action(description="Reintentar notificaciones fallidas")
    def retry_failed(self, request, queryset):
        failed = list(queryset.filter(status="FAILED"))
        for delivery in failed:
            retry_delivery(delivery.id)
        self.message_user(request, f"{len(failed)} notificación(es) reintentada(s).")
