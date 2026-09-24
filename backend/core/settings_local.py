"""Explicit local profile: existing catalog is read-only, tests are disposable."""

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
    "PAYMENT_PROVIDER": "mock", "EMAIL_HOST": "", "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "", "EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend",
    "CLOUDINARY_CLOUD_NAME": "", "CLOUDINARY_API_KEY": "",
    "CLOUDINARY_API_SECRET": "", "CLOUDINARY_UPLOAD_PRESET": "",
})

from .settings import *  # noqa: E402,F403

LOCAL_CLOUDINARY_NAMESPACE = os.environ.get("LOCAL_CLOUDINARY_NAMESPACE", "")
STORAGES = {**STORAGES, "default": {"BACKEND": "core.local_storage.LocalReferenceStorage"}}
if os.environ.get("LOCAL_TEST_DATABASE") == "1":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.InMemoryStorage"}
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
else:
    DATABASES = {"default": local_database(Path(__file__).resolve().parents[2] / "docker/postgres.env")}
