from django.db import transaction
from rest_framework import viewsets, serializers, mixins, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .serializers import ProductSerializer, SupplierSerializer, CategorySerializer, StockMovementSerializer, FavoriteSerializer, FavoriteMergeSerializer
from .models import Product, Supplier, Category, StockMovement, Favorite
from .services import merge_favorites
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter

# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'supplier').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'id'] # <-- Campos permitidos para ordenar
    ordering = ['-id'] # Orden por defecto (más recientes)

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
                    movement_type='IN',
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


class FavoritesView(APIView):
    """Favoritos privados del cliente autenticado (lectura y merge de invitado)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar favoritos del usuario autenticado",
        responses={200: FavoriteSerializer(many=True)},
        tags=["Favoritos"],
    )
    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user)
        return Response(FavoriteSerializer(favorites, many=True).data)

    @extend_schema(
        summary="Fusionar favoritos de invitado (sin duplicados)",
        request=FavoriteMergeSerializer,
        responses={200: FavoriteSerializer(many=True)},
        tags=["Favoritos"],
    )
    def post(self, request):
        serializer = FavoriteMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merge_favorites(user=request.user, product_ids=serializer.validated_data['product_ids'])
        favorites = Favorite.objects.filter(user=request.user)
        return Response(FavoriteSerializer(favorites, many=True).data)


class FavoriteDeleteView(APIView):
    """Elimina un favorito del cliente autenticado."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Eliminar un favorito por producto",
        responses={204: None},
        tags=["Favoritos"],
    )
    def delete(self, request, product_id):
        deleted_count, _ = Favorite.objects.filter(user=request.user, product_id=product_id).delete()
        if not deleted_count:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)