from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication from Authorization header or HttpOnly cookie; cookie writes require CSRF."""

    def enforce_csrf(self, request):
        """Replicate DRF SessionAuthentication CSRF enforcement."""
        check = CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        access_cookie_name = settings.SIMPLE_JWT.get("JWT_AUTH_COOKIE", "access_token")
        if access_cookie_name not in request.COOKIES:
            return None

        raw_token = request.COOKIES.get(access_cookie_name)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            self.enforce_csrf(request)
        return user, validated_token


def enforce_csrf(request):
    """Standalone CSRF enforcement helper for cookie-backed views."""
    check = CSRFCheck(lambda req: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")
