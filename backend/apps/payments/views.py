from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.db import transaction
from apps.orders.services import GUEST_ACCESS_COOKIE_NAME, authorize_order_access
from .models import Transaction
from .serializers import InitiatePaymentSerializer

CAPABILITY_HEADER = 'X-Order-Capability'


class InitiatePaymentView(APIView):
    """Endpoint para iniciar el proceso de pago de un pedido autorizado."""
    permission_classes = [AllowAny]
    throttle_scope = 'payment_initiate'

    @extend_schema(
        summary="Iniciar proceso de pago",
        description="Recibe el order_id, registra el intento mock y devuelve la URL de pago.",
        tags=["Pagos"],
        request=InitiatePaymentSerializer
    )
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = authorize_order_access(
            order_id=serializer.validated_data['order_id'],
            user=request.user,
            capability=request.headers.get(CAPABILITY_HEADER),
            access_cookie=request.COOKIES.get(GUEST_ACCESS_COOKIE_NAME),
        )
        if order is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if order.status != 'PENDING':
            return Response(
                {'order_id': [f"Este pedido no se puede pagar porque su estado es: {order.get_status_display()}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if order.transactions.filter(status='APPROVED').exists():
            return Response({'order_id': ['Este pedido ya fue pagado.']}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Registramos el intento de pago con el proveedor mock existente.
            token_simulado = f"token_simulado_cl_f_{order.id}x99"
            payment_transaction = Transaction.objects.create(
                order=order,
                amount=order.total,
                status='PENDING',
                gateway_reference=token_simulado,
                payment_method='MÉTODO SIMULADO'
            )
            url_pago_simulada = f"https://api.tu_pasarela.cl/mock-checkout?token={token_simulado}"

        return Response({
            "transaction_id": payment_transaction.id,
            "order_id": order.id,
            "amount": order.total,
            "payment_url": url_pago_simulada,
            "gateway_reference": token_simulado
        }, status=status.HTTP_200_OK)
