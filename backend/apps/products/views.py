from django.db import transaction
from rest_framework import viewsets
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
        initial_stock = int(request.data.get('current_stock', 0))

        if initial_stock and int(initial_stock) < 0:
            raise serializers.ValidationError({
                "current_stock": "El stock inicial no puede ser menor que cero."
            })
        
        # Creamos el producto usando el serializer normal
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            product = serializer.save()  # Guardamos el producto para obtener su ID

            # Si se proporcionó un stock inicial mayor a 0, registramos un movimiento de stock IN
            if initial_stock and int(initial_stock) > 0:
                StockMovement.objects.create(
                    product=product,
                    type='IN',
                    quantity=int(initial_stock)
                )

        return Response(serializer.data, status=201)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer