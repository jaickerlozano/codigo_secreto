"""Env-driven email settings (deferred from Unit 2); the test runner overrides
EMAIL_BACKEND, so only non-overridden env values are asserted."""
from django.conf import settings


def test_email_port_and_tls_defaults_are_dev_safe():
    assert settings.EMAIL_PORT == 587
    assert settings.EMAIL_USE_TLS is True


def test_branded_default_from_email():
    assert settings.DEFAULT_FROM_EMAIL == "Código Secreto <no-reply@codigosecreto.cl>"
