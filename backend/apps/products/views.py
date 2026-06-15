from django.db import transaction
from rest_framework import viewsets, serializers, mixins, status
from rest_framework.response import Response
from .serializers import ProductSerializer, SupplierSerializer, CategorySerializer, StockMovementSerializer
from .models import Product, Supplier, Category, StockMovement
from django.db.models import F

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

    # def update(self, request, *args, **kwargs):
    #     """
    #     Actualizar un producto y registrar un movimiento de stock si se cambia el current_stock
    #     """
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     old_stock = instance.current_stock
    #     new_stock = request.data.get('current_stock', old_stock)

    #     # 1. Instanciamos y validamos primero. El serializer convierte todo a tipos correctos.
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)

    #     with transaction.atomic():
    #         # 2. Guardamos los cambios en la base de datos
    #         product = serializer.save()

    #         # 3. Obtenemos el nuevo stock directamente del objeto ya guardado (garantiza que es un entero)
    #         product = Product.objects.select_for_update().get(id=product.id)  # Bloqueamos la fila para evitar condiciones de carrera
    #         new_stock = product.current_stock

    #         # 4. Si el stock cambió, registramos el movimiento con datos limpios
    #         if new_stock != old_stock:
    #             movement_type = 'IN' if new_stock > old_stock else 'OUT'
    #             StockMovement.objects.create(
    #                 product=product,
    #                 type=movement_type,
    #                 quantity=abs(new_stock - old_stock)
    #             )

    #     return Response(serializer.data, status=status.HTTP_200_OK)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

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
