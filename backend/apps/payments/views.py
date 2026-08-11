from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from apps.orders.services import GUEST_ACCESS_COOKIE_NAME, authorize_order_access

from .serializers import InitiatePaymentSerializer
from .services import (
    PaymentAlreadyPaidError,
    PaymentIdempotencyConflictError,
    PaymentMethodUnsupportedError,
    PaymentProviderUnavailableError,
    PaymentStateError,
    initiate_payment,
)

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
        serializer = InitiatePaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        order = authorize_order_access(
            order_id=serializer.validated_data['order_id'],
            user=request.user,
            capability=request.headers.get(CAPABILITY_HEADER),
            access_cookie=request.COOKIES.get(GUEST_ACCESS_COOKIE_NAME),
        )
        if order is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            attempt, payment_url = initiate_payment(
                order=order, idempotency_key=serializer.validated_data['idempotency_key'])
        except PaymentProviderUnavailableError:
            return Response({'detail': 'Payment service unavailable.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentIdempotencyConflictError:
            return Response({'code': 'payment_key_conflict',
                             'detail': 'The idempotency key cannot be reused for a different payment.'},
                            status=status.HTTP_409_CONFLICT)
        except PaymentStateError as error:
            return Response(
                {'order_id': [f"Este pedido no se puede pagar porque su estado es: {error.args[0]}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PaymentAlreadyPaidError:
            return Response({'order_id': ['Este pedido ya fue pagado.']},
                            status=status.HTTP_400_BAD_REQUEST)
        except PaymentMethodUnsupportedError:
            return Response({'order_id': ['El método de pago seleccionado no está disponible.']},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "transaction_id": attempt.id,
            "order_id": order.id,
            "amount": attempt.amount,
            "payment_url": payment_url,
            "gateway_reference": attempt.gateway_reference
        }, status=status.HTTP_200_OK)
