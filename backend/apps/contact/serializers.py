from rest_framework import serializers

from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'body', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']


class ContactMessageResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
