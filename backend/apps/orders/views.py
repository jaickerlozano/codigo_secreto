from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Order
from .serializers import OrderSerializer

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
        if self.action in ('create', 'track'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Los administradores ven todo. Los clientes registrados solo ven lo suyo.
        # Los invitados no tienen historial ejecutable por GET masivo.
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='order_number',
                location=OpenApiParameter.QUERY,
                required=True,
                type=str,
                description='Número de pedido público (ej: CS-XXXXXXX).',
            ),
        ],
        responses={200: OrderSerializer},
    )
    @action(detail=False, methods=['get'], url_path='track')
    def track(self, request):
        """
        Permite a cualquier usuario (incluidos invitados) consultar un pedido
        únicamente por su número de orden público (order_number).
        """
        order_number = request.query_params.get('order_number')
        if not order_number:
            return Response(
                {'detail': 'Debes indicar el número de pedido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Pedido no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(order)
        return Response(serializer.data)
