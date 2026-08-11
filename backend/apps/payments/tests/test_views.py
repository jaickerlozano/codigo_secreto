import pytest
from django.test import override_settings
from rest_framework import status

from apps.payments.models import Transaction


@pytest.mark.django_db
class TestInitiatePaymentView:
    """Integration tests for the payment initiation endpoint."""

    def test_initiate_payment_success(self, authenticated_client, order_factory, user, mock_payment_enabled):
        """An authorized owner still receives the existing mock payment response."""
        order = order_factory(user=user, status="PENDING", total=30000)

        response = authenticated_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert "order_id" in data
        assert "amount" in data
        assert "payment_url" in data
        assert "gateway_reference" in data
        assert data["order_id"] == order.id
        assert data["amount"] == order.total
        assert "mock-checkout" in data["payment_url"]
        assert Transaction.objects.filter(order=order).exists()

    def test_initiate_payment_without_access_creates_no_transaction(self, api_client, order_factory):
        """An inaccessible order is masked and cannot create a transaction."""
        order = order_factory(status="PENDING")

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Not found."}
        assert not Transaction.objects.filter(order=order).exists()

    def test_validate_paid_order(self, authenticated_client, order_factory, user, mock_payment_enabled):
        """Payment initiation fails when the order is not in PENDING status."""
        order = order_factory(user=user, status="PAID")

        response = authenticated_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 400
        assert "no se puede pagar" in str(response.json()).lower()

    def test_initiate_payment_nonexistent_order_is_masked(self, api_client):
        """Unknown order identifiers are indistinguishable from unauthorized access."""
        response = api_client.post("/api/payments/initiate/", {"order_id": 99999})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Not found."}

    def test_initiate_payment_already_paid(self, authenticated_client, order_factory, transaction_factory, user, mock_payment_enabled):
        """Payment initiation fails when the order already has an APPROVED transaction."""
        order = order_factory(user=user, status="PENDING", total=15000)
        transaction_factory(order=order, status="APPROVED")

        response = authenticated_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 400
        assert "ya fue pagado" in str(response.json()).lower()

    @pytest.mark.parametrize("debug,provider", [(False, "mock"), (True, None), (True, "stripe")])
    def test_initiation_denied_when_mock_not_explicitly_enabled(self, authenticated_client, order_factory, user, debug, provider):
        """Production, absent and unknown providers fail closed with a masked 503."""
        order = order_factory(user=user, status="PENDING", total=30000)
        with override_settings(DEBUG=debug, PAYMENT_PROVIDER=provider):
            response = authenticated_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {"detail": "Payment service unavailable."}
        assert not Transaction.objects.filter(order=order).exists()

    def test_idempotent_replay_returns_same_attempt(self, authenticated_client, order_factory, user, mock_payment_enabled):
        """The same owned order and key replay the one pending attempt."""
        order = order_factory(user=user, status="PENDING", total=30000)

        def post(key):
            return authenticated_client.post(
                "/api/payments/initiate/", {"order_id": order.id}, HTTP_IDEMPOTENCY_KEY=key
            )

        first, second = post("pay-key-1"), post("pay-key-1")

        assert first.status_code == second.status_code == 200
        assert first.json()["transaction_id"] == second.json()["transaction_id"]
        assert first.json()["payment_url"] == second.json()["payment_url"]
        assert Transaction.objects.filter(order=order).count() == 1

    def test_conflicting_key_reuse_is_masked_409(self, authenticated_client, order_factory, user, mock_payment_enabled):
        """Reusing a key for another order fails masked and creates nothing."""
        order = order_factory(user=user, status="PENDING", total=15000)
        other = order_factory(user=user, status="PENDING", total=20000)
        assert authenticated_client.post(
            "/api/payments/initiate/", {"order_id": order.id}, HTTP_IDEMPOTENCY_KEY="pay-key-2"
        ).status_code == 200

        response = authenticated_client.post(
            "/api/payments/initiate/", {"order_id": other.id}, HTTP_IDEMPOTENCY_KEY="pay-key-2"
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert set(response.json()) == {"code", "detail"}
        assert not Transaction.objects.filter(order=other).exists()

    def test_unsupported_payment_method_rejected(self, authenticated_client, order_factory, user, mock_payment_enabled):
        """An order with a non-approved method cannot initiate payment."""
        order = order_factory(user=user, status="PENDING", payment_method="crypto")

        response = authenticated_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 400
        assert "no está disponible" in str(response.json()).lower()
        assert not Transaction.objects.filter(order=order).exists()

    def test_invalid_idempotency_key_rejected(self, authenticated_client, order_factory, user, mock_payment_enabled):
        """An unusable key fails closed instead of silently disabling idempotency."""
        order = order_factory(user=user, status="PENDING", total=30000)

        response = authenticated_client.post(
            "/api/payments/initiate/", {"order_id": order.id}, HTTP_IDEMPOTENCY_KEY="k" * 65
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "idempotency" in str(response.json()["detail"]).lower()
        assert not Transaction.objects.filter(order=order).exists()

    def test_guest_capability_cookie_authorizes_payment(self, api_client, order_factory, mock_payment_enabled):
        """A guest with a valid exchanged cookie can initiate payment."""
        order = order_factory(user=None, status="PENDING")
        raw_token = order.issue_guest_access()
        exchange = api_client.post(
            f"/api/orders/by-order-number/{order.order_number}/access/",
            {},
            format="json",
            HTTP_X_ORDER_CAPABILITY=raw_token,
        )
        api_client.cookies["guest_order_access"] = exchange.cookies["guest_order_access"].value

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == status.HTTP_200_OK
        assert Transaction.objects.filter(order=order).count() == 1

        from django.core.cache import cache
        from rest_framework.settings import api_settings
        cache.clear()
        api_settings.DEFAULT_THROTTLE_RATES['payment_initiate'] = '2/min'
        assert api_client.post('/api/payments/initiate/', {'order_id': order.id}).status_code == 200
        assert api_client.post('/api/payments/initiate/', {'order_id': order.id}).status_code == 200
        assert api_client.post('/api/payments/initiate/', {'order_id': order.id}).status_code == 429
        cache.clear()
        assert api_client.post('/api/payments/initiate/', {'order_id': order.id}).status_code == 200
