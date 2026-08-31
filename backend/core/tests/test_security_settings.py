"""Production configuration validation contracts."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from core.settings import validate_production_configuration


VALID_CONFIGURATION = {
    "ENVIRONMENT": "production",
    "SECRET_KEY": "a-production-secret-key-with-sufficient-entropy-for-testing",
    "DEBUG": "False",
    "FRONTEND_ORIGIN": "https://app.example.test",
    "API_HOSTNAME": "api.example.test",
    "ALLOWED_HOSTS": "api.example.test",
    "CORS_ALLOWED_ORIGINS": "https://app.example.test",
    "CSRF_TRUSTED_ORIGINS": "https://app.example.test",
    "COOKIE_TOPOLOGY": "shared-parent",
    "COOKIE_SITE_DOMAIN": "example.test",
    "TLS_TERMINATION": "proxy",
    "NUM_PROXIES": "1",
    "SECURE_HSTS_SECONDS": "3600",
    "DATABASE_URL": "postgresql://app:password@db.example.test:5432/app",
    "LOG_LEVEL": "INFO",
    "EMAIL_HOST": "smtp.example.test",
    "EMAIL_PORT": "587",
    "EMAIL_HOST_USER": "smtp-user",
    "EMAIL_HOST_PASSWORD": "smtp-password",
    "DEFAULT_FROM_EMAIL": "no-reply@example.test",
    "CLOUDINARY_CLOUD_NAME": "example-cloud",
    "CLOUDINARY_API_KEY": "example-key",
    "CLOUDINARY_API_SECRET": "example-secret",
    "CLOUDINARY_UPLOAD_PRESET": "example-preset",
}

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_COMMAND = """import json
from core import settings
print(json.dumps({
    "allowed": settings.ALLOWED_HOSTS,
    "cors": settings.CORS_ALLOWED_ORIGINS,
    "csrf": settings.CSRF_TRUSTED_ORIGINS,
    "database": settings.DATABASES["default"]["ENGINE"],
    "debug": settings.DEBUG,
    "log": settings.LOGGING["root"]["level"],
    "deploy": [settings.SECURE_SSL_REDIRECT, settings.SECURE_HSTS_SECONDS, settings.SECURE_CONTENT_TYPE_NOSNIFF, settings.X_FRAME_OPTIONS],
    "proxy": [settings.SECURE_PROXY_SSL_HEADER, settings.SECURE_SSL_REDIRECT, settings.USE_X_FORWARDED_HOST],
    "headers": [settings.SECURE_HSTS_INCLUDE_SUBDOMAINS, settings.SECURE_CONTENT_TYPE_NOSNIFF, settings.X_FRAME_OPTIONS, settings.SECURE_REFERRER_POLICY],
    "storage": [settings.STORAGES["default"]["BACKEND"], settings.STORAGES["staticfiles"]["BACKEND"]],
}))"""


def production_configuration(**overrides):
    configuration = dict(VALID_CONFIGURATION)
    for setting, value in overrides.items():
        if value is None:
            configuration.pop(setting)
        else:
            configuration[setting] = value
    return configuration


def import_settings(configuration):
    environment = os.environ | configuration
    return subprocess.run(
        [sys.executable, "-c", SNAPSHOT_COMMAND],
        cwd=BACKEND_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_shared_parent_configuration_returns_derived_cookie_domain():
    configuration = validate_production_configuration(VALID_CONFIGURATION)

    assert configuration["ALLOWED_HOSTS"] == ("api.example.test",)
    assert configuration["csrf_cookie_domain"] == ".example.test"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"ENVIRONMENT": "development"}, "ENVIRONMENT"),
        ({"SECRET_KEY": None}, "SECRET_KEY"),
        ({"DATABASE_URL": None}, "DATABASE_URL"),
        ({"LOG_LEVEL": None}, "LOG_LEVEL"),
        ({"CLOUDINARY_API_SECRET": None}, "CLOUDINARY_API_SECRET"),
        ({"EMAIL_HOST_PASSWORD": ""}, "EMAIL_HOST_PASSWORD"),
        ({"API_HOSTNAME": "localhost"}, "API_HOSTNAME"),
        ({"ALLOWED_HOSTS": "*"}, "ALLOWED_HOSTS"),
        ({"FRONTEND_ORIGIN": "app.example.test"}, "FRONTEND_ORIGIN"),
        ({"FRONTEND_ORIGIN": "https://user:pass@app.example.test"}, "FRONTEND_ORIGIN"),
        ({"FRONTEND_ORIGIN": "https://app.unrelated.test"}, "FRONTEND_ORIGIN"),
        ({"COOKIE_TOPOLOGY": "host-only"}, "COOKIE_TOPOLOGY"),
        ({"TLS_TERMINATION": "none"}, "TLS_TERMINATION"),
        ({"SECURE_HSTS_SECONDS": "0"}, "SECURE_HSTS_SECONDS"),
        ({"DATABASE_URL": "postgresql://app:password@db.example.test:invalid/app"}, "DATABASE_URL"),
        ({"CORS_ALLOWED_ORIGINS": "https://other.example.test"}, "CORS_ALLOWED_ORIGINS"),
        ({"DEBUG": "True"}, "DEBUG"),
        (
            {
                "COOKIE_SITE_DOMAIN": "co.uk",
                "API_HOSTNAME": "api.co.uk",
                "ALLOWED_HOSTS": "api.co.uk",
                "FRONTEND_ORIGIN": "https://app.co.uk",
                "CORS_ALLOWED_ORIGINS": "https://app.co.uk",
                "CSRF_TRUSTED_ORIGINS": "https://app.co.uk",
            },
            "public suffix",
        ),
    ],
)
def test_unsafe_production_tuples_are_rejected(overrides, expected):
    with pytest.raises(ImproperlyConfigured) as error:
        validate_production_configuration(production_configuration(**overrides))

    assert expected in str(error.value)


def test_multiple_production_failures_are_aggregated():
    with pytest.raises(ImproperlyConfigured) as error:
        validate_production_configuration(
            production_configuration(
                SECRET_KEY=None,
                DEBUG="True",
                SECURE_HSTS_SECONDS="0",
            )
        )

    assert all(setting in str(error.value) for setting in ("SECRET_KEY", "DEBUG", "SECURE_HSTS_SECONDS"))


def test_production_import_fails_closed_and_applies_deploy_controls():
    blocked = import_settings(production_configuration(DATABASE_URL=""))
    ready = import_settings(VALID_CONFIGURATION)

    assert blocked.returncode != 0 and "DATABASE_URL" in blocked.stderr
    assert ready.returncode == 0, ready.stderr
    assert json.loads(ready.stdout) == {
        "allowed": ["api.example.test"],
        "cors": ["https://app.example.test"],
        "csrf": ["https://app.example.test"],
        "database": "django.db.backends.postgresql",
        "debug": False,
        "log": "INFO",
        "deploy": [True, 3600, True, "DENY"],
        "proxy": [["HTTP_X_FORWARDED_PROTO", "https"], True, False],
        "headers": [True, True, "DENY", "same-origin"],
        "storage": [
            "cloudinary_storage.storage.MediaCloudinaryStorage",
            "django.contrib.staticfiles.storage.StaticFilesStorage",
        ],
    }


@pytest.mark.parametrize("environment", ("development", "test"))
def test_local_modes_preserve_localhost_and_sqlite_fallbacks(environment):
    result = import_settings(
        production_configuration(ENVIRONMENT=environment, DATABASE_URL="")
    )

    assert result.returncode == 0, result.stderr
    snapshot = json.loads(result.stdout)
    assert snapshot["allowed"] == ["localhost", "127.0.0.1"]
    assert snapshot["database"] == "django.db.backends.sqlite3"
    assert snapshot["deploy"] == [False, 0, False, "DENY"]
    assert snapshot["proxy"] == [None, False, False]
    assert snapshot["headers"] == [False, False, "DENY", "same-origin"]
    assert snapshot["storage"] == [
        "cloudinary_storage.storage.MediaCloudinaryStorage",
        "django.contrib.staticfiles.storage.StaticFilesStorage",
    ]
