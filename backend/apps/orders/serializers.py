from rest_framework import serializers
from .models import Order, OrderItem
from .services import (
    EmptyCartError,
    GuestQuoteValidationError,
    InvalidCheckoutKeyError,
    create_order,
    normalize_checkout_key,
)
from apps.shipping.services import ShippingSnapshotResolutionError, resolve_shipping_price

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
            'carrier', 'tracking_number', 'items',
            'delivery_kind', 'requested_dispatch_date', 'special_delivery_agreed_at',
            'estimated_delivery_date', 'dispatched_at',
        ]
        read_only_fields = [
            'order_number', 'subtotal', 'shipping_cost', 'total', 'status', 'created_at',
            'comuna_display', 'carrier', 'tracking_number',
            'delivery_kind', 'requested_dispatch_date', 'special_delivery_agreed_at',
            'estimated_delivery_date', 'dispatched_at',
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

        # Resolve the exclusive shipping price authority without importing the shipping model.
        if 'comuna_id' not in attrs:
            comuna_name = attrs.pop('comuna_name', None)
            region_name = attrs.pop('region_name', None)
            if not comuna_name or not region_name:
                raise serializers.ValidationError({
                    'comuna': 'Debes indicar la comuna de entrega.'
                })
            try:
                snapshot = resolve_shipping_price(
                    comuna_name=comuna_name,
                    region_name=region_name,
                )
            except ShippingSnapshotResolutionError:
                raise serializers.ValidationError({
                    'comuna': 'La comuna y región indicadas no son válidas.'
                })
            if snapshot is None:
                raise serializers.ValidationError({'comuna': 'El envío no está disponible para la comuna indicada.'})
            attrs['comuna_id'] = snapshot.comuna_id
            attrs['_shipping_price'] = snapshot.price
        else:
            attrs.pop('comuna_name', None)
            attrs.pop('region_name', None)
            try:
                snapshot = resolve_shipping_price(comuna_id=attrs['comuna_id'])
            except ShippingSnapshotResolutionError:
                raise serializers.ValidationError({'comuna': 'La comuna indicada no es válida.'})
            if snapshot is None:
                raise serializers.ValidationError({'comuna': 'El envío no está disponible para la comuna indicada.'})
            attrs['_shipping_price'] = snapshot.price

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            checkout_key = normalize_checkout_key(
                self.context['request'].headers.get('Idempotency-Key')
            )
        except InvalidCheckoutKeyError:
            raise serializers.ValidationError({'detail': 'Invalid idempotency key.'})

        if not user or user.is_anonymous:
            guest_items = validated_data.pop('guest_items')
            confirmed_revision = validated_data.pop('confirmed_revision', None)
            comuna_selector = validated_data.pop('_comuna_selector')
            try:
                return create_order(
                    checkout_key=checkout_key,
                    guest_email=validated_data.get('guest_email'),
                    guest_name=validated_data.get('guest_name'),
                    phone=validated_data['phone'],
                    shipping_address=validated_data['shipping_address'],
                    apartment_office=validated_data.get('apartment_office', ''),
                    payment_method=validated_data.get('payment_method', 'webpay'),
                    guest_items=guest_items,
                    confirmed_revision=confirmed_revision,
                    comuna_selector=comuna_selector,
                )
            except GuestQuoteValidationError as error:
                raise serializers.ValidationError({
                    'guest_items': 'Unable to resolve the confirmed quote.'
                }) from error

        comuna_id = validated_data.pop('comuna_id')
        shipping_cost = validated_data.pop('_shipping_price')
        try:
            return create_order(
                user=user,
                checkout_key=checkout_key,
                phone=validated_data['phone'],
                shipping_address=validated_data['shipping_address'],
                apartment_office=validated_data.get('apartment_office', ''),
                payment_method=validated_data.get('payment_method', 'webpay'),
                comuna_id=comuna_id,
                shipping_cost=shipping_cost,
            )
        except EmptyCartError:
            raise serializers.ValidationError({
                "detail": "No puedes crear un pedido con el carrito vacío."
            })
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
