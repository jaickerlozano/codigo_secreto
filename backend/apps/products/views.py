from django.db import transaction
from rest_framework import viewsets, serializers, mixins, status, filters
from rest_framework.response import Response
from .serializers import ProductSerializer, SupplierSerializer, CategorySerializer, StockMovementSerializer
from .models import Product, Supplier, Category, StockMovement
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # Quito 'category' de filterset_fields porque ahora haremos un filtro personalizado más potente
    filterset_fields = ['supplier']
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')

        if category_id:
            try:
                # Buscamos la categoría solicitada
                category = Category.objects.get(id=category_id)
                
                # Expresión recursiva de Django: busca la categoría seleccionada
                # Y ADEMÁS busca en cualquier nivel de subcategoría descendiente
                descendants = Category.objects.filter(pk=category_id) | Category.objects.filter(parent=category)
                
                # Para cubrir hasta 3 niveles de profundidad (Padre -> Hijo -> Nieto)
                sub_descendants = Category.objects.filter(parent__in=descendants)
                all_categories = descendants | sub_descendants

                queryset = queryset.filter(category__in=all_categories)
            except Category.DoesNotExist:
                pass
                
        return queryset

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


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Si el frontend consulta `/api/categories/?menu=true`,
        # solo devolvemos las categorías principales (Padres raíces).
        if self.request.query_params.get('menu') == 'true':
            return queryset.filter(parent__isnull=True)
        return queryset
    

# Habilito creación de movimientos de stock. No se puede actualizar o eliminar movimientos.
class StockMovementViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear un movimiento de stock
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

