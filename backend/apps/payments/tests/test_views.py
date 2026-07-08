import pytest
from django.urls import reverse

from apps.payments.models import Transaction


@pytest.mark.django_db
class TestInitiatePaymentView:
    """Integration tests for the payment initiation endpoint."""

    def test_initiate_payment_success(self, api_client, order_factory):
        """Initiating payment for a pending order creates a Transaction and returns a mock URL."""
        order = order_factory(status="PENDING", total=30000)

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

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

    def test_initiate_payment_public(self, api_client, order_factory):
        """The endpoint is public and works without authentication."""
        order = order_factory(status="PENDING")

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 200

    def test_initiate_payment_amount_matches(self, api_client, order_factory):
        """The created transaction amount equals the order total."""
        order = order_factory(status="PENDING", total=45000)

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 200
        transaction = Transaction.objects.get(order=order)
        assert transaction.amount == order.total
        assert response.json()["amount"] == order.total

    def test_validate_paid_order(self, api_client, order_factory):
        """Payment initiation fails when the order is not in PENDING status."""
        order = order_factory(status="PAID")

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 400
        assert "no se puede pagar" in str(response.json()).lower()

    def test_initiate_payment_nonexistent_order(self, api_client):
        """Payment initiation fails when the order does not exist."""
        response = api_client.post("/api/payments/initiate/", {"order_id": 99999})

        assert response.status_code == 400
        assert "no existe" in str(response.json()).lower()

    def test_initiate_payment_already_paid(self, api_client, order_factory, transaction_factory):
        """Payment initiation fails when the order already has an APPROVED transaction."""
        order = order_factory(status="PENDING", total=15000)
        transaction_factory(order=order, status="APPROVED")

        response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert response.status_code == 400
        assert "ya fue pagado" in str(response.json()).lower()

    def test_multiple_payment_attempts_create_multiple_transactions(self, api_client, order_factory):
        """Multiple payment attempts for the same pending order create multiple transactions."""
        order = order_factory(status="PENDING", total=20000)

        first_response = api_client.post("/api/payments/initiate/", {"order_id": order.id})
        second_response = api_client.post("/api/payments/initiate/", {"order_id": order.id})

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert Transaction.objects.filter(order=order).count() == 2
