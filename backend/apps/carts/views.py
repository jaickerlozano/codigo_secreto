from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer
from django.db.models import F


# Create your views here.
class MyCartView(APIView):
    """
    Controlador central para que el usuario autenticado gestione su carrito de compras.
    """
    permission_classes = [IsAuthenticated]

    def _get_cart(self, user):
        """Trae el carro del usuario precargando los ítems y productos."""
        return Cart.objects.prefetch_related('items__product').get(user=user)

    @extend_schema(
        summary="Ver mi carrito de compras",
        description="Devuelve el carrito del usuario con subtotales, envío y total; con ?comuna={id} el envío usa la autoridad de precios del backend.",
        tags=["Carrito"],
        parameters=[OpenApiParameter(
            name="comuna", location=OpenApiParameter.QUERY, required=False,
            type=OpenApiTypes.INT,
            description="ID de la comuna de entrega para el estimado de envío autoritativo.",
        )],
        responses={200: CartSerializer}
    )
    def get(self, request):
        # Obtenemos el carro con prefetch_related para evitar consultas N+1
        cart = self._get_cart(request.user)
        comuna_selector = request.query_params.get("comuna")
        if comuna_selector is not None:
            try:
                comuna_selector = int(comuna_selector)
            except ValueError:
                return Response(
                    {"comuna": ["El parámetro comuna debe ser un número entero."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        serializer = CartSerializer(cart, context={"comuna_selector": comuna_selector})
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

        # 3. Traemos el carro fresco con prefetch_related para serializar los totales
        cart = self._get_cart(request.user)
        # Devolvemos el carrito actualizado
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Remover o disminuir producto del carrito",
        description="Recibe un product_id y la cantidad a quitar. Si la cantidad del carro llega a cero o menos, el ítem se elimina por completo.",
        tags=["Carrito"],
        parameters=[
            OpenApiParameter(
                name="product_id",
                location=OpenApiParameter.QUERY,
                required=True,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="quantity",
                location=OpenApiParameter.QUERY,
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={200: CartSerializer}
    )
    def delete(self, request):
        # 1. Validamos los datos de entrada (product_id y quantity a restar)
        serializer = AddToCartSerializer(
            data=request.query_params if request.query_params else request.data
        )
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity_to_subtract = serializer.validated_data['quantity']
        cart = request.user.cart

        try:
            # 2. Buscamos si el producto realmente existe en el carro del usuario
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)

            if cart_item.quantity <= quantity_to_subtract:
                # Si lo que quiere restar es mayor o igual a lo que tiene, borramos el registro completo
                cart_item.delete()
            else:
                # Si aún quedan unidades tras la resta, disminuimos la cantidad de forma segura
                CartItem.objects.filter(id=cart_item.id).update(
                    quantity=F('quantity') - quantity_to_subtract
                )

            # 3. Traemos el carro fresco con prefetch_related para serializar los totales
            cart = self._get_cart(request.user)
            return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

        except CartItem.DoesNotExist:
            # Si intentan restar un producto que no está en el carro, respondemos con un error limpio
            return Response(
                {"detail": "El producto seleccionado no se encuentra en tu carrito de compras."},
                status=status.HTTP_400_BAD_REQUEST
            )
