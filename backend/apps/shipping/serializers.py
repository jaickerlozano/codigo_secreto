from rest_framework import serializers
from .models import Region, Comuna

class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = ['id', 'name', 'shipping_cost', 'is_active']


class RegionSerializer(serializers.ModelSerializer):
    # Traemos las comunas asociadas de forma anidada
    comunas = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ['id', 'name', 'ordinal_number', 'comunas']

    def get_comunas(self, obj):
        # Filtramos para enviar al frontend solo las comunas donde sí hacemos despachos
        comunas_activas = obj.comunas.filter(is_active=True)
        return ComunaSerializer(comunas_activas, many=True).data