from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserMeSerializer
from rest_framework.views import APIView

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