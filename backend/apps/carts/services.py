"""Servicios de cálculo financiero para el carrito de compras.

Toda la lógica monetaria del carrito vive en el backend para respetar la
regla de oro: el frontend solo debe mostrar valores, nunca calcularlos.
"""

from typing import TypedDict

from apps.shipping.services import ShippingSnapshotResolutionError, resolve_shipping_price

class CartTotals(TypedDict):
    """Valores calculados para un carrito."""

    subtotal: int
    shipping_cost: int | None
    total: int | None
    free_shipping_progress: float
    free_shipping_threshold: int


def calculate_cart_totals(cart, comuna_selector=None) -> CartTotals:
    """Calcula todos los valores monetarios de un carrito.

    A selected eligible comuna is required to quote shipping. Its positive
    ``shipping_cost`` is the sole price authority; no cart threshold or
    regional dispatch profile can modify it.
    """
    subtotal = sum(item.subtotal for item in cart.items.all())
    if subtotal == 0:
        shipping_cost = 0
    elif comuna_selector is not None:
        try:
            shipping = resolve_shipping_price(comuna_id=comuna_selector)
        except ShippingSnapshotResolutionError:
            shipping = None
        shipping_cost = shipping.price if shipping is not None else None
    else:
        shipping_cost = None
    total = subtotal + shipping_cost if shipping_cost is not None else None

    return CartTotals(
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        free_shipping_progress=0.0,
        free_shipping_threshold=0,
    )
