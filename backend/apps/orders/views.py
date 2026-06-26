from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
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
        Pero exige estar Autenticado para ver la lista de pedidos del historial.
        """
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Los administradores ven todo. Los clientes registrados solo ven lo suyo.
        # Los invitados no tienen historial ejecutable por GET masivo.
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
