from rest_framework import serializers
from .models import Region, Comuna

class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = ['id', 'name', 'shipping_cost', 'is_active']


class RegionalDispatchOptionSerializer(serializers.Serializer):
    """The one applicable regional dispatch profile for a non-Santiago comuna."""

    shipping_option_id = serializers.IntegerField(read_only=True)
    key = serializers.CharField(read_only=True)
    carrier = serializers.CharField(read_only=True)
    min_lead_days = serializers.IntegerField(read_only=True)
    max_lead_days = serializers.IntegerField(read_only=True)


class DispatchOptionsSerializer(serializers.Serializer):
    """Read-only dispatch options for a selected destination comuna.

    Santiago comunas expose the next four future Tuesday/Thursday dates;
    non-Santiago comunas expose the single applicable regional option.
    Exactly one of ``dates``/``shipping_option`` is populated per mode.
    """

    comuna_id = serializers.IntegerField(read_only=True)
    mode = serializers.ChoiceField(
        choices=[("santiago", "santiago"), ("regional", "regional")],
        read_only=True,
    )
    dates = serializers.ListField(
        child=serializers.DateField(), read_only=True, allow_null=True
    )
    shipping_option = RegionalDispatchOptionSerializer(
        read_only=True, allow_null=True
    )


class RegionSerializer(serializers.ModelSerializer):
    # Traemos las comunas asociadas de forma anidada
    comunas = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ['id', 'name', 'ordinal_number', 'comunas']

    def get_comunas(self, obj):
        # Filtramos para enviar al frontend solo las comunas donde sí hacemos despachos
        comunas_activas = obj.comunas.filter(is_active=True, shipping_cost__gt=0)
        return ComunaSerializer(comunas_activas, many=True).data
