import pytest

from apps.carts.services import (
    FREE_SHIPPING_THRESHOLD,
    FLAT_SHIPPING_RATE,
    calculate_cart_totals,
    calculate_shipping_cost,
)
from apps.shipping.tests.factories import (
    ComunaFactory,
    RegionFactory,
    RegionalShippingOptionFactory,
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


def test_calculate_cart_totals_regional_selector_uses_exact_sole_active_tariff(
    cart_item_factory, product_factory, user
):
    """Con comuna regional aplicable, el estimado usa exactamente la tarifa activa."""
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=1)
    comuna = ComunaFactory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)
    RegionalShippingOptionFactory(key="regional", tariff=5500)

    totals = calculate_cart_totals(user.cart, comuna_selector=comuna.id)

    assert (totals["shipping_cost"], totals["total"]) == (5500, 15500)


def test_calculate_cart_totals_missing_regional_config_fails_closed(
    cart_item_factory, product_factory, user
):
    """Sin configuración regional aplicable, el envío queda no disponible."""
    product = product_factory(price=10000)
    cart_item_factory(cart=user.cart, product=product, quantity=1)
    comuna = ComunaFactory(region=RegionFactory(name="Valparaiso"))

    totals = calculate_cart_totals(user.cart, comuna_selector=comuna.id)

    assert totals["shipping_cost"] is None and totals["total"] is None
