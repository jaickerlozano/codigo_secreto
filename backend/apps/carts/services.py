"""Servicios de cálculo financiero para el carrito de compras.

Toda la lógica monetaria del carrito vive en el backend para respetar la
regla de oro: el frontend solo debe mostrar valores, nunca calcularlos.
"""

from typing import TypedDict

from apps.shipping.services import ShippingSnapshotResolutionError, resolve_shipping_price

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------

FREE_SHIPPING_THRESHOLD = 30000  # CLP
FLAT_SHIPPING_RATE = 3000  # CLP


class CartTotals(TypedDict):
    """Valores calculados para un carrito."""

    subtotal: int
    shipping_cost: int | None
    total: int | None
    free_shipping_progress: float
    free_shipping_threshold: int


def calculate_shipping_cost(subtotal: int) -> int:
    """Devuelve el costo de envío en función del subtotal.

    - Carritos vacíos no pagan envío.
    - Subtotales mayores o iguales al umbral tienen envío gratis.
    - El resto paga una tarifa plana.
    """
    if subtotal == 0:
        return 0
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    return FLAT_SHIPPING_RATE


def calculate_cart_totals(cart, comuna_selector=None) -> CartTotals:
    """Calcula todos los valores monetarios de un carrito.

    Con comuna de destino, el envío se resuelve con la autoridad de precios
    exclusiva del backend (costo exacto de la comuna para Santiago, tarifa
    regional activa para el resto); sin configuración aplicable queda no
    disponible (``None``). Sin destino, se conserva la tarifa plana de la
    vista promocional del carrito.
    """
    subtotal = sum(item.subtotal for item in cart.items.all())
    if comuna_selector is None:
        shipping_cost = calculate_shipping_cost(subtotal)
    else:
        try:
            shipping = resolve_shipping_price(comuna_id=comuna_selector)
        except ShippingSnapshotResolutionError:
            shipping = None
        shipping_cost = shipping.price if shipping is not None else None
    total = subtotal + shipping_cost if shipping_cost is not None else None

    if FREE_SHIPPING_THRESHOLD > 0:
        progress = (subtotal / FREE_SHIPPING_THRESHOLD) * 100
    else:
        progress = 0.0

    if progress > 100:
        progress = 100.0

    return CartTotals(
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        free_shipping_progress=progress,
        free_shipping_threshold=FREE_SHIPPING_THRESHOLD,
    )
