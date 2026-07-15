from rest_framework import serializers
from django.db import transaction
from apps.products.models import Product
from apps.shipping.models import Comuna
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'price', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_number = serializers.CharField(read_only=True)

    # NUEVO: El frontend debe enviar la lista de productos solo si compra como invitado
    guest_items = serializers.JSONField(write_only=True, required=False, help_text="Lista de productos para invitados")

    # Permitimos resolver la comuna por ID (tests) o por nombre + región (frontend checkout)
    comuna = serializers.PrimaryKeyRelatedField(queryset=Comuna.objects.all(), required=False)
    comuna_name = serializers.CharField(required=False)
    region_name = serializers.CharField(required=False)

    # Método de pago elegido en el checkout
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'phone', 'comuna', 'comuna_name', 'region_name',
            'shipping_address', 'apartment_office',
            'guest_email', 'guest_name', 'guest_items', 'payment_method',
            'subtotal', 'shipping_cost', 'total', 'status', 'created_at', 'items'
        ]
        read_only_fields = ['order_number', 'subtotal', 'shipping_cost', 'total', 'status', 'created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        comuna = getattr(instance, 'comuna', None)
        if comuna is not None:
            data['comuna_name'] = comuna.name
            data['region_name'] = comuna.region.name if comuna.region else None
        else:
            data['comuna_name'] = None
            data['region_name'] = None
        return data

    def validate(self, attrs):
        user = self.context['request'].user

        # Resolvemos la comuna: preferimos el ID, si no viene usamos nombre + región
        if 'comuna' not in attrs:
            comuna_name = attrs.pop('comuna_name', None)
            region_name = attrs.pop('region_name', None)
            if not comuna_name or not region_name:
                raise serializers.ValidationError({
                    'comuna': 'Debes indicar la comuna de entrega.'
                })
            try:
                attrs['comuna'] = Comuna.objects.get(
                    name__iexact=comuna_name,
                    region__name__iexact=region_name
                )
            except Comuna.DoesNotExist:
                raise serializers.ValidationError({
                    'comuna': 'La comuna y región indicadas no son válidas.'
                })
        else:
            attrs.pop('comuna_name', None)
            attrs.pop('region_name', None)

        # SI ES INVITADO (No está autenticado)
        if not user or user.is_anonymous:
            if not attrs.get('guest_email') or not attrs.get('guest_name'):
                raise serializers.ValidationError({
                    "detail": "Para compras como invitado, el correo y el nombre son obligatorios."
                })
            if not attrs.get('guest_items'):
                raise serializers.ValidationError({
                    "guest_items": "Debes enviar la lista de productos del carrito local."
                })
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        comuna_seleccionada = validated_data['comuna']
        costo_envio_chile = comuna_seleccionada.shipping_cost
        payment_method = validated_data.get('payment_method', 'webpay')

        # Inicializamos variables para el bucle de clonación
        productos_a_comprar = []
        subtotal_productos = 0

        # LÓGICA RUTA A: USUARIO REGISTRADO (Usa el carro de la Base de Datos)
        if user and user.is_authenticated:
            # Los datos de invitado no aplican para usuarios autenticados
            validated_data.pop('guest_items', None)
            cart = user.cart
            cart_items = cart.items.all()

            if not cart_items.exists():
                raise serializers.ValidationError({"detail": "No puedes crear un pedido con el carrito vacío."})

            subtotal_productos = sum(item.subtotal for item in cart_items)

            for item in cart_items:
                productos_a_comprar.append({
                    'product': item.product,
                    'name': item.product.name,
                    'price': item.product.price,
                    'quantity': item.quantity
                })

        # LÓGICA RUTA B: INVITADO ANÓNIMO (Lee la lista del LocalStorage que envía el Frontend)
        else:
            guest_items = validated_data.pop('guest_items')
            for item in guest_items:
                try:
                    product = Product.objects.get(id=item['product_id'])
                    quantity = int(item['quantity'])

                    if quantity < 1:
                        continue

                    subtotal_productos += (product.price * quantity)
                    productos_a_comprar.append({
                        'product': product,
                        'name': product.name,
                        'price': product.price,
                        'quantity': quantity
                    })
                except (Product.DoesNotExist, KeyError, ValueError):
                    raise serializers.ValidationError({"guest_items": "Uno de los productos enviados no es válido."})

        total_final = subtotal_productos + costo_envio_chile

        # PROCESO DE GUARDADO ATÓMICO (Sirve para ambos casos)
        with transaction.atomic():
            order = Order.objects.create(
                # Evaluamos de forma segura si el usuario está autenticado
                user=user if user.is_authenticated else None,
                guest_email=validated_data.get('guest_email'),
                guest_name=validated_data.get('guest_name'),
                phone=validated_data['phone'],
                comuna=comuna_seleccionada,
                shipping_address=validated_data['shipping_address'],
                apartment_office=validated_data.get('apartment_office', ''),
                payment_method=payment_method,
                subtotal=subtotal_productos,
                shipping_cost=costo_envio_chile,
                total=total_final
            )

            # Clonamos y congelamos los productos recolectados
            for prod in productos_a_comprar:
                OrderItem.objects.create(
                    order=order,
                    product=prod['product'],
                    product_name=prod['name'],
                    price=prod['price'],
                    quantity=prod['quantity']
                )

            # Si era un usuario registrado, limpiamos su carro de la BD
            if user and user.is_authenticated:
                cart_items.delete()

        return order

