from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from core.local_storage import LocalReferenceStorage
from core.local_configuration import local_database
from core.settings_local import local_email_configuration


def test_local_test_profile():
    if settings.SETTINGS_MODULE != "core.settings_local":
        pytest.skip("Explicit local profile only")
    assert settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")
    assert settings.STORAGES["default"]["BACKEND"].endswith("InMemoryStorage")
    assert settings.EMAIL_BACKEND.endswith("locmem.EmailBackend")
    assert settings.EMAIL_HOST == ""
    assert settings.EMAIL_PORT == 1025
    assert settings.EMAIL_HOST_USER == ""
    assert settings.EMAIL_HOST_PASSWORD == ""
    assert settings.EMAIL_USE_TLS is False
    assert settings.DEFAULT_FROM_EMAIL == "local@example.invalid"
    assert settings.PAYMENT_PROVIDER == "mock"
    assert apps.is_installed("cloudinary")
    assert apps.is_installed("cloudinary_storage")
    assert not any(settings.CLOUDINARY_STORAGE.values())


def test_local_runtime_routes_email_only_to_loopback_mailpit():
    assert local_email_configuration(testing=False) == {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "127.0.0.1",
        "EMAIL_PORT": 1025,
        "EMAIL_USE_TLS": False,
        "EMAIL_HOST_USER": "",
        "EMAIL_HOST_PASSWORD": "",
        "DEFAULT_FROM_EMAIL": "local@example.invalid",
    }


def test_compose_mailpit_is_loopback_bound_without_persistent_storage():
    compose_path = Path(__file__).resolve().parents[3] / "compose.yaml"
    mailpit = yaml.safe_load(compose_path.read_text(encoding="utf-8"))["services"]["mailpit"]

    assert mailpit["image"].startswith("axllent/mailpit:v")
    assert mailpit["ports"] == ["127.0.0.1:1025:1025", "127.0.0.1:8025:8025"]
    assert "volumes" not in mailpit
    assert "env_file" not in mailpit


def test_loopback_readonly_database_configuration():
    path = Mock()
    path.read_text.side_effect = [
        "POSTGRES_DB=test\nPOSTGRES_USER=test\nPOSTGRES_PASSWORD='synthetic'\nHOST=remote.invalid\n",
        "POSTGRES_PASSWORD='do-not-expose\n",
    ]
    database = local_database(path)
    assert (database["HOST"], database["PORT"]) == ("127.0.0.1", "5432")
    assert "default_transaction_read_only=on" in database["OPTIONS"]["options"]
    with pytest.raises(ImproperlyConfigured, match="^Invalid local PostgreSQL configuration$"):
        local_database(path)


def test_remote_media_reference_stays_offline():
    assert LocalReferenceStorage().url("products/example.webp") is None


def test_writable_mode_is_explicit_opt_in():
    path = Mock()
    path.read_text.return_value = "POSTGRES_DB=test\nPOSTGRES_USER=test\nPOSTGRES_PASSWORD='synthetic'\n"
    readonly = local_database(path)
    assert "default_transaction_read_only=on" in readonly["OPTIONS"]["options"]
    writable = local_database(path, read_only=False)
    assert "options" not in writable["OPTIONS"]
    assert writable["OPTIONS"]["connect_timeout"] == 5


@pytest.mark.parametrize("operation", ["open", "save", "delete", "exists"])
def test_storage_operations_are_forbidden(operation):
    with pytest.raises(PermissionError):
        getattr(LocalReferenceStorage(), operation)("products/example.webp")
