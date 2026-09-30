"""Explicit local profile: catalog is read-only unless opted in; tests are disposable."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


from .local_configuration import local_database


if os.environ.get("DJANGO_READ_DOTENV") != "0" or os.environ.get("PIPENV_DONT_LOAD_ENV") != "1":
    raise ImproperlyConfigured("Local startup requires both dotenv guards")
if os.environ.get("ENVIRONMENT") == "production":
    raise ImproperlyConfigured("Local settings cannot be used for production")

# Replace service inputs before base settings are evaluated. Never load a dotenv.
os.environ.update({
    "ENVIRONMENT": "development", "DEBUG": "True", "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "local-development-only-not-a-production-secret-0000000000",
    "PAYMENT_PROVIDER": "mock",
    "CLOUDINARY_CLOUD_NAME": "", "CLOUDINARY_API_KEY": "",
    "CLOUDINARY_API_SECRET": "", "CLOUDINARY_UPLOAD_PRESET": "",
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "EMAIL_HOST": "", "EMAIL_PORT": "1025", "EMAIL_USE_TLS": "False",
    "EMAIL_HOST_USER": "", "EMAIL_HOST_PASSWORD": "",
    "SECRET_EMAIL": "", "SECRET_KEY_EMAIL": "",
    "DEFAULT_FROM_EMAIL": "local@example.invalid",
})

from .settings import *  # noqa: E402,F403

# Keep local integrations offline even if the base settings gain new aliases.
PAYMENT_PROVIDER = "mock"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_HOST = ""
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
SECRET_EMAIL = ""
SECRET_KEY_EMAIL = ""
DEFAULT_FROM_EMAIL = "local@example.invalid"
CLOUDINARY_STORAGE = {key: "" for key in CLOUDINARY_STORAGE}
STORAGES = {**STORAGES, "default": {"BACKEND": "core.local_storage.LocalReferenceStorage"}}
if os.environ.get("LOCAL_TEST_DATABASE") == "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.InMemoryStorage"}
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
else:
    # Manual checkout testing needs an explicit LOCAL_ALLOW_WRITES=1 opt-in;
    # the catalog connection stays read-only by default.
    LOCAL_ALLOW_WRITES = os.environ.get("LOCAL_ALLOW_WRITES") == "1"
    DATABASES = {"default": local_database(
        Path(__file__).resolve().parents[2] / "docker/postgres.env",
        read_only=not LOCAL_ALLOW_WRITES,
    )}
