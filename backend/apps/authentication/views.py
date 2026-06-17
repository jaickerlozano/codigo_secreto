from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema

# Create your views here.
@extend_schema(
        summary="Iniciar sesión (Login)",
    description="Recibe el correo electrónico y la contraseña. Devuelve un token de acceso y un token de refresco.",
    tags=["Autenticación"]
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para el inicio de sesión que genera los tokens JWT.
    """
    pass


@extend_schema(
    summary="Refrescar token de acceso",
    description="Recibe un token de refresco válido y entrega un nuevo token de acceso para mantener la sesión activa.",
    tags=["Autenticación"]
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Vista personalizada para renovar el token de acceso del cliente.
    """
    pass