"""Env-driven email settings with deterministic backend precedence.

The precedence helper is unit-tested directly because the test runner may
override EMAIL_BACKEND at runtime; the helper decides the value at settings
load time.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings

from core.settings import _resolve_database_config, _resolve_email_backend


EMAIL_SETTINGS = (
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_USE_TLS",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "DEFAULT_FROM_EMAIL",
    "SECRET_EMAIL",
    "SECRET_KEY_EMAIL",
)


def load_local_email_settings(**overrides):
    environment = os.environ.copy()
    for setting in (*EMAIL_SETTINGS, "LOCAL_TEST_DATABASE"):
        environment.pop(setting, None)
    environment.update(
        {
            "PIPENV_DONT_LOAD_ENV": "1",
            "DJANGO_READ_DOTENV": "0",
            "DJANGO_SETTINGS_MODULE": "core.settings_local",
            # Email tests must not read or connect to the shared PostgreSQL setup.
            "LOCAL_TEST_DATABASE": "1",
            **overrides,
        }
    )
    script = """
import json
from django.conf import settings

print(json.dumps({
    name: getattr(settings, name)
    for name in (
        "EMAIL_BACKEND", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_USE_TLS",
        "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "DEFAULT_FROM_EMAIL",
    )
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        text=True,
    )
    return json.loads(result.stdout)


def test_local_email_transport_has_no_smtp_tls_configuration():
    assert settings.EMAIL_PORT == 1025
    assert settings.EMAIL_USE_TLS is False


def test_local_sender_uses_a_non_deliverable_domain():
    assert settings.DEFAULT_FROM_EMAIL == "local@example.invalid"


LOCAL_EMAIL_SETTINGS = {
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "EMAIL_HOST": "",
    "EMAIL_PORT": 1025,
    "EMAIL_USE_TLS": False,
    "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "",
    "DEFAULT_FROM_EMAIL": "local@example.invalid",
}


def test_local_settings_use_in_memory_email_without_smtp():
    assert load_local_email_settings() == LOCAL_EMAIL_SETTINGS


@pytest.mark.parametrize(
    "smtp_overrides",
    [
        {
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "EMAIL_HOST": "smtp.example.test",
            "EMAIL_PORT": "2525",
            "EMAIL_USE_TLS": "True",
            "EMAIL_HOST_USER": "test-user",
            "EMAIL_HOST_PASSWORD": "test-password",
            "DEFAULT_FROM_EMAIL": "notifications@example.test",
        },
        {
            "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "EMAIL_HOST": "smtp.example.test",
            "SECRET_EMAIL": "alias-sender@example.test",
            "SECRET_KEY_EMAIL": "alias-password",
        },
    ],
)
def test_local_settings_ignore_all_smtp_configuration(smtp_overrides):
    assert load_local_email_settings(**smtp_overrides) == LOCAL_EMAIL_SETTINGS


def test_debug_blank_host_selects_console_backend():
    assert _resolve_email_backend(debug=True, email_host="") == (
        "django.core.mail.backends.console.EmailBackend"
    )
    assert _resolve_email_backend(debug=True, email_host=None) == (
        "django.core.mail.backends.console.EmailBackend"
    )


def test_any_explicit_host_selects_smtp_backend():
    assert _resolve_email_backend(debug=True, email_host="smtp.example.test") == (
        "django.core.mail.backends.smtp.EmailBackend"
    )
    assert _resolve_email_backend(debug=False, email_host="smtp.example.test") == (
        "django.core.mail.backends.smtp.EmailBackend"
    )


def test_explicit_backend_is_selected_in_development():
    assert (
        _resolve_email_backend(
            debug=True,
            email_host="",
            email_backend="django.core.mail.backends.console.EmailBackend",
        )
        == "django.core.mail.backends.console.EmailBackend"
    )
    assert (
        _resolve_email_backend(
            debug=True,
            email_host="smtp.example.test",
            email_backend="django.core.mail.backends.smtp.EmailBackend",
        )
        == "django.core.mail.backends.smtp.EmailBackend"
    )


def test_database_url_selects_postgresql_configuration():
    database = _resolve_database_config(
        "postgres://sdd_user@127.0.0.1:5432/sdd_notifications"
    )

    assert database["ENGINE"] == "django.db.backends.postgresql"
    assert database["NAME"] == "sdd_notifications"
    assert database["HOST"] == "127.0.0.1"
    assert database["PORT"] == 5432


def test_missing_database_url_keeps_sqlite_default():
    database = _resolve_database_config(None)

    assert database == {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": settings.BASE_DIR / "db.sqlite3",
    }
