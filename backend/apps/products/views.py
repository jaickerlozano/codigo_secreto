from django.db import transaction
from rest_framework import viewsets, serializers
from rest_framework.response import Response 
from .serializers import ProductSerializer, SupplierSerializer, CategorySerializer, StockMovementSerializer
from .models import Product, Supplier, Category, StockMovement

# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear un producto y registrar un movimiento de stock inicial si se proporciona current_stock
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Guardamos el producto. Al ser válido, 'current_stock' ya es un entero seguro.
            product = serializer.save()
            
            # Registramos el movimiento de stock IN solo si es mayor que cero
            if product.current_stock > 0:
                StockMovement.objects.create(
                    product=product,
                    type='IN',
                    quantity=product.current_stock
                )
                
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Actualizar un producto y registrar un movimiento de stock si se cambia el current_stock
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_stock = instance.current_stock
        new_stock = request.data.get('current_stock', old_stock)

        # 1. Instanciamos y validamos primero. El serializer convierte todo a tipos correctos.
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # 2. Guardamos los cambios en la base de datos
            product = serializer.save()

            # 3. Obtenemos el nuevo stock directamente del objeto ya guardado (garantiza que es un entero)
            new_stock = product.current_stock

            # 4. Si el stock cambió, registramos el movimiento con datos limpios
            if new_stock != old_stock:
                movement_type = 'IN' if new_stock > old_stock else 'OUT'
                StockMovement.objects.create(
                    product=product,
                    type=movement_type,
                    quantity=abs(new_stock - old_stock)
                )

        return Response(serializer.data)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer