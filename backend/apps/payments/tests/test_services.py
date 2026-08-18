"""Service tests for backend-owned payment initiation (Unit 4, task 2.2).

Frozen attempt creation, the approved method set and the idempotency guards
at the service boundary. HTTP-level acceptance (masked 503/409/400 denial
contracts) lives in test_views.py; this file keeps service-only guarantees.
"""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.payments.models import Transaction
from apps.payments.services import (
    InvalidPaymentKeyError,
    SpecialDeliveryAgreementRequiredError,
    _replay_conflict,
    initiate_payment,
    normalize_idempotency_key,
)


@pytest.mark.django_db
class TestInitiatePaymentService:
    """Backend-owned initiation: frozen attempt and approved method set."""

    def test_initiate_creates_pending_attempt(self, order_factory, mock_payment_enabled):
        order = order_factory(status="PENDING", subtotal=20000, shipping_cost=3000, total=23000)

        attempt, url = initiate_payment(order=order, idempotency_key=None)

        assert (attempt.status, attempt.amount) == ("PENDING", 23000)
        assert (attempt.payment_method, attempt.provider) == ("webpay", "mock")
        assert attempt.idempotency_key is None
        assert "mock-checkout" in url and "token=" in url
        assert attempt.gateway_reference

    @pytest.mark.parametrize("method", ["webpay", "flow", "mercadopago", "transfer"])
    def test_approved_methods_are_supported(self, order_factory, mock_payment_enabled, method):
        order = order_factory(status="PENDING", payment_method=method)

        attempt, _ = initiate_payment(order=order, idempotency_key=None)

        assert attempt.payment_method == method


class TestReplayGuard:
    """Pure replay-guard rules: only PENDING, method-consistent attempts replay."""

    @pytest.mark.parametrize("status,method,expected", [
        ("PENDING", "webpay", False),
        ("PENDING", "flow", True),
        ("REJECTED", "webpay", True),
    ])
    def test_replay_requires_pending_and_matching_method(self, status, method, expected):
        existing = SimpleNamespace(status=status, payment_method=method)

        assert _replay_conflict(existing, "webpay") is expected


class TestNormalizeIdempotencyKey:
    """Header normalization: absent and blank values disable replay."""

    @pytest.mark.parametrize("raw,expected", [
        (None, None),
        ("", None),
        ("   ", None),
        ("pay-key-1", "pay-key-1"),
    ])
    def test_valid_keys(self, raw, expected):
        assert normalize_idempotency_key(raw) == expected

    @pytest.mark.parametrize("raw", ["k" * 65, 123, True])
    def test_unusable_keys_fail_closed(self, raw):
        with pytest.raises(InvalidPaymentKeyError):
            normalize_idempotency_key(raw)


@pytest.mark.django_db
class TestSpecialDeliveryPaymentGate:
    """A special-dispatch order blocks payment until staff records the
    agreement; standard delivery is never gated."""

    @staticmethod
    def _special_order(order_factory, agreed_at=None):
        return order_factory(
            status="PENDING", total=23000,
            delivery_kind="special",
            requested_dispatch_date=timezone.localdate() + timedelta(days=1),
            special_delivery_agreed_at=agreed_at,
        )

    def test_special_without_agreement_blocks_and_creates_no_transaction(
        self, order_factory, mock_payment_enabled
    ):
        order = self._special_order(order_factory)

        with pytest.raises(SpecialDeliveryAgreementRequiredError) as error:
            initiate_payment(order=order, idempotency_key=None)

        assert "whatsapp" in error.value.recovery_guidance.lower()
        assert error.value.whatsapp_url.startswith("https://wa.me/")
        assert error.value.poll_after_seconds > 0
        assert not Transaction.objects.filter(order=order).exists()

    def test_special_with_agreement_allows_payment(self, order_factory, mock_payment_enabled):
        order = self._special_order(order_factory, agreed_at=timezone.now())

        attempt, _ = initiate_payment(order=order, idempotency_key=None)

        assert attempt.status == "PENDING"
        assert Transaction.objects.filter(order=order).count() == 1

    def test_standard_delivery_without_dispatch_date_is_not_gated(self, order_factory, mock_payment_enabled):
        order = order_factory(status="PENDING", delivery_kind="standard", requested_dispatch_date=None)

        attempt, _ = initiate_payment(order=order, idempotency_key=None)

        assert attempt.status == "PENDING"
