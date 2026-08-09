from django.conf import settings
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Order
from .serializers import (
    GuestQuoteResponseSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    QuoteErrorSerializer,
    QuoteSerializer,
)
from .services import (
    GUEST_ACCESS_COOKIE_MAX_AGE,
    GUEST_ACCESS_COOKIE_NAME,
    GuestQuoteValidationError,
    authorize_order_access,
    calculate_guest_quote,
    issue_guest_access_cookie,
)


CAPABILITY_HEADER = "X-Order-Capability"


class OrderViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        """
        Permite que CUALQUIERA (incluidos invitados) pueda hacer un POST para comprar
        o consultar el estado de un pedido por su número de orden.
        Pero exige estar Autenticado para ver la lista de pedidos del historial.
        """
        if self.action in ('create', 'by_order_number', 'access', 'quote'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_throttles(self):
        if self.action == 'create':
            self.throttle_scope = 'order_create'
        elif self.action == 'quote':
            self.throttle_scope = 'order_quote'
        elif self.action in ('by_order_number', 'access'):
            self.throttle_scope = 'order_lookup'
        else:
            self.throttle_scope = None
        return super().get_throttles()

    def get_queryset(self):
        # Los administradores ven todo. Los clientes registrados solo ven lo suyo.
        # Los invitados no tienen historial ejecutable por GET masivo.
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    @extend_schema(request=OrderCreateSerializer, responses={201: OrderSerializer})
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        request=QuoteSerializer,
        responses={200: GuestQuoteResponseSerializer, 400: QuoteErrorSerializer, 429: QuoteErrorSerializer},
    )
    @action(detail=False, methods=['post'], url_path='quote')
    def quote(self, request):
        serializer = QuoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code': 'invalid_quote', 'detail': 'Unable to create quote.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quote = calculate_guest_quote(
                serializer.validated_data['items'], serializer.validated_data.get('comuna')
            )
        except GuestQuoteValidationError:
            return Response({'code': 'invalid_quote', 'detail': 'Unable to create quote.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(GuestQuoteResponseSerializer(quote.as_dict()).data)

    @staticmethod
    def _masked_not_found():
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        responses={200: OrderSerializer},
    )
    @action(detail=False, methods=['get'], url_path='by-order-number/(?P<order_number>[^/.]+)')
    def by_order_number(self, request, order_number=None):
        """
        Endpoint seguro para consultar una orden por order_number.
        Requiere propietario, staff o cookie de capacidad válida.
        """
        order = authorize_order_access(
            order_number,
            user=request.user,
            access_cookie=request.COOKIES.get(GUEST_ACCESS_COOKIE_NAME),
        )
        if order is None:
            return self._masked_not_found()

        return Response(self.get_serializer(order).data)

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name=CAPABILITY_HEADER,
                location=OpenApiParameter.HEADER,
                required=True,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={204: None},
    )
    @action(detail=False, methods=['post'], url_path='by-order-number/(?P<order_number>[^/.]+)/access')
    def access(self, request, order_number=None):
        raw_token = request.headers.get(CAPABILITY_HEADER)
        if not raw_token:
            return self._masked_not_found()

        order = authorize_order_access(
            order_number,
            capability=raw_token,
        )
        if order is None:
            return self._masked_not_found()

        cookie_value = issue_guest_access_cookie(order)
        if cookie_value is None:
            return self._masked_not_found()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        simple_jwt = getattr(settings, "SIMPLE_JWT", {})
        response.set_cookie(
            GUEST_ACCESS_COOKIE_NAME, cookie_value, max_age=GUEST_ACCESS_COOKIE_MAX_AGE,
            httponly=True, secure=getattr(settings, "GUEST_ORDER_ACCESS_COOKIE_SECURE", simple_jwt.get("JWT_COOKIE_SECURE", False)),
            samesite=getattr(settings, "GUEST_ORDER_ACCESS_COOKIE_SAMESITE", "Strict"), path="/",
        )
        return response
