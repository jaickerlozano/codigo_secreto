from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'amount_clp', 'status_badge', 'gateway_reference', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order__id', 'gateway_reference')
    ordering = ('-created_at',)
    
    # Como es un historial contable financiero, BLOQUEAMOS cualquier edición manual desde el admin
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

    def amount_clp(self, obj):
        return f"${obj.amount:,}".replace(",", ".")
    amount_clp.short_description = "Monto"

    def status_badge(self, obj):
        from django.utils.html import format_html
        if obj.status == 'APPROVED':
            # Inyectamos el texto pasándolo como argumento seguro después de la coma utilizando {0}
            return format_html('<span style="background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "APROBADO")
        elif obj.status == 'REJECTED':
            return format_html('<span style="background: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "RECHAZADO")
        
        return format_html('<span style="background: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{0}</span>', "PENDIENTE")
    status_badge.short_description = "Estado"
