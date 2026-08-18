from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Region, Comuna
from .serializers import (
    RegionSerializer,
    ComunaSerializer,
    DispatchOptionsSerializer,
)
from .services import (
    SHIPPING_AUTHORITY_COMUNA,
    ShippingSnapshotResolutionError,
    future_dispatch_dates,
    resolve_regional_shipping_option,
    resolve_shipping_price,
)

@extend_schema(
    summary="Listar regiones de Chile con sus comunas",
    description="Devuelve el listado completo de las 16 regiones oficiales ordenadas de Norte a Sur, incluyendo sus comunas activas de forma anidada.",
    tags=["Despachos"]
)
class RegionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Controlador de solo lectura para obtener las regiones de Chile.
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny] # Público para el cálculo de envíos


@extend_schema(
    summary="Listar todas las comunas de Chile sueltas",
    description="Devuelve el listado plano de todas las comunas de Chile. Permite ver sus costos de despacho individuales.",
    tags=["Despachos"]
)
class ComunaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Controlador de solo lectura para obtener las comunas de Chile de forma plana.
    """
    queryset = Comuna.objects.filter(is_active=True)
    serializer_class = ComunaSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['region']


@extend_schema(
    summary="Opciones de despacho para una comuna",
    description="Devuelve las opciones de despacho autoritativas para la comuna indicada: para Santiago, las próximas cuatro fechas de martes/jueves (excluyendo hoy); fuera de Santiago, la única opción regional configurada (transportista, tarifa y plazos). Si el destino o la configuración no están disponibles, falla cerrado con un error tipificado.",
    tags=["Despachos"],
    parameters=[OpenApiParameter(
        name="comuna", location=OpenApiParameter.QUERY, required=True,
        type=OpenApiTypes.INT,
        description="ID de la comuna de destino para calcular las opciones de despacho.",
    )],
    responses={200: DispatchOptionsSerializer}
)
class DispatchOptionsView(APIView):
    """
    Controlador de solo lectura de opciones de despacho (público, como regiones/comunas).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        comuna_param = request.query_params.get("comuna")
        if comuna_param is None:
            return Response(
                {"code": "comuna_required", "detail": "El parámetro comuna es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            comuna_id = int(comuna_param)
        except ValueError:
            return Response(
                {"code": "comuna_invalid", "detail": "El parámetro comuna debe ser un número entero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            comuna = Comuna.objects.select_related("region").only(
                "id", "is_active", "region__name"
            ).get(id=comuna_id)
        except Comuna.DoesNotExist:
            return self._unavailable()

        if not comuna.is_active:
            return self._unavailable()

        try:
            price = resolve_shipping_price(comuna_id=comuna_id)
        except ShippingSnapshotResolutionError:
            # Ambiguous (duplicate) regional configuration: masked, typed, no leaks.
            return Response(
                {"code": "delivery_configuration_invalid",
                 "detail": "El envío no está disponible para la comuna indicada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if price is None:
            return self._unavailable()

        if price.authority == SHIPPING_AUTHORITY_COMUNA:
            return Response(DispatchOptionsSerializer({
                "comuna_id": comuna_id,
                "mode": "santiago",
                "dates": future_dispatch_dates(),
                "shipping_option": None,
            }).data)

        regional = resolve_regional_shipping_option()
        if regional is None:
            return self._unavailable()
        return Response(DispatchOptionsSerializer({
            "comuna_id": comuna_id,
            "mode": "regional",
            "dates": None,
            "shipping_option": {
                "shipping_option_id": regional.id,
                "key": regional.key,
                "carrier": regional.carrier,
                "tariff": regional.tariff,
                "min_lead_days": regional.min_lead_days,
                "max_lead_days": regional.max_lead_days,
            },
        }).data)

    @staticmethod
    def _unavailable():
        """Typed fail-closed response for an unavailable destination or configuration."""
        return Response(
            {"code": "delivery_unavailable",
             "detail": "El envío no está disponible para la comuna indicada."},
            status=status.HTTP_404_NOT_FOUND,
        )
