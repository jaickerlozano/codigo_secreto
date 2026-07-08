import pytest

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
