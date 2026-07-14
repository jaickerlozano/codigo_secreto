from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
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
        Permite que CUALQUIERA (incluidos invitados) pueda hacer un POST para comprar.
        Permite que CUALQUIERA pueda consultar una orden por order_number (tracking público).
        Pero exige estar Autenticado para ver la lista de pedidos del historial.
        """
        if self.action in ['create', 'by_order_number']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Los administradores ven todo. Los clientes registrados solo ven lo suyo.
        # Los invitados no tienen historial ejecutable por GET masivo.
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='by-order-number/(?P<order_number>[^/.]+)')
    def by_order_number(self, request, order_number=None):
        """
        Endpoint público para consultar una orden por order_number.
        Permite que guests y usuarios autenticados consulten el estado de su orden.
        """
        try:
            order = Order.objects.get(order_number=order_number)
            
            # Si el usuario está autenticado, verificar que la orden le pertenezca
            if request.user.is_authenticated and order.user and order.user != request.user:
                return Response(
                    {'detail': 'No tienes permiso para ver esta orden.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Si el usuario no está autenticado y la orden tiene user, requerir autenticación
            if not request.user.is_authenticated and order.user:
                return Response(
                    {'detail': 'Esta orden requiere autenticación para ser consultada.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            serializer = self.get_serializer(order)
            return Response(serializer.data)
            
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Orden no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
