import pytest
from rest_framework import status

from apps.payments.models import Transaction


@pytest.mark.django_db
class TestInitiatePaymentView:
    """Integration tests for the payment initiation endpoint."""

    def test_initiate_payment_success(self, authenticated_client, order_factory, user):
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

    def test_validate_paid_order(self, authenticated_client, order_factory, user):
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

    def test_initiate_payment_already_paid(self, authenticated_client, order_factory, transaction_factory, user):
        """Payment initiation fails when the order already has an APPROVED transaction."""
        order = order_factory(user=user, status="PENDING", total=15000)
        transaction_factory(order=order, status="APPROVED")

        response = authenticated_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 400
        assert "ya fue pagado" in str(response.json()).lower()

    def test_guest_capability_cookie_authorizes_payment(self, api_client, order_factory):
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
