from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from .models import Region, Comuna
from .serializers import RegionSerializer, ComunaSerializer

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
