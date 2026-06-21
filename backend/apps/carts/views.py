from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer
from django.db.models import F


# Create your views here.
class MyCartView(APIView):
    """
    Controlador central para que el usuario autenticado gestione su carrito de compras.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Ver mi carrito de compras",
        description="Devuelve el carrito del usuario conectado con su lista de productos, subtotales y el monto total final.",
        tags=["Carrito"],
        responses={200: CartSerializer}
    )
    def get(self, request):
        # request.user.cart obtiene el carro único del usuario gracias a la señal
        serializer = CartSerializer(request.user.cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Añadir o actualizar producto en el carrito",
        description="Recibe un product_id y la cantidad. Si el producto ya está en el carro, suma la cantidad; si no, lo añade.",
        tags=["Carrito"],
        request=AddToCartSerializer,
        responses={201: CartSerializer}
    )
    def post(self, request):
        # 1. Validamos los datos de entrada con el serializador auxiliar
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        cart = request.user.cart

        # 2. APLICAMOS TU LÓGICA: Buscamos si el producto ya existe en ESTE carro
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={'quantity': quantity}
        )

        if not created:
            # CORRECCIÓN EXTRA SEGURA: Actualizamos directo en la BD con filter y update
            # Esto se salta cualquier bloqueo del método save() y fuerza la suma inmediata
            CartItem.objects.filter(id=cart_item.id).update(
                quantity=F('quantity') + quantity
            )

        # 🔥 CORRECCIÓN CRUCIAL: Obligamos al objeto 'cart' a borrar su caché en memoria
        # y traer los datos frescos y sumados desde la base de datos SQL.
        cart.refresh_from_db()
        # Devolvemos el carrito actualizado
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
