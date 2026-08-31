import json

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import User
from apps.authentication.tests.factories import UserFactory
from apps.carts.models import Cart
from core.tests.test_security_settings import run_production_script

pytestmark = pytest.mark.django_db


REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
REFRESH_URL = "/api/auth/token/refresh/"
ME_URL = "/api/auth/me/"
PROFILE_PHONE_URL = "/api/auth/me/phone/"

PRODUCTION_AUTH_COOKIE_SNAPSHOT = """
import json
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from django.conf import settings
from django.test import Client
from rest_framework.response import Response

from apps.authentication.views import _set_jwt_cookie

response = Response()
_set_jwt_cookie(response, "access_token", "test-token")
jwt_cookie = response.cookies["access_token"]

csrf_response = Client().get(
    "/api/auth/csrf/",
    HTTP_HOST="api.example.test",
    HTTP_X_FORWARDED_PROTO="https",
)
assert csrf_response.status_code == 204
csrf_cookie = csrf_response.cookies["csrftoken"]

print(json.dumps({
    "jwt": {
        "httponly": bool(jwt_cookie["httponly"]),
        "secure": bool(jwt_cookie["secure"]),
        "samesite": jwt_cookie["samesite"],
        "host_only": not bool(jwt_cookie["domain"]),
    },
    "csrf": {
        "httponly": bool(csrf_cookie["httponly"]),
        "secure": bool(csrf_cookie["secure"]),
        "samesite": csrf_cookie["samesite"],
        "domain": csrf_cookie["domain"],
    },
    "session": {
        "httponly": settings.SESSION_COOKIE_HTTPONLY,
        "secure": settings.SESSION_COOKIE_SECURE,
        "samesite": settings.SESSION_COOKIE_SAMESITE,
        "host_only": settings.SESSION_COOKIE_DOMAIN is None,
    },
}))
"""


def test_register_endpoint_success(api_client):
    """POST /api/auth/register/ crea usuario, perfil y carrito con 201."""
    data = {
        "first_name": "María",
        "last_name": "González",
        "email": "newuser@example.com",
        "rut": "12.345.678-9",
        "phone": "+56912345678",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    }
    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 201
    assert User.objects.filter(email="newuser@example.com").exists()
    user = User.objects.get(email="newuser@example.com")
    assert hasattr(user, "profile")
    assert Cart.objects.filter(user=user).exists()
    assert "password" not in response.data
    assert "password_confirm" not in response.data


def test_register_endpoint_password_mismatch(api_client):
    """POST /api/auth/register/ con contraseñas distintas devuelve 400."""
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "mismatch@example.com",
        "password": "SecurePass123!",
        "password_confirm": "DifferentPass123!",
    }
    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 400
    assert "password_confirm" in response.data
    assert not User.objects.filter(email="mismatch@example.com").exists()


def test_register_endpoint_duplicate_email(api_client):
    """POST /api/auth/register/ con email duplicado devuelve 400."""
    existing = UserFactory.create(email="dup@example.com")
    data = {
        "first_name": "Another",
        "last_name": "User",
        "email": existing.email,
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    }
    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 400
    assert "email" in response.data


def test_register_endpoint_invalid_data(api_client):
    """POST /api/auth/register/ sin campos requeridos devuelve 400."""
    response = api_client.post(REGISTER_URL, {}, format="json")

    assert response.status_code == 400
    assert "email" in response.data
    assert "password" in response.data


def test_login_sets_cookies_and_no_tokens_in_body(api_client):
    """Login sets HttpOnly cookies and returns user info, never tokens in body."""
    user = UserFactory.create(email="login@example.com")
    user.set_password("SecurePass123!")
    user.save()

    response = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" not in response.data
    assert "refresh" not in response.data
    assert "message" in response.data
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert "csrftoken" in response.cookies
    assert response.cookies["access_token"]["httponly"] is True
    assert response.cookies["refresh_token"]["httponly"] is True
    assert not bool(response.cookies["access_token"]["secure"])
    assert response.cookies["access_token"]["samesite"] == "Lax"
    assert not bool(response.cookies["access_token"]["domain"])
    assert response.cookies["access_token"]["path"] == "/"


def test_production_auth_cookie_boundary_is_secure_and_host_only():
    result = run_production_script(PRODUCTION_AUTH_COOKIE_SNAPSHOT)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "jwt": {
            "httponly": True,
            "secure": True,
            "samesite": "Lax",
            "host_only": True,
        },
        "csrf": {
            "httponly": False,
            "secure": True,
            "samesite": "Lax",
            "domain": ".example.test",
        },
        "session": {
            "httponly": True,
            "secure": True,
            "samesite": "Lax",
            "host_only": True,
        },
    }


def test_login_wrong_password(api_client):
    """Login con contraseña incorrecta devuelve 401."""
    user = UserFactory.create(email="wrongpass@example.com")
    user.set_password("SecurePass123!")
    user.save()

    response = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "WrongPass123!"},
        format="json",
    )

    assert response.status_code == 401


def test_login_nonexistent_email(api_client):
    """Login con email inexistente devuelve 401."""
    response = api_client.post(
        LOGIN_URL,
        {"email": "ghost@example.com", "password": "SecurePass123!"},
        format="json",
    )

    assert response.status_code == 401


def test_refresh_reads_cookie_and_no_token_in_body(jwt_cookies_client):
    """Refresh reads HttpOnly cookie and returns no access token in body."""
    response = jwt_cookies_client.post(REFRESH_URL, {}, format="json")

    assert response.status_code == 200
    assert "access" not in response.data
    assert "access_token" in response.cookies
    assert response.cookies["access_token"]["httponly"] is True


def test_refresh_from_body_no_token_in_body(api_client, user):
    """Refresh accepts token in body but still returns no token in body."""
    refresh = RefreshToken.for_user(user)
    response = api_client.post(
        REFRESH_URL, {"refresh": str(refresh)}, format="json"
    )

    assert response.status_code == 200
    assert "access" not in response.data


def test_refresh_invalid_token(api_client):
    """Refresh con token inválido o expirado devuelve 401."""
    response = api_client.post(
        REFRESH_URL, {"refresh": "invalid-token"}, format="json"
    )

    assert response.status_code == 401


def test_me_authenticated(authenticated_client, user):
    """GET /api/auth/me/ con JWT válido devuelve el perfil del usuario."""
    response = authenticated_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["id"] == user.id
    assert response.data["email"] == user.email
    assert response.data["first_name"] == user.first_name
    assert response.data["last_name"] == user.last_name
    assert response.data["is_admin"] is False


def test_me_unauthenticated(api_client):
    """GET /api/auth/me/ sin autenticación devuelve 401."""
    response = api_client.get(ME_URL)

    assert response.status_code == 401


def test_me_admin(staff_client, staff_user):
    """GET /api/auth/me/ para staff devuelve is_admin=True."""
    response = staff_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["is_admin"] is True
    assert response.data["email"] == staff_user.email


def test_update_profile_phone_normalizes_and_returns_current_user(authenticated_client, user):
    response = authenticated_client.patch(
        PROFILE_PHONE_URL, {"phone": "912345678"}, format="json"
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.phone == "+56 9 1234 5678"
    assert response.data["phone"] == user.phone


def test_update_profile_phone_rejects_invalid_phone(authenticated_client, user):
    response = authenticated_client.patch(
        PROFILE_PHONE_URL, {"phone": "812345678"}, format="json"
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.phone != "812345678"


def test_update_profile_phone_requires_authentication(api_client):
    response = api_client.patch(PROFILE_PHONE_URL, {"phone": "912345678"}, format="json")

    assert response.status_code == 401


def test_update_profile_phone_cookie_auth_requires_csrf(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.cookies["access_token"] = str(refresh.access_token)
    api_client.handler.enforce_csrf_checks = True

    response = api_client.patch(
        PROFILE_PHONE_URL, {"phone": "912345678"}, format="json"
    )

    assert response.status_code == 403


def test_auth_with_cookie(api_client, user):
    """CookieJWTAuthentication autentica mediante cookie access_token."""
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    api_client.cookies["access_token"] = access

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["email"] == user.email


def test_auth_with_header(api_client, user):
    """CookieJWTAuthentication sigue aceptando el header Authorization Bearer."""
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = api_client.get(ME_URL)

    assert response.status_code == 200
    assert response.data["email"] == user.email


def test_auth_without_both(api_client):
    """Sin cookie ni header, la autenticación falla con 401."""
    response = api_client.get(ME_URL)

    assert response.status_code == 401


def test_auth_with_empty_header(api_client):
    """Un header Authorization vacío no autentica y devuelve 401."""
    api_client.credentials(HTTP_AUTHORIZATION="")

    response = api_client.get(ME_URL)

    assert response.status_code == 401


def test_logout_clears_cookies(api_client):
    """POST /api/auth/logout/ requires CSRF when cookies exist and clears them."""
    user = UserFactory.create(email="logout@example.com")
    user.set_password("SecurePass123!")
    user.save()

    login_response = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    assert "access_token" in api_client.cookies
    assert "refresh_token" in api_client.cookies
    assert "csrftoken" in login_response.cookies

    csrf_token = api_client.cookies["csrftoken"].value
    api_client.handler.enforce_csrf_checks = True
    response = api_client.post(
        LOGOUT_URL,
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 200
    assert response.data["message"] == "Sesión cerrada correctamente."
    assert response.cookies["access_token"].value == ""
    assert response.cookies["refresh_token"].value == ""


def test_logout_without_session_still_succeeds(api_client):
    """POST /api/auth/logout/ sin sesión activa devuelve 200 y limpia cookies."""
    response = api_client.post(LOGOUT_URL, {}, format="json")

    assert response.status_code == 200
    assert "message" in response.data


CSRF_URL = "/api/auth/csrf/"
ECHO_UNSAFE_URL = "/api/test/echo-unsafe/"


def _make_user(email, password="SecurePass123!"):
    user = UserFactory.create(email=email)
    user.set_password(password)
    user.save()
    return user


def test_csrf_endpoint_sets_cookie(api_client):
    """GET /api/auth/csrf/ sets a readable CSRF cookie."""
    response = api_client.get(CSRF_URL)
    assert response.status_code == 204
    assert "csrftoken" in response.cookies
    assert response.cookies["csrftoken"].value


@pytest.mark.urls("apps.authentication.tests.urls")
def test_cookie_auth_unsafe_without_csrf_rejected(api_client, user):
    """Cookie-authenticated POST without CSRF token is rejected."""
    refresh = RefreshToken.for_user(user)
    api_client.cookies["access_token"] = str(refresh.access_token)
    api_client.handler.enforce_csrf_checks = True
    response = api_client.post(ECHO_UNSAFE_URL, {}, format="json")
    assert response.status_code == 403


@pytest.mark.urls("apps.authentication.tests.urls")
def test_cookie_auth_unsafe_with_csrf_accepted(api_client, user):
    """Cookie-authenticated POST with matching CSRF token succeeds."""
    csrf_token = get_random_string(32)
    refresh = RefreshToken.for_user(user)
    api_client.cookies["access_token"] = str(refresh.access_token)
    api_client.cookies["csrftoken"] = csrf_token
    api_client.handler.enforce_csrf_checks = True
    response = api_client.post(
        ECHO_UNSAFE_URL,
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert response.data["ok"] is True


@pytest.mark.urls("apps.authentication.tests.urls")
@override_settings(CSRF_TRUSTED_ORIGINS=["https://app.example.test"])
def test_cookie_authenticated_mutation_rejects_untrusted_origin(api_client, user):
    """A valid CSRF token cannot authorize a cookie mutation from an untrusted origin."""
    csrf_token = get_random_string(32)
    refresh = RefreshToken.for_user(user)
    api_client.cookies["access_token"] = str(refresh.access_token)
    api_client.cookies["csrftoken"] = csrf_token
    api_client.handler.enforce_csrf_checks = True

    response = api_client.post(
        ECHO_UNSAFE_URL,
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_ORIGIN="https://untrusted.example.test",
    )

    assert response.status_code == 403


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    SECURE_SSL_REDIRECT=True,
)
def test_request_boundary_rejects_untrusted_host_and_non_https_forwarding(api_client):
    """Only an allowlisted host with the expected proxy HTTPS signal reaches the view."""
    trusted = api_client.get(
        CSRF_URL,
        HTTP_HOST="testserver",
        HTTP_X_FORWARDED_PROTO="https",
    )
    untrusted_host = api_client.get(
        CSRF_URL,
        HTTP_HOST="untrusted.example.test",
        HTTP_X_FORWARDED_PROTO="https",
    )
    non_https_forwarding = api_client.get(
        CSRF_URL,
        HTTP_HOST="testserver",
        HTTP_X_FORWARDED_PROTO="http",
    )

    assert trusted.status_code == 204
    assert untrusted_host.status_code == 400
    assert non_https_forwarding.status_code == 301


@pytest.mark.urls("apps.authentication.tests.urls")
def test_bearer_auth_unsafe_without_csrf_accepted(api_client, user):
    """Bearer-authenticated POST is exempt from cookie CSRF checks."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    api_client.handler.enforce_csrf_checks = True
    response = api_client.post(ECHO_UNSAFE_URL, {}, format="json")
    assert response.status_code == 200
    assert response.data["ok"] is True


def test_refresh_cookie_requires_csrf(jwt_cookies_client):
    """Refresh using the refresh cookie requires a valid CSRF token."""
    jwt_cookies_client.handler.enforce_csrf_checks = True
    response = jwt_cookies_client.post(REFRESH_URL, {}, format="json")
    assert response.status_code == 403


def test_refresh_cookie_with_csrf_succeeds(jwt_cookies_client):
    """Refresh with matching CSRF token returns no token body and sets access cookie."""
    csrf_token = get_random_string(32)
    jwt_cookies_client.cookies["csrftoken"] = csrf_token
    jwt_cookies_client.handler.enforce_csrf_checks = True
    response = jwt_cookies_client.post(
        REFRESH_URL,
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    assert "access" not in response.data
    assert "access_token" in response.cookies


def test_logout_without_csrf_rejected(api_client):
    """Logout with auth cookies but no CSRF token is rejected."""
    user = _make_user("logout-csrf@example.com")
    api_client.handler.enforce_csrf_checks = True
    api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    response = api_client.post(LOGOUT_URL, {}, format="json")
    assert response.status_code == 403


def test_throttle_login_rate_limit(api_client):
    """More than 5 login requests per minute from the same client are throttled."""
    user = _make_user("throttle-login@example.com")
    for _ in range(5):
        response = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": "SecurePass123!"},
            format="json",
        )
        assert response.status_code == 200
    response = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    assert response.status_code == 429


def test_throttle_register_rate_limit(api_client):
    """More than 3 register requests per hour from the same client are throttled."""
    for i in range(3):
        data = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"throttle-register{i}@example.com",
            "rut": f"12.345.{i:03d}-9",
            "phone": f"+5691234567{i}",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post(REGISTER_URL, data, format="json")
        assert response.status_code == 201
    response = api_client.post(
        REGISTER_URL,
        {
            "first_name": "Test",
            "last_name": "User",
            "email": "throttle-register3@example.com",
            "rut": "12.345.003-9",
            "phone": "+56912345673",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        },
        format="json",
    )
    assert response.status_code == 429


def test_throttle_reset_allows_request(api_client):
    """Clearing the throttle cache permits a new request after rate limiting."""
    from django.core.cache import cache

    user = _make_user("throttle-reset@example.com")
    for _ in range(5):
        api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": "SecurePass123!"},
            format="json",
        )
    throttled = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    assert throttled.status_code == 429

    cache.clear()

    response = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    assert response.status_code == 200
