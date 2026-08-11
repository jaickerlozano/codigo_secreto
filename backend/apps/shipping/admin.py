from django.contrib import admin
from .models import Region, Comuna, RegionalShippingOption

class ComunaInline(admin.TabularInline):
    model = Comuna
    extra = 0
    fields = ('name', 'shipping_cost', 'is_active')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ordinal_number')
    ordering = ('ordinal_number',)
    # Permite ver y editar todas las comunas de una región en la misma pantalla
    inlines = [ComunaInline]
    list_display_links = ['id', 'name']

@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'region', 'price_clp', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'region__name')
    list_editable = ('is_active',) # Permite activar/desactivar comunas directo desde la lista
    list_display_links = ['id', 'name']

    def price_clp(self, obj):
        return f"${obj.shipping_cost:,}".replace(",", ".")
    price_clp.short_description = "Costo de Envío"


@admin.register(RegionalShippingOption)
class RegionalShippingOptionAdmin(admin.ModelAdmin):
    list_display = ('key', 'carrier', 'tariff_clp', 'min_lead_days', 'max_lead_days', 'is_active')
    list_editable = ('is_active',)  # Permite activar/desactivar la opción regional directo desde la lista

    def tariff_clp(self, obj):
        return f"${obj.tariff:,}".replace(",", ".")
    tariff_clp.short_description = "Tarifa de Envío"
