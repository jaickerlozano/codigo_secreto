import pytest

from apps.carts.tests.factories import CartFactory, CartItemFactory
from apps.products.tests.factories import ProductFactory


@pytest.fixture
def cart_factory():
    """Return the CartFactory class."""
    return CartFactory


@pytest.fixture
def cart_item_factory():
    """Return the CartItemFactory class."""
    return CartItemFactory


@pytest.fixture
def product_factory():
    """Return the ProductFactory class."""
    return ProductFactory


@pytest.fixture
def empty_cart(authenticated_client, user):
    """Return the authenticated user's empty signal-created cart."""
    return user.cart


@pytest.fixture
def cart_with_items(db, user, product_factory, cart_item_factory):
    """Cart with two items for total calculation tests."""
    cart = user.cart
    product_a = product_factory(price=5000)
    product_b = product_factory(price=12000)
    cart_item_factory(cart=cart, product=product_a, quantity=2)
    cart_item_factory(cart=cart, product=product_b, quantity=1)
    cart.refresh_from_db()
    return cart
