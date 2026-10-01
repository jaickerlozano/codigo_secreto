"""Explicit local profile: catalog is read-only unless opted in; tests are disposable."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


from .local_configuration import local_database


LOCAL_MAILPIT_EMAIL = {
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": "127.0.0.1",
    "EMAIL_PORT": 1025,
    "EMAIL_USE_TLS": False,
    "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "",
    "DEFAULT_FROM_EMAIL": "local@example.invalid",
}


def local_email_configuration(*, testing):
    """Return the fixed local capture transport without consulting the environment."""
    if testing:
        return {
            **LOCAL_MAILPIT_EMAIL,
            "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
            "EMAIL_HOST": "",
        }
    return LOCAL_MAILPIT_EMAIL.copy()


if os.environ.get("DJANGO_READ_DOTENV") != "0" or os.environ.get("PIPENV_DONT_LOAD_ENV") != "1":
    raise ImproperlyConfigured("Local startup requires both dotenv guards")
if os.environ.get("ENVIRONMENT") == "production":
    raise ImproperlyConfigured("Local settings cannot be used for production")

LOCAL_TESTING = os.environ.get("LOCAL_TEST_DATABASE") == "1"
LOCAL_EMAIL = local_email_configuration(testing=LOCAL_TESTING)

# Replace service inputs before base settings are evaluated. Never load a dotenv.
os.environ.update({
    "ENVIRONMENT": "development", "DEBUG": "True", "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "local-development-only-not-a-production-secret-0000000000",
    "PAYMENT_PROVIDER": "mock",
    "CLOUDINARY_CLOUD_NAME": "", "CLOUDINARY_API_KEY": "",
    "CLOUDINARY_API_SECRET": "", "CLOUDINARY_UPLOAD_PRESET": "",
    **{key: str(value) for key, value in LOCAL_EMAIL.items()},
    "SECRET_EMAIL": "", "SECRET_KEY_EMAIL": "",
})

from .settings import *  # noqa: E402,F403

# Keep local integrations fixed to loopback-only services even if the base
# settings gain new aliases or the parent process contains SMTP credentials.
PAYMENT_PROVIDER = "mock"
globals().update(LOCAL_EMAIL)
SECRET_EMAIL = ""
SECRET_KEY_EMAIL = ""
CLOUDINARY_STORAGE = {key: "" for key in CLOUDINARY_STORAGE}
STORAGES = {**STORAGES, "default": {"BACKEND": "core.local_storage.LocalReferenceStorage"}}
if LOCAL_TESTING:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.InMemoryStorage"}
else:
    # Manual checkout testing needs an explicit LOCAL_ALLOW_WRITES=1 opt-in;
    # the catalog connection stays read-only by default.
    LOCAL_ALLOW_WRITES = os.environ.get("LOCAL_ALLOW_WRITES") == "1"
    DATABASES = {"default": local_database(
        Path(__file__).resolve().parents[2] / "docker/postgres.env",
        read_only=not LOCAL_ALLOW_WRITES,
    )}
