from rest_framework import serializers

from .services import InvalidPaymentKeyError, normalize_idempotency_key


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        request = self.context.get("request")
        try:
            attrs["idempotency_key"] = normalize_idempotency_key(
                request.headers.get("Idempotency-Key") if request else None
            )
        except InvalidPaymentKeyError:
            raise serializers.ValidationError({"detail": "Invalid idempotency key."})
        return attrs


class InitiatePaymentResponseSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    amount = serializers.IntegerField()
    payment_url = serializers.CharField()
    gateway_reference = serializers.CharField()


class MockApproveResponseSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    status = serializers.CharField()
    order_status = serializers.CharField()
