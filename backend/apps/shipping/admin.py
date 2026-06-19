from django.contrib import admin
from .models import Region, Comuna

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


@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'region', 'price_clp', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'region__name')
    list_editable = ('is_active',) # Permite activar/desactivar comunas directo desde la lista

    def price_clp(self, obj):
        return f"${obj.shipping_cost:,}".replace(",", ".")
    price_clp.short_description = "Costo de Envío"
