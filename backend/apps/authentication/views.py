from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserMeSerializer
from rest_framework.views import APIView

from .authentication import enforce_csrf

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


def _clear_jwt_cookie(response, cookie_name):
    """Helper para eliminar una cookie JWT respetando la configuración del proyecto."""
    response.delete_cookie(
        cookie_name,
        path=settings.SIMPLE_JWT.get("JWT_COOKIE_PATH", "/"),
        samesite=settings.SIMPLE_JWT.get("JWT_COOKIE_SAMESITE", "Lax"),
    )


class CookieCSRFMixin:
    """Enforces CSRF only when the request carries one of the named cookies."""

    csrf_cookie_names = []

    def _enforce_csrf_for_cookie(self, request):
        if any(n in request.COOKIES for n in self.csrf_cookie_names):
            enforce_csrf(request)


@extend_schema(
        summary="Iniciar sesión (Login)",
    description="Recibe el correo electrónico y la contraseña. Establece cookies HttpOnly de acceso y refresco, y devuelve un mensaje sin exponer tokens.",
    tags=["Autenticación"]
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Cookie-first login: no tokens in body, HttpOnly cookies plus CSRF.
    """

    throttle_scope = "login"

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200 and 'access' in response.data:
            access_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_COOKIE', 'access_token')
            refresh_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_REFRESH_COOKIE', 'refresh_token')
            _set_jwt_cookie(response, access_cookie, response.data['access'])
            _set_jwt_cookie(response, refresh_cookie, response.data['refresh'])
            get_token(request)
            response.data = {'message': 'Inicio de sesión exitoso.'}
        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    summary="Refrescar token de acceso",
    description="Lee el token de refresco desde la cookie HttpOnly, requiere CSRF, y renueva la cookie de acceso sin devolver tokens en el body.",
    tags=["Autenticación"]
)
class CustomTokenRefreshView(CookieCSRFMixin, TokenRefreshView):
    """
    Refresh reads the refresh cookie, enforces CSRF, returns no token body.
    """

    throttle_scope = "login"
    csrf_cookie_names = [settings.SIMPLE_JWT.get('JWT_AUTH_REFRESH_COOKIE', 'refresh_token')]

    def post(self, request, *args, **kwargs):
        refresh_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_REFRESH_COOKIE', 'refresh_token')
        if refresh_cookie in request.COOKIES and 'refresh' not in request.data:
            request._full_data = request.data.copy()
            request._full_data['refresh'] = request.COOKIES[refresh_cookie]
        self._enforce_csrf_for_cookie(request)
        return super().post(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200 and 'access' in response.data:
            access_cookie = settings.SIMPLE_JWT.get('JWT_AUTH_COOKIE', 'access_token')
            _set_jwt_cookie(response, access_cookie, response.data['access'])
            response.data = {'message': 'Token de acceso renovado.'}
        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    summary="Semilla de cookie CSRF",
    description="Endpoint público que genera y establece la cookie CSRF para clientes de navegador.",
    tags=["Autenticación"],
    responses={204: None},
)
class GetCSRFTokenView(APIView):
    """Sets the readable CSRF cookie so browser clients can send unsafe requests."""

    permission_classes = [AllowAny]
    throttle_scope = "login"

    def get(self, request):
        get_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    throttle_scope = "register"

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


class LogoutView(CookieCSRFMixin, APIView):
    """
    Endpoint para cerrar sesión; elimina cookies JWT y requiere CSRF si hay cookies.
    """
    permission_classes = [AllowAny]
    throttle_scope = "login"
    csrf_cookie_names = [
        settings.SIMPLE_JWT.get("JWT_AUTH_COOKIE", "access_token"),
        settings.SIMPLE_JWT.get("JWT_AUTH_REFRESH_COOKIE", "refresh_token"),
    ]

    @extend_schema(
        summary="Cerrar sesión (Logout)",
        description="Elimina las cookies HttpOnly del token de acceso y refresco.",
        tags=["Autenticación"],
        request=None,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}}
    )
    def post(self, request):
        self._enforce_csrf_for_cookie(request)
        access_cookie = settings.SIMPLE_JWT.get("JWT_AUTH_COOKIE", "access_token")
        refresh_cookie = settings.SIMPLE_JWT.get("JWT_AUTH_REFRESH_COOKIE", "refresh_token")
        response = Response(
            {"message": "Sesión cerrada correctamente."},
            status=status.HTTP_200_OK,
        )
        _clear_jwt_cookie(response, access_cookie)
        _clear_jwt_cookie(response, refresh_cookie)
        return response
