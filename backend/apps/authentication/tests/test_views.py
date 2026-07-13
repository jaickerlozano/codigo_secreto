import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import User
from apps.authentication.tests.factories import UserFactory
from apps.carts.models import Cart

pytestmark = pytest.mark.django_db


REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
REFRESH_URL = "/api/auth/token/refresh/"
ME_URL = "/api/auth/me/"


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


def test_login_sets_cookies(api_client):
    """Login exitoso setea access_token y refresh_token como cookies HttpOnly."""
    user = UserFactory.create(email="login@example.com")
    user.set_password("SecurePass123!")
    user.save()

    response = api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert response.cookies["access_token"]["httponly"] is True
    assert response.cookies["refresh_token"]["httponly"] is True
    assert response.cookies["access_token"]["samesite"] == "Lax"
    assert response.cookies["access_token"]["path"] == "/"


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


def test_refresh_reads_cookie(jwt_cookies_client):
    """Refresh lee el token desde la cookie HttpOnly cuando el body está vacío."""
    response = jwt_cookies_client.post(REFRESH_URL, {}, format="json")

    assert response.status_code == 200
    assert "access" in response.data
    assert "access_token" in response.cookies
    assert response.cookies["access_token"]["httponly"] is True


def test_refresh_from_body(api_client, user):
    """Refresh acepta el token directamente en el body."""
    refresh = RefreshToken.for_user(user)
    response = api_client.post(
        REFRESH_URL, {"refresh": str(refresh)}, format="json"
    )

    assert response.status_code == 200
    assert "access" in response.data


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
    """POST /api/auth/logout/ elimina las cookies access_token y refresh_token."""
    user = UserFactory.create(email="logout@example.com")
    user.set_password("SecurePass123!")
    user.save()

    api_client.post(
        LOGIN_URL,
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    assert "access_token" in api_client.cookies
    assert "refresh_token" in api_client.cookies

    response = api_client.post(LOGOUT_URL, {}, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "Sesión cerrada correctamente."
    assert response.cookies["access_token"].value == ""
    assert response.cookies["refresh_token"].value == ""


def test_logout_without_session_still_succeeds(api_client):
    """POST /api/auth/logout/ sin sesión activa devuelve 200 y limpia cookies."""
    response = api_client.post(LOGOUT_URL, {}, format="json")

    assert response.status_code == 200
    assert "message" in response.data
