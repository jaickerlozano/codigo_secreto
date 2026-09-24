from types import SimpleNamespace

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.products.images import product_image_delivery_urls
from core.local_storage import LocalReferenceStorage
from core.local_configuration import local_database


def test_local_test_profile():
    if settings.SETTINGS_MODULE != "core.settings_local":
        pytest.skip("Explicit local profile only")
    assert settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")
    assert settings.STORAGES["default"]["BACKEND"].endswith("InMemoryStorage")
    assert settings.EMAIL_BACKEND.endswith("locmem.EmailBackend")
    assert settings.PAYMENT_PROVIDER == "mock"
    assert not settings.CLOUDINARY_STORAGE["API_SECRET"]


def test_loopback_readonly_database_configuration(tmp_path):
    path = tmp_path / "postgres.env"
    path.write_text("POSTGRES_DB=test\nPOSTGRES_USER=test\nPOSTGRES_PASSWORD='synthetic'\nHOST=remote.invalid\n")
    database = local_database(path)
    assert (database["HOST"], database["PORT"]) == ("127.0.0.1", "5432")
    assert "default_transaction_read_only=on" in database["OPTIONS"]["options"]
    path.write_text("POSTGRES_PASSWORD='do-not-expose\n")
    with pytest.raises(ImproperlyConfigured, match="^Invalid local PostgreSQL configuration$"):
        local_database(path)


def test_missing_namespace_uses_existing_placeholder(settings):
    settings.LOCAL_CLOUDINARY_NAMESPACE = ""
    assert LocalReferenceStorage().url("products/example.webp") is None


def test_public_reference_is_not_transformed(settings):
    settings.LOCAL_CLOUDINARY_NAMESPACE = "synthetic-namespace"
    storage = LocalReferenceStorage()
    url = storage.url("products/example.webp")
    image = SimpleNamespace(url=url, storage=storage)
    delivery = product_image_delivery_urls(image, max_width=640)
    assert delivery.transformed == delivery.original == url
    assert url == "https://res.cloudinary.com/synthetic-namespace/image/upload/products/example.webp"


@pytest.mark.parametrize("operation", ["open", "save", "delete", "exists"])
def test_storage_operations_are_forbidden(operation):
    with pytest.raises(PermissionError):
        getattr(LocalReferenceStorage(), operation)("products/example.webp")


@pytest.mark.parametrize("name", ["../image", "https://remote.invalid/image", "/image"])
def test_invalid_references_are_rejected(settings, name):
    settings.LOCAL_CLOUDINARY_NAMESPACE = "synthetic"
    with pytest.raises(ValueError):
        LocalReferenceStorage().url(name)
