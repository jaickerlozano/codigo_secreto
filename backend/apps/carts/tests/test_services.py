import pytest

from apps.carts.services import (
    FREE_SHIPPING_THRESHOLD,
    FLAT_SHIPPING_RATE,
    calculate_cart_totals,
    calculate_shipping_cost,
)


pytestmark = pytest.mark.django_db


def test_calculate_shipping_cost_empty():
    """Carritos vacíos no pagan envío."""
    assert calculate_shipping_cost(0) == 0


def test_calculate_shipping_cost_below_threshold():
    """Subtotales bajo el umbral usan la tarifa plana."""
    assert calculate_shipping_cost(FREE_SHIPPING_THRESHOLD - 1) == FLAT_SHIPPING_RATE


def test_calculate_shipping_cost_at_threshold():
    """Subtotales que alcanzan el umbral tienen envío gratis."""
    assert calculate_shipping_cost(FREE_SHIPPING_THRESHOLD) == 0


def test_calculate_shipping_cost_above_threshold():
    """Subtotales sobre el umbral tienen envío gratis."""
    assert calculate_shipping_cost(FREE_SHIPPING_THRESHOLD + 1) == 0


def test_calculate_cart_totals_empty(user):
    """Un carrito vacío tiene todos los totales en cero."""
    totals = calculate_cart_totals(user.cart)

    assert totals["subtotal"] == 0
    assert totals["shipping_cost"] == 0
    assert totals["total"] == 0
    assert totals["free_shipping_progress"] == 0
    assert totals["free_shipping_threshold"] == FREE_SHIPPING_THRESHOLD


def test_calculate_cart_totals_with_items(cart_item_factory, product_factory, user):
    """Un carrito con ítems calcula subtotal, envío, total y progreso."""
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=2)

    totals = calculate_cart_totals(user.cart)

    assert totals["subtotal"] == 20000
    assert totals["shipping_cost"] == FLAT_SHIPPING_RATE
    assert totals["total"] == 20000 + FLAT_SHIPPING_RATE
    assert totals["free_shipping_progress"] == pytest.approx(
        (20000 / FREE_SHIPPING_THRESHOLD) * 100
    )
    assert totals["free_shipping_threshold"] == FREE_SHIPPING_THRESHOLD


def test_calculate_cart_totals_free_shipping(cart_item_factory, product_factory, user):
    """Un carrito que supera el umbral tiene envío gratis."""
    product = product_factory(price=FREE_SHIPPING_THRESHOLD)
    cart_item_factory(cart=user.cart, product=product, quantity=1)

    totals = calculate_cart_totals(user.cart)

    assert totals["subtotal"] == FREE_SHIPPING_THRESHOLD
    assert totals["shipping_cost"] == 0
    assert totals["total"] == FREE_SHIPPING_THRESHOLD
    assert totals["free_shipping_progress"] == 100
