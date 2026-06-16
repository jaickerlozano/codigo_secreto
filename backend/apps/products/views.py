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


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Si el frontend consulta `/api/categories/?menu=true`,
        # solo devolvemos las categorías principales (Padres raíces).
        if self.request.query_params.get('menu') == 'true':
            return queryset.filter(parent__isnull=True)
        return queryset
    

# Habilito solo lectura, creación y eliminación de movimientos de stock. No se pueden actualizar.
class StockMovementViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer

    def create(self, request, *args, **kwargs):
        """
        Crear un movimiento de stock
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extraigo los datos validados SIN guardarlos aún en la base de datos
        validated_data = serializer.validated_data
        product_instance = validated_data['product']
        movement_type = validated_data['type']
        quantity = validated_data['quantity']

        with transaction.atomic():
            # 1. Bloqueo la fila del producto INMEDIATAMENTE antes de leer su stock actual
            product = Product.objects.select_for_update().get(id=product_instance.id)

            # 2. Ejecuto la validación de negocio con el stock real y fresco de la base de datos
            if movement_type == 'OUT':
                if quantity > product.current_stock:
                    raise serializers.ValidationError({
                        "quantity": f"Stock insuficiente. Stock actual disponible: {product.current_stock}."
                    })
                # Restamos directamente en memoria (es seguro gracias a select_for_update)
                product.current_stock -= quantity
            else:
                # Sumamos directamente en memoria
                product.current_stock += quantity

            # 3. Guardamos primero el movimiento (ahora que sabemos que es válido)
            movement = serializer.save()

            # 4. Guardamos el producto con su nuevo stock modificado
            product.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar un movimiento de stock. Esto no revertirá el cambio en el stock del producto, ya que los movimientos son registros históricos.
        """
        instance = self.get_object()
        product_instance = instance.product
        movement_type = instance.type
        quantity = instance.quantity

        with transaction.atomic():
            # Bloqueamos la fila del producto para evitar condiciones de carrera
            product = Product.objects.select_for_update().get(id=product_instance.id)

            # Revertimos el movimiento en el stock del producto
            if movement_type == 'IN':
                if quantity > product.current_stock:
                    raise serializers.ValidationError({
                        "detail": f"No se puede eliminar este movimiento porque revertiría el stock a un valor negativo. Stock actual: {product.current_stock}."
                    })
                product.current_stock -= quantity
            else:
                product.current_stock += quantity

            # Guardamos el producto con su nuevo stock modificado
            product.save()

            # Finalmente, eliminamos el movimiento
            self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)
