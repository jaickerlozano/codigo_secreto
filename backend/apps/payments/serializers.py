from rest_framework import serializers

class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
