import pytest
from django.db import IntegrityError

from apps.carts.models import Cart, CartItem


pytestmark = pytest.mark.django_db


def test_cart_str(cart_factory, user):
    """Cart.__str__ references the user's email."""
    cart = cart_factory(user=user)

    assert str(cart) == f"Carro de {user.email}"


def test_cart_item_str(cart_item_factory, product_factory):
    """CartItem.__str__ includes quantity, product name and user email."""
    product = product_factory(name="Vibrador X")
    item = cart_item_factory(product=product, quantity=3)

    expected = f"3 x Vibrador X (Carro: {item.cart.user.email})"
    assert str(item) == expected


def test_cart_item_subtotal(cart_item_factory, product_factory):
    """CartItem.subtotal equals quantity multiplied by product price."""
    product = product_factory(price=1000)
    item = cart_item_factory(product=product, quantity=3)

    assert item.subtotal == 3000


def test_cart_item_unique_together(cart_factory, cart_item_factory, product_factory):
    """The same product cannot be added twice to the same cart."""
    cart = cart_factory()
    product = product_factory()
    cart_item_factory(cart=cart, product=product, quantity=1)

    with pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, product=product, quantity=2)


def test_cart_total(cart_item_factory, product_factory, user):
    """Cart total is the sum of all item subtotals."""
    cart = user.cart
    product_a = product_factory(price=5000)
    product_b = product_factory(price=12000)
    cart_item_factory(cart=cart, product=product_a, quantity=2)
    cart_item_factory(cart=cart, product=product_b, quantity=1)

    cart.refresh_from_db()
    total = sum(item.subtotal for item in cart.items.all())

    assert total == 22000


def test_cart_auto_created_on_user_creation(user):
    """A Cart is automatically created for every new user via signal."""
    assert Cart.objects.filter(user=user).exists()
    assert user.cart is not None
