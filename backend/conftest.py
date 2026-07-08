import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.authentication.tests.factories import UserFactory


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def user(db) -> User:
    """Standard active user created via UserFactory.

    Depends on the ``db`` fixture because factory-boy writes to the database.
    """
    return UserFactory.create()


@pytest.fixture
def staff_user(db) -> User:
    """Staff user created via UserFactory."""
    return UserFactory.create(is_staff=True, is_superuser=True)


@pytest.fixture
def authenticated_client(api_client, user) -> APIClient:
    """APIClient authenticated with the ``user`` fixture."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def staff_client(api_client, staff_user) -> APIClient:
    """APIClient authenticated with the ``staff_user`` fixture."""
    api_client.force_authenticate(user=staff_user)
    return api_client


def pytest_collection_modifyitems(config, items):
    """Auto-skip ``pg_only`` tests when the test database is not PostgreSQL."""
    from django.conf import settings

    engine = settings.DATABASES["default"].get("ENGINE", "")
    if "postgresql" not in engine:
        skip = pytest.mark.skip(reason="pg_only: PostgreSQL required")
        for item in items:
            if "pg_only" in item.keywords:
                item.add_marker(skip)
