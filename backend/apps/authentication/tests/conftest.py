import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.authentication.tests.factories import UserFactory


@pytest.fixture
def user_factory():
    """Expose UserFactory as a pytest fixture."""
    return UserFactory


@pytest.fixture
def jwt_cookies_client(api_client, user):
    """Return an APIClient with valid access/refresh tokens set as HttpOnly cookies.

    DRF's test client has limited support for cookie attributes, so this fixture
    is intended for the dedicated cookie-setting scenarios. For most view tests,
    prefer ``force_authenticate(user)`` or ``HTTP_AUTHORIZATION``.
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    refresh_token = str(refresh)

    api_client.cookies["access_token"] = access
    api_client.cookies["access_token"]["httponly"] = True
    api_client.cookies["refresh_token"] = refresh_token
    api_client.cookies["refresh_token"]["httponly"] = True

    return api_client


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Reset DRF throttle cache before each test to avoid cross-test leakage."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
