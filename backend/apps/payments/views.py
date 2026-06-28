from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.db import transaction
from apps.orders.models import Order
from .models import Transaction
from .serializers import InitiatePaymentSerializer

class InitiatePaymentView(APIView):
    """
    Endpoint para iniciar el proceso de pago de un pedido.
    """
    permission_classes = [AllowAny] # Público para soportar invitados

    @extend_schema(
        summary="Iniciar proceso de pago",
        description="Recibe el order_id, registra el intento de pago en el backend y devuelve la URL de redirección de la pasarela.",
        tags=["Pagos"],
        request=InitiatePaymentSerializer
    )
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']
        order = Order.objects.get(id=order_id)

        with transaction.atomic():
            # 1. Registramos el intento de pago en nuestra base de datos
            # De forma temporal, simulamos una referencia simulada de pasarela
            token_simulado = f"token_simulado_cl_f_{order.id}x99"
            
            payment_transaction = Transaction.objects.create(
                order=order,
                amount=order.total,
                status='PENDING',
                gateway_reference=token_simulado,
                payment_method='MÉTODO SIMULADO'
            )

            # 2. Simulamos la URL a la que el frontend enviará al usuario a pagar
            # Cuando el cliente elija Flow/Webpay, esta URL se reemplazará por la del proveedor real
            url_pago_simulada = f"https://api.tu_pasarela.cl/mock-checkout?token={token_simulado}"

        return Response({
            "transaction_id": payment_transaction.id,
            "order_id": order.id,
            "amount": order.total,
            "payment_url": url_pago_simulada,
            "gateway_reference": token_simulado
        }, status=status.HTTP_200_OK)
