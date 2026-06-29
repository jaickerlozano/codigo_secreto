from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Autenticación JWT que lee el token de acceso desde una cookie HttpOnly.

    Si la petición trae el header ``Authorization`` se comporta exactamente
    igual que ``JWTAuthentication`` (compatibilidad con clientes que aún
    envíen el Bearer token). Si no hay header, intenta leer la cookie
    configurada en ``SIMPLE_JWT['JWT_AUTH_COOKIE']``.
    """

    def authenticate(self, request):
        access_cookie_name = settings.SIMPLE_JWT.get('JWT_AUTH_COOKIE', 'access_token')

        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        elif access_cookie_name in request.COOKIES:
            raw_token = request.COOKIES.get(access_cookie_name)
        else:
            return None

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
