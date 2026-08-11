"""Provider abstraction contract tests (Unit 4, task 2.2).

The base provider only defines the initiation contract; the mock provider
produces a deterministic development continuation contract with unique
gateway references per attempt.
"""
from types import SimpleNamespace

import pytest

from apps.payments.providers import BasePaymentProvider, MockPaymentProvider


def test_base_provider_requires_initiation_implementation():
    """The abstraction never initiates: subclasses must implement it."""
    with pytest.raises(NotImplementedError):
        BasePaymentProvider(order=None).initiate(method="webpay", idempotency_key=None)


def test_mock_provider_returns_dev_continuation_contract():
    """Mock initiation returns a dev continuation URL and a unique reference."""
    provider = MockPaymentProvider(order=SimpleNamespace(id=7))

    reference, url = provider.initiate(method="webpay", idempotency_key="pay-key-1")
    second, _ = provider.initiate(method="webpay", idempotency_key=None)

    assert "mock-checkout" in url
    assert str(7) in reference
    assert provider.continuation_url(reference) == url
    assert provider.continuation_url("ref-1") == provider.continuation_url("ref-1")
    assert second != reference
