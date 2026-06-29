from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserMeSerializer
from rest_framework.views import APIView

# Create your views here.
def _set_jwt_cookie(response, cookie_name, token, **overrides):
    """Helper para escribir una cookie JWT con los defaults de settings."""
    defaults = {
        "httponly": settings.SIMPLE_JWT.get("JWT_AUTH_HTTPONLY", True),
        "secure": settings.SIMPLE_JWT.get("JWT_COOKIE_SECURE", False),
        "samesite": settings.SIMPLE_JWT.get("JWT_COOKIE_SAMESITE", "Lax"),
        "path": settings.SIMPLE_JWT.get("JWT_COOKIE_PATH", "/"),
    }
    defaults.update(overrides)
    response.set_cookie(cookie_name, token, **defaults)


@extend_schema(
        summary="Iniciar sesión (Login)",
    description="Recibe el correo electrónico y la contraseña. Devuelve un token de acceso y un token de refresco.",
    tags=["Autenticación"]
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para el inicio de sesión que genera los tokens JWT.
    """

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200 and 'access' in response.data:
            access_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_COOKIE', 'access_token')
            refresh_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_REFRESH_COOKIE', 'refresh_token')
            _set_jwt_cookie(response, access_cookie, response.data['access'])
            _set_jwt_cookie(response, refresh_cookie, response.data['refresh'])
        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    summary="Refrescar token de acceso",
    description="Recibe un token de refresco válido y entrega un nuevo token de acceso para mantener la sesión activa.",
    tags=["Autenticación"]
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Vista personalizada para renovar el token de acceso del cliente.
    """

    def post(self, request, *args, **kwargs):
        refresh_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_REFRESH_COOKIE', 'refresh_token')
        if refresh_cookie in request.COOKIES and 'refresh' not in request.data:
            request._full_data = request.data.copy()
            request._full_data['refresh'] = request.COOKIES[refresh_cookie]
        return super().post(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200 and 'access' in response.data:
            access_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_COOKIE', 'access_token')
            _set_jwt_cookie(response, access_cookie, response.data['access'])
        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    summary="Registrar un nuevo cliente",
    description="Permite a los usuarios de la tienda crear una cuenta de cliente. Crea el usuario y su perfil de despacho de forma automática.",
    tags=["Autenticación"],
    request=RegisterSerializer
)
class RegisterView(generics.CreateAPIView):
    """
    Vista para el registro público de nuevos clientes en la plataforma.
    """
    permission_classes = [AllowAny] # Permite el acceso a usuarios no logueados
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "message": "Usuario registrado con éxito de forma segura."
        }, status=status.HTTP_201_CREATED)


class UserMeView(APIView):
    """
    Endpoint protegido para obtener la información detallada del usuario autenticado actual.
    """
    permission_classes = [IsAuthenticated] # OBLIGATORIO: Bloquea el acceso a invitados

    @extend_schema(
        summary="Obtener perfil del usuario autenticado",
        description="Lee el token JWT enviado en las cabeceras y devuelve los datos personales del usuario conectado.",
        tags=["Autenticación"],
        responses={200: UserMeSerializer}
    )
    def get(self, request):
        # request.user contiene automáticamente al usuario dueño del token JWT
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)