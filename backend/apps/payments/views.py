from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.orders.services import GUEST_ACCESS_COOKIE_NAME, authorize_order_access

from .models import Transaction
from .serializers import (
    InitiatePaymentResponseSerializer,
    InitiatePaymentSerializer,
    MockApproveResponseSerializer,
)
from .services import (
    PaymentAlreadyPaidError,
    PaymentApprovalError,
    PaymentIdempotencyConflictError,
    PaymentMethodUnsupportedError,
    PaymentProviderUnavailableError,
    PaymentStateError,
    SpecialDeliveryAgreementRequiredError,
    approve_payment,
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
        request=InitiatePaymentSerializer,
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                location=OpenApiParameter.HEADER,
                required=False,
                type=OpenApiTypes.STR,
                description="Clave de idempotencia del intento de pago (máx. 64 caracteres).",
            ),
        ],
        responses={200: InitiatePaymentResponseSerializer},
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
        except SpecialDeliveryAgreementRequiredError as error:
            return Response({
                'code': 'special_delivery_agreement_required',
                'detail': error.recovery_guidance,
                'whatsapp_url': error.whatsapp_url,
                'poll_after_seconds': error.poll_after_seconds,
            }, status=status.HTTP_409_CONFLICT)
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


class ApproveMockPaymentView(APIView):
    """Endpoint para aprobar (solo desarrollo) el pago mock de un pedido autorizado."""
    permission_classes = [AllowAny]
    throttle_scope = 'payment_approve'

    @extend_schema(
        summary="Aprobar pago mock (solo desarrollo)",
        description="Aprueba la transacción mock pendiente y marca el pedido como pagado.",
        tags=["Pagos"],
        request=None,
        responses={200: MockApproveResponseSerializer},
    )
    def post(self, request, transaction_id):
        attempt = Transaction.objects.filter(id=transaction_id).first()
        if attempt is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        order = authorize_order_access(
            order_id=attempt.order_id,
            user=request.user,
            capability=request.headers.get(CAPABILITY_HEADER),
            access_cookie=request.COOKIES.get(GUEST_ACCESS_COOKIE_NAME),
        )
        if order is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            attempt, order = approve_payment(order=order, transaction_id=transaction_id)
        except PaymentProviderUnavailableError:
            return Response({'detail': 'Payment service unavailable.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except PaymentStateError as error:
            return Response(
                {'order_id': [f"Este pedido no se puede pagar porque su estado es: {error.args[0]}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PaymentApprovalError:
            return Response({'transaction_id': ['Esta transacción no puede ser aprobada.']},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "transaction_id": attempt.id,
            "order_id": order.id,
            "status": attempt.status,
            "order_status": order.status,
        }, status=status.HTTP_200_OK)
