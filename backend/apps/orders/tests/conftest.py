import pytest
from rest_framework.throttling import SimpleRateThrottle

from apps.carts.tests.factories import CartFactory, CartItemFactory
from apps.orders.tests.factories import OrderFactory, OrderItemFactory
from apps.products.tests.factories import ProductFactory
from apps.shipping.tests.factories import ComunaFactory


def reset_order_throttle_cache():
    """Clear test-client throttle history between order test cases."""
    SimpleRateThrottle.cache.clear()


@pytest.fixture(autouse=True)
def reset_order_throttle_cache_between_tests():
    reset_order_throttle_cache()


@pytest.fixture
def order_factory():
    """Return the OrderFactory class."""
    return OrderFactory


@pytest.fixture
def order_item_factory():
    """Return the OrderItemFactory class."""
    return OrderItemFactory


@pytest.fixture
def product_factory():
    """Return the ProductFactory class."""
    return ProductFactory


@pytest.fixture
def comuna_factory():
    """Return the ComunaFactory class."""
    return ComunaFactory


@pytest.fixture
def cart_factory():
    """Return the CartFactory class."""
    return CartFactory


@pytest.fixture
def cart_item_factory():
    """Return the CartItemFactory class."""
    return CartItemFactory


@pytest.fixture
def pending_order(db, order_factory, order_item_factory, product_factory):
    """Order in PENDING status with a single item."""
    product = product_factory(price=10000)
    order = order_factory(status="PENDING", subtotal=20000, shipping_cost=3000, total=23000)
    order_item_factory(order=order, product=product, quantity=2, price=10000)
    order.refresh_from_db()
    return order


@pytest.fixture
def paid_order(db, order_factory, order_item_factory, product_factory):
    """Order in PAID status with a single item."""
    product = product_factory(price=15000)
    order = order_factory(status="PAID", subtotal=15000, shipping_cost=4000, total=19000)
    order_item_factory(order=order, product=product, quantity=1, price=15000)
    order.refresh_from_db()
    return order
