from .models import Cart, CartItem
from apps.products.serializers import ProductSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .services import calculate_cart_totals


class CartItemSerializer(serializers.ModelSerializer):
    # Traemos los datos completos del producto de esta forma
    product = ProductSerializer(read_only=True)

    # Expongo la propiedad dinámica que cree en el modelo de forma explícita
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = ['cart', 'product', 'quantity', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    # 1. Anidamos la lista de ítems usando el related_name=items que se definió en el modelo
    items = CartItemSerializer(many=True, read_only=True)

    # 2. Campos financieros calculados en el backend; el frontend solo los muestra
    monto_total_final = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    shipping_cost = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    free_shipping_progress = serializers.SerializerMethodField()
    free_shipping_threshold = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        # Omitimos mostrar el ID del usuario para no exponer datos sensibles y nos enfocamos en el contenido
        fields = [
            'id',
            'created_at',
            'updated_at',
            'items',
            'monto_total_final',
            'subtotal',
            'shipping_cost',
            'total',
            'free_shipping_progress',
            'free_shipping_threshold',
        ]

    def _cart_totals(self, obj):
        """Cachea los totales por instancia para evitar recomputos."""
        cache = getattr(self, '_cached_totals', None)
        if cache is None:
            cache = {}
            setattr(self, '_cached_totals', cache)

        if obj.pk not in cache:
            cache[obj.pk] = calculate_cart_totals(obj, comuna_selector=self.context.get('comuna_selector'))

        return cache[obj.pk]

    @extend_schema_field(OpenApiTypes.INT)
    def get_monto_total_final(self, obj):
        # Campo histórico: suma de los subtotales de los ítems (sin envío).
        return self._cart_totals(obj)['subtotal']

    @extend_schema_field(OpenApiTypes.INT)
    def get_subtotal(self, obj):
        return self._cart_totals(obj)['subtotal']

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_shipping_cost(self, obj):
        return self._cart_totals(obj)['shipping_cost']

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_total(self, obj):
        return self._cart_totals(obj)['total']

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_free_shipping_progress(self, obj):
        return self._cart_totals(obj)['free_shipping_progress']

    @extend_schema_field(OpenApiTypes.INT)
    def get_free_shipping_threshold(self, obj):
        return 0


class AddToCartSerializer(serializers.Serializer):
    # Validamos que el ID del producto que envía el frontend realmente exista en la tienda
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

    def validate_product_id(self, value):
        from apps.products.models import Product
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("El producto seleccionado no existe.")
        return value
