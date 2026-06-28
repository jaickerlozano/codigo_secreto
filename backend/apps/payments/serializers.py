from rest_framework import serializers
from apps.orders.models import Order

class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
            if order.status != 'PENDING':
                raise serializers.ValidationError(f"Este pedido no se puede pagar porque su estado es: {order.get_status_display()}.")
        except Order.DoesNotExist:
            raise serializers.ValidationError("El pedido seleccionado no existe.")
        return value
