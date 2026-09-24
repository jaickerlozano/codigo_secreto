import pytest
import os
import socket
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.authentication.tests.factories import UserFactory


if __import__("os").environ.get("MANAGED_POSTGRESQL_RUNTIME") == "1":
    pytest_plugins = ["core.managed_postgresql_runtime.pytest_plugin"]


@pytest.fixture(autouse=True)
def offline_local_tests(monkeypatch):
    if os.environ.get("LOCAL_TEST_DATABASE") == "1":
        def deny_network(*args, **kwargs):
            raise AssertionError("Network access is forbidden in isolated local tests")
        monkeypatch.setattr(socket.socket, "connect", deny_network)
        monkeypatch.setattr(socket.socket, "connect_ex", deny_network)


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
    if "postgresql" not in engine and __import__("os").environ.get("MANAGED_POSTGRESQL_RUNTIME") != "1":
        skip = pytest.mark.skip(reason="pg_only: PostgreSQL required")
        for item in items:
            if "pg_only" in item.keywords:
                item.add_marker(skip)
