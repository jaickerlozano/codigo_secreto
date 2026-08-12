from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .serializers import ContactMessageSerializer


class ContactMessageView(APIView):
    """Endpoint público para enviar mensajes de contacto."""
    permission_classes = [AllowAny]
    throttle_scope = 'contact_message'

    @extend_schema(summary="Enviar mensaje de contacto", request=ContactMessageSerializer, tags=["Contacto"])
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response({'id': message.id, 'status': message.status}, status=status.HTTP_201_CREATED)
