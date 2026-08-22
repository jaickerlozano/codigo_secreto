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


class SpecialDeliveryAgreementRequiredErrorSerializer(serializers.Serializer):
    """409 response body when a special-dispatch order still awaits its staff
    agreement: typed error code, recovery guidance, the backend-produced
    WhatsApp agreement link, and the client poll interval in seconds."""

    code = serializers.CharField()
    detail = serializers.CharField()
    whatsapp_url = serializers.URLField()
    poll_after_seconds = serializers.IntegerField(min_value=1)


class MockApproveResponseSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    status = serializers.CharField()
    order_status = serializers.CharField()
