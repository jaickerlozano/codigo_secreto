from rest_framework import serializers
from django.db import transaction
from apps.carts.models import Cart
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    """Molde para ver los productos ya comprados y congelados"""
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'price', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    # Mostramos los ítems del pedido usando el serializador de arriba
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        # Campos que el frontend completará en el formulario, y los que Django calculará solos
        fields = [
            'id', 'phone', 'comuna', 'shipping_address', 'apartment_office', 
            'subtotal', 'shipping_cost', 'total', 'status', 'created_at', 'items'
        ]
        # Estos campos los calcula el backend en base al carrito; el frontend NO los puede digitar
        read_only_fields = ['subtotal', 'shipping_cost', 'total', 'status', 'created_at']

    def create(self, validated_data):
        # 1. Conseguimos al usuario que está comprando a través del contexto de la petición de DRF
        user = self.context['request'].user
        
        # 2. Obtenemos su carrito de compras de la Base de Datos
        cart = user.cart
        cart_items = cart.items.all()

        # Si el carrito está vacío, detenemos la operación de inmediato
        if not cart_items.exists():
            raise serializers.ValidationError({"detail": "No puedes crear un pedido con el carrito vacío."})

        # 3. Calculamos los montos financieros en base a su carro y la comuna elegida
        comuna_seleccionada = validated_data['comuna']
        
        subtotal_productos = sum(item.subtotal for item in cart_items)
        costo_envio_chile = comuna_seleccionada.shipping_cost
        total_final = subtotal_productos + costo_envio_chile

        # 4. Iniciamos un bloque atómico para asegurar que se guarde TODO o NADA si hay un fallo eléctrico
        with transaction.atomic():
            # Creamos la cabecera del Pedido asociándolo al usuario actual
            order = Order.objects.create(
                user=user,
                phone=validated_data['phone'],
                comuna=comuna_seleccionada,
                shipping_address=validated_data['shipping_address'],
                apartment_office=validated_data.get('apartment_office', ''),
                subtotal=subtotal_productos,
                shipping_cost=costo_envio_chile,
                total=total_final
            )

            # 5. REGLA DE ORO: Clonamos y congelamos cada producto del carrito dentro del pedido
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name, # Congelamos el nombre por si cambia mañana
                    price=item.product.price,       # Congelamos el precio de este milisegundo
                    quantity=item.quantity
                )

            # 6. Una vez que el pedido se guardó a salvo, VACIAMOS el carro del cliente automáticamente
            cart_items.delete()

        return order
