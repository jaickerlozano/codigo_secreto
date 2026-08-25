"""Env-driven email settings with deterministic backend precedence.

The precedence helper is unit-tested directly because the test runner may
override EMAIL_BACKEND at runtime; the helper decides the value at settings
load time.
"""
from django.conf import settings

from core.settings import _resolve_email_backend


def test_email_port_and_tls_defaults_are_dev_safe():
    assert settings.EMAIL_PORT == 587
    assert settings.EMAIL_USE_TLS is True


def test_branded_default_from_email():
    assert settings.DEFAULT_FROM_EMAIL == "Código Secreto <no-reply@codigosecreto.cl>"


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


def test_production_never_falls_back_to_console():
    assert _resolve_email_backend(
        debug=False,
        email_host="",
        email_backend="django.core.mail.backends.console.EmailBackend",
    ) == "django.core.mail.backends.smtp.EmailBackend"
    assert _resolve_email_backend(
        debug=False,
        email_host="smtp.example.test",
        email_backend="django.core.mail.backends.console.EmailBackend",
    ) == "django.core.mail.backends.smtp.EmailBackend"
