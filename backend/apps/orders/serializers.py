from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from .services import (
    GuestQuoteRevisionStale,
    GuestQuoteValidationError,
    calculate_guest_quote,
    quote_revision_matches,
)
from apps.shipping.services import ShippingSnapshotResolutionError, resolve_comuna_shipping_snapshot

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'price', 'quantity', 'subtotal']


class GuestAccessSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()


class GuestOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {'product_id', 'quantity'}:
            raise serializers.ValidationError('Only product_id and quantity are accepted.')
        if any(isinstance(data[key], bool) or not isinstance(data[key], int) for key in data):
            raise serializers.ValidationError('Product identifiers and quantities must be integers.')
        return super().to_internal_value(data)


class ConfirmedRevisionField(serializers.CharField):
    """Keep malformed primitives available for the deterministic stale response."""

    def to_internal_value(self, data):
        if data is None or not isinstance(data, str):
            return data
        return super().to_internal_value(data)


class QuoteSerializer(serializers.Serializer):
    items = GuestOrderItemSerializer(many=True, allow_empty=False)
    comuna = serializers.IntegerField(min_value=1, required=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {'items', 'comuna'}:
            raise serializers.ValidationError('Only items and comuna are accepted.')
        return super().to_internal_value(data)

    def validate_items(self, value):
        if len(value) > 50 or len({item['product_id'] for item in value}) != len(value):
            raise serializers.ValidationError('Invalid quote items.')
        return value


class GuestQuoteLineSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.IntegerField()
    line_total = serializers.IntegerField()


class GuestQuoteResponseSerializer(serializers.Serializer):
    items = GuestQuoteLineSerializer(many=True)
    subtotal = serializers.IntegerField()
    shipping_cost = serializers.IntegerField(required=False)
    total = serializers.IntegerField(required=False)
    revision = serializers.CharField()


class QuoteErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()


class QuoteRevisionStaleSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()
    refreshed_quote = GuestQuoteResponseSerializer()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_number = serializers.CharField(read_only=True)
    guest_access = GuestAccessSerializer(read_only=True, required=False, allow_null=True)

    # NUEVO: El frontend debe enviar la lista de productos solo si compra como invitado
    guest_items = GuestOrderItemSerializer(
        many=True,
        write_only=True,
        required=False,
        help_text="Lista de productos para invitados",
    )
    confirmed_revision = ConfirmedRevisionField(
        required=False, allow_blank=True, allow_null=True, write_only=True,
        help_text="Signed quote revision explicitly confirmed by a guest.",
    )

    # Permitimos resolver la comuna por ID (tests) o por nombre + región (frontend checkout)
    comuna = serializers.IntegerField(source='comuna_id', required=False)
    comuna_name = serializers.CharField(required=False)
    region_name = serializers.CharField(required=False)

    # Nombre legible de la comuna (solo lectura) para el frontend de seguimiento
    comuna_display = serializers.SerializerMethodField()

    # Método de pago elegido en el checkout
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'phone', 'comuna', 'comuna_name', 'comuna_display', 'region_name',
            'shipping_address', 'apartment_office',
            'guest_email', 'guest_name', 'guest_items', 'confirmed_revision', 'payment_method',
            'guest_access',
            'subtotal', 'shipping_cost', 'total', 'status', 'created_at',
            'carrier', 'tracking_number', 'items'
        ]
        read_only_fields = [
            'order_number', 'subtotal', 'shipping_cost', 'total', 'status', 'created_at',
            'comuna_display', 'carrier', 'tracking_number'
        ]

    def get_comuna_display(self, obj):
        return str(obj.comuna) if obj.comuna else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        comuna = getattr(instance, 'comuna', None)
        if comuna is not None:
            data['comuna_name'] = comuna.name
            data['region_name'] = comuna.region.name if comuna.region else None
        else:
            data['comuna_name'] = None
            data['region_name'] = None

        data.setdefault('guest_access', None)
        raw_token = getattr(instance, '_guest_access_token', None)
        if raw_token:
            data['guest_access'] = {
                'token': raw_token,
                'expires_at': instance.guest_access_expires_at,
            }
            del instance._guest_access_token
        return data

    def validate(self, attrs):
        user = self.context['request'].user

        # Guest creation resolves and locks its destination inside create().
        if not user or user.is_anonymous:
            if not attrs.get('guest_email') or not attrs.get('guest_name'):
                raise serializers.ValidationError({
                    "detail": "Para compras como invitado, el correo y el nombre son obligatorios."
                })
            if not attrs.get('guest_items'):
                raise serializers.ValidationError({
                    "guest_items": "Debes enviar la lista de productos del carrito local."
                })
            if 'comuna_id' in attrs:
                attrs.pop('comuna_name', None)
                attrs.pop('region_name', None)
                attrs['_comuna_selector'] = {'comuna_id': attrs['comuna_id']}
            else:
                comuna_name = attrs.pop('comuna_name', None)
                region_name = attrs.pop('region_name', None)
                if not comuna_name or not region_name:
                    raise serializers.ValidationError({
                        'comuna': 'Debes indicar la comuna de entrega.'
                    })
                attrs['_comuna_selector'] = {
                    'comuna_name': comuna_name,
                    'region_name': region_name,
                }
            return attrs

        # Resolve the shipping snapshot without importing the shipping model.
        if 'comuna_id' not in attrs:
            comuna_name = attrs.pop('comuna_name', None)
            region_name = attrs.pop('region_name', None)
            if not comuna_name or not region_name:
                raise serializers.ValidationError({
                    'comuna': 'Debes indicar la comuna de entrega.'
                })
            try:
                snapshot = resolve_comuna_shipping_snapshot(
                    comuna_name=comuna_name,
                    region_name=region_name,
                )
            except ShippingSnapshotResolutionError:
                raise serializers.ValidationError({
                    'comuna': 'La comuna y región indicadas no son válidas.'
                })
            attrs['comuna_id'] = snapshot.id
        else:
            attrs.pop('comuna_name', None)
            attrs.pop('region_name', None)
            try:
                snapshot = resolve_comuna_shipping_snapshot(comuna_id=attrs['comuna_id'])
            except ShippingSnapshotResolutionError:
                raise serializers.ValidationError({'comuna': 'La comuna indicada no es válida.'})
        attrs['_comuna_snapshot'] = snapshot

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user

        if not user or user.is_anonymous:
            guest_items = validated_data.pop('guest_items')
            confirmed_revision = validated_data.pop('confirmed_revision', None)
            comuna_selector = validated_data.pop('_comuna_selector')
            with transaction.atomic():
                try:
                    quote = calculate_guest_quote(
                        guest_items, comuna_selector=comuna_selector, lock=True
                    )
                except GuestQuoteValidationError as error:
                    raise serializers.ValidationError({
                        'guest_items': 'Unable to resolve the confirmed quote.'
                    }) from error
                if not quote_revision_matches(confirmed_revision, quote):
                    raise GuestQuoteRevisionStale(quote)

                order = Order.objects.create(
                    user=None,
                    guest_email=validated_data.get('guest_email'),
                    guest_name=validated_data.get('guest_name'),
                    phone=validated_data['phone'],
                    comuna_id=quote.comuna_id,
                    shipping_address=validated_data['shipping_address'],
                    apartment_office=validated_data.get('apartment_office', ''),
                    payment_method=validated_data.get('payment_method', 'webpay'),
                    subtotal=quote.subtotal,
                    shipping_cost=quote.shipping_cost,
                    total=quote.total,
                )
                order._guest_access_token = order.issue_guest_access()
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        product_id=line.product_id,
                        product_name=line.product_name,
                        price=line.unit_price,
                        quantity=line.quantity,
                    )
                    for line in quote.items
                ])
            return order

        comuna_id = validated_data.pop('comuna_id')
        comuna_snapshot = validated_data.pop('_comuna_snapshot')
        costo_envio_chile = comuna_snapshot.shipping_cost
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
            try:
                quote = calculate_guest_quote(guest_items, comuna_selector=comuna_id)
            except GuestQuoteValidationError as error:
                raise serializers.ValidationError({'guest_items': str(error)}) from error
            subtotal_productos = quote.subtotal
            productos_a_comprar = [
                {
                    'product_id': line.product_id,
                    'name': line.product_name,
                    'price': line.unit_price,
                    'quantity': line.quantity,
                }
                for line in quote.items
            ]

        total_final = subtotal_productos + costo_envio_chile

        # PROCESO DE GUARDADO ATÓMICO (Sirve para ambos casos)
        with transaction.atomic():
            order = Order.objects.create(
                # Evaluamos de forma segura si el usuario está autenticado
                user=user if user.is_authenticated else None,
                guest_email=validated_data.get('guest_email'),
                guest_name=validated_data.get('guest_name'),
                phone=validated_data['phone'],
                comuna_id=comuna_id,
                shipping_address=validated_data['shipping_address'],
                apartment_office=validated_data.get('apartment_office', ''),
                payment_method=payment_method,
                subtotal=subtotal_productos,
                shipping_cost=costo_envio_chile,
                total=total_final
            )

            if not user.is_authenticated:
                order._guest_access_token = order.issue_guest_access()

            # Clonamos y congelamos los productos recolectados
            for prod in productos_a_comprar:
                OrderItem.objects.create(
                    order=order,
                    product_id=prod.get('product_id') or prod['product'].id,
                    product_name=prod['name'],
                    price=prod['price'],
                    quantity=prod['quantity']
                )

            # Si era un usuario registrado, limpiamos su carro de la BD
            if user and user.is_authenticated:
                cart_items.delete()

        return order
class OrderCreateSerializer(serializers.ModelSerializer):
    comuna = serializers.IntegerField(source='comuna_id', required=False)
    comuna_name = serializers.CharField(required=False)
    region_name = serializers.CharField(required=False)
    guest_items = GuestOrderItemSerializer(many=True, required=False, write_only=True, help_text='Lista de productos para invitados')
    confirmed_revision = ConfirmedRevisionField(
        required=False, allow_blank=True, allow_null=True, write_only=True,
        help_text='Signed quote revision explicitly confirmed by a guest.',
    )
    payment_method = serializers.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES, required=False
    )

    class Meta:
        model = Order
        fields = ['phone', 'comuna', 'comuna_name', 'region_name', 'shipping_address', 'apartment_office', 'guest_email', 'guest_name', 'guest_items', 'confirmed_revision', 'payment_method']
