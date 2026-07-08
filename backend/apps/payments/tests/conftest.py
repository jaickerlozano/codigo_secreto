import pytest

from apps.orders.tests.factories import OrderFactory
from apps.payments.tests.factories import TransactionFactory


@pytest.fixture
def transaction_factory():
    """Return the TransactionFactory class."""
    return TransactionFactory


@pytest.fixture
def order_factory():
    """Return the OrderFactory class."""
    return OrderFactory


@pytest.fixture
def pending_order_for_payment(db, order_factory):
    """Order in PENDING status ready for payment initiation."""
    return order_factory(status="PENDING", subtotal=20000, shipping_cost=3000, total=23000)
