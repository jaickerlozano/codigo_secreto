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


def test_email_port_and_tls_defaults_are_dev_safe():
    assert settings.EMAIL_PORT == 587
    assert settings.EMAIL_USE_TLS is True


def test_development_has_no_hardcoded_sender():
    assert settings.DEFAULT_FROM_EMAIL == ""


def test_local_settings_use_console_backend_without_smtp():
    local_settings = load_local_email_settings()

    assert (
        local_settings["EMAIL_BACKEND"]
        == "django.core.mail.backends.console.EmailBackend"
    )


def test_local_settings_preserve_explicit_smtp_configuration():
    local_settings = load_local_email_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="smtp.example.test",
        EMAIL_PORT="2525",
        EMAIL_USE_TLS="True",
        EMAIL_HOST_USER="test-user",
        EMAIL_HOST_PASSWORD="test-password",
        DEFAULT_FROM_EMAIL="notifications@example.test",
    )

    assert local_settings == {
        "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.example.test",
        "EMAIL_PORT": 2525,
        "EMAIL_USE_TLS": True,
        "EMAIL_HOST_USER": "test-user",
        "EMAIL_HOST_PASSWORD": "test-password",
        "DEFAULT_FROM_EMAIL": "notifications@example.test",
    }


def test_local_test_database_forces_locmem_email_backend():
    local_settings = load_local_email_settings(
        LOCAL_TEST_DATABASE="1",
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="smtp.example.test",
    )

    assert (
        local_settings["EMAIL_BACKEND"]
        == "django.core.mail.backends.locmem.EmailBackend"
    )


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
