import pytest
from django.db import IntegrityError

from apps.payments.models import Transaction


@pytest.mark.django_db
class TestTransactionModel:
    """Unit tests for the Transaction model."""

    def test_transaction_default_status(self, transaction_factory):
        """A new transaction defaults to PENDING status."""
        transaction = transaction_factory()

        assert transaction.status == "PENDING"

    def test_transaction_str(self, transaction_factory):
        """__str__ includes the transaction id, order id and status label."""
        transaction = transaction_factory()

        representation = str(transaction)

        assert f"Transacción #{transaction.id}" in representation
        assert f"Pedido #{transaction.order.id}" in representation
        assert transaction.get_status_display() in representation

    def test_transaction_amount_matches_order_total(self, transaction_factory, order_factory):
        """Transaction.amount is set to the linked order's total."""
        order = order_factory(total=45000)
        transaction = transaction_factory(order=order)

        assert transaction.amount == 45000
        assert transaction.amount == order.total

    def test_transaction_status_choices(self, transaction_factory):
        """Transaction supports PENDING, APPROVED and REJECTED statuses."""
        transaction = transaction_factory()

        assert transaction.status == "PENDING"

        transaction.status = "APPROVED"
        transaction.save()
        transaction.refresh_from_db()
        assert transaction.status == "APPROVED"

        transaction.status = "REJECTED"
        transaction.save()
        transaction.refresh_from_db()
        assert transaction.status == "REJECTED"

    def test_transaction_ordering(self, transaction_factory, order_factory):
        """Transactions are ordered by newest created_at first."""
        order = order_factory()
        first = transaction_factory(order=order, gateway_reference="first")
        second = transaction_factory(order=order, gateway_reference="second")

        transactions = list(Transaction.objects.filter(order=order))

        assert transactions[0] == second
        assert transactions[1] == first

    def test_transaction_idempotency_key_unique_per_order(self, transaction_factory, order_factory):
        """Two attempts for the same order with the same idempotency key are rejected."""
        order = order_factory()
        transaction_factory(order=order, idempotency_key="attempt-1")

        with pytest.raises(IntegrityError):
            transaction_factory(order=order, idempotency_key="attempt-1")

    def test_transaction_same_idempotency_key_allowed_across_orders(self, transaction_factory, order_factory):
        """The same idempotency key is allowed for different orders."""
        order_a = order_factory()
        order_b = order_factory()

        transaction_factory(order=order_a, idempotency_key="shared-key")
        transaction = transaction_factory(order=order_b, idempotency_key="shared-key")

        assert transaction.idempotency_key == "shared-key"

    def test_transaction_new_idempotency_key_allows_retry(self, transaction_factory, order_factory):
        """An order may retry with a NEW idempotency key without duplicates."""
        order = order_factory()
        transaction_factory(order=order, idempotency_key="attempt-1")
        transaction_factory(order=order, idempotency_key="attempt-2")

        assert Transaction.objects.filter(order=order).count() == 2

    def test_transaction_provider_and_method_are_persisted(self, transaction_factory, order_factory):
        """Provider and payment method are stored on the attempt."""
        order = order_factory()
        transaction = transaction_factory(order=order, provider="mock", payment_method="webpay")
        transaction.refresh_from_db()

        assert transaction.provider == "mock"
        assert transaction.payment_method == "webpay"
