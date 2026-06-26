from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer

# Habilitamos solo lectura (List/Retrieve) y creación (Create). No se permiten ediciones ni eliminaciones históricas.
class OrderViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated] # 🛡️ Solo clientes logueados pueden comprar

    def get_queryset(self):
        # Medida de seguridad: Si es superusuario, puede ver todas las órdenes de la tienda.
        # Si es un cliente común, SOLO puede ver su propio historial de pedidos.
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
