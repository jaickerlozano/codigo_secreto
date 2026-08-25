import pytest

from apps.carts.services import calculate_cart_totals
from apps.shipping.tests.factories import (
    ComunaFactory,
    RegionFactory,
)


pytestmark = pytest.mark.django_db


def test_calculate_cart_totals_empty(user):
    """Un carrito vacío tiene todos los totales en cero."""
    totals = calculate_cart_totals(user.cart)

    assert totals["subtotal"] == 0
    assert totals["shipping_cost"] == 0
    assert totals["total"] == 0
    assert totals["free_shipping_progress"] == 0
    assert totals["free_shipping_threshold"] == 0


def test_calculate_cart_totals_without_destination_is_not_quoted(cart_item_factory, product_factory, user):
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=2)

    totals = calculate_cart_totals(user.cart)

    assert totals["subtotal"] == 20000
    assert totals["shipping_cost"] is None
    assert totals["total"] is None
    assert totals["free_shipping_progress"] == 0
    assert totals["free_shipping_threshold"] == 0


def test_calculate_cart_totals_santiago_selector_uses_exact_comuna_cost(
    cart_item_factory, product_factory, user
):
    """Con comuna de destino, el estimado usa exactamente el costo de la comuna."""
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=2)
    comuna = ComunaFactory(
        region=RegionFactory(name="Metropolitana de Santiago", ordinal_number=7),
        shipping_cost=3500,
    )

    totals = calculate_cart_totals(user.cart, comuna_selector=comuna.id)

    assert (totals["subtotal"], totals["shipping_cost"], totals["total"]) == (20000, 3500, 23500)


def test_calculate_cart_totals_regional_selector_uses_exact_comuna_cost(
    cart_item_factory, product_factory, user
):
    """A regional quote uses its comuna price without a dispatch profile."""
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=1)
    comuna = ComunaFactory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)

    totals = calculate_cart_totals(user.cart, comuna_selector=comuna.id)

    assert (totals["shipping_cost"], totals["total"]) == (9000, 19000)


def test_calculate_cart_totals_ineligible_comuna_fails_closed(
    cart_item_factory, product_factory, user
):
    """A zero-priced comuna cannot be estimated."""
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=1)
    comuna = ComunaFactory(region=RegionFactory(name="Valparaiso"), shipping_cost=0)

    totals = calculate_cart_totals(user.cart, comuna_selector=comuna.id)

    assert totals["shipping_cost"] is None and totals["total"] is None
