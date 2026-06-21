from .models import Cart, CartItem
from apps.products.serializers import ProductSerializer
from rest_framework import serializers

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

    # 2. Declaramos un campo dinámico para calcular el total final en memoria de Python
    monto_total_final = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        # Omitimos mostrar el ID del usuario para no exponer datos sensibles y nos enfocamos en el contenido
        fields = ['id', 'created_at', 'updated_at', 'items', 'monto_total_final']

    def get_monto_total_final(self, obj):
        # 'obj' representa la instancia del carro actual que se está consultando.
        # Recorremos en un bucle simple de Python todos los ítems asociados a ESTE carro
        # y sumamos sus subtotales de forma aislada y segura.
        return sum(item.subtotal for item in obj.items.all())


class AddToCartSerializer(serializers.ModelSerializer):
    # Validamos que el ID del producto que envía el frontend realmente exista en la tienda
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

    def validate_product_id(self, value):
        from apps.products.models import Product
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("El producto seleccionado no existe.")
        return value
