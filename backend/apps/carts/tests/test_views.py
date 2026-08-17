import pytest
from rest_framework import status

from apps.carts.models import CartItem
from apps.shipping.tests.factories import ComunaFactory, RegionFactory


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cart_payload(product_id, quantity):
    """Return a JSON payload for cart add/remove operations."""
    return {"product_id": product_id, "quantity": quantity}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def test_cart_unauthenticated(api_client):
    """GET /api/cart/me/ without authentication returns 401."""
    response = api_client.get("/api/cart/me/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# GET cart
# ---------------------------------------------------------------------------


def test_get_cart_empty(authenticated_client, user):
    """GET /api/cart/me/ returns an empty cart for an authenticated user."""
    response = authenticated_client.get("/api/cart/me/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["monto_total_final"] == 0
    assert data["subtotal"] == 0
    assert data["shipping_cost"] == 0
    assert data["total"] == 0
    assert data["free_shipping_progress"] == 0
    assert data["free_shipping_threshold"] == 30000


def test_get_cart_authenticated(authenticated_client, cart_with_items):
    """GET /api/cart/me/ returns the cart with its items and calculated totals."""
    response = authenticated_client.get("/api/cart/me/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["monto_total_final"] == 22000
    assert data["subtotal"] == 22000
    assert data["shipping_cost"] == 3000
    assert data["total"] == 25000
    assert data["free_shipping_progress"] == pytest.approx((22000 / 30000) * 100)
    assert data["free_shipping_threshold"] == 30000


def test_get_cart_estimate_for_selected_comuna(authenticated_client, cart_with_items):
    """GET /api/cart/me/?comuna={id} prices the estimate with the comuna authority."""
    comuna = ComunaFactory(shipping_cost=3500)

    data = authenticated_client.get(f"/api/cart/me/?comuna={comuna.id}").json()

    assert data["shipping_cost"] == 3500
    assert data["total"] == data["subtotal"] + 3500


def test_get_cart_estimate_unavailable_delivery_fails_closed(
    authenticated_client, cart_with_items
):
    """Sin configuración regional aplicable, el estimado queda no disponible."""
    comuna = ComunaFactory(region=RegionFactory(name="Valparaiso"))

    data = authenticated_client.get(f"/api/cart/me/?comuna={comuna.id}").json()

    assert data["shipping_cost"] is None and data["total"] is None


def test_get_cart_rejects_non_numeric_comuna_param(authenticated_client, cart_with_items):
    """Un parámetro comuna no numérico se rechaza sin estimar."""
    response = authenticated_client.get("/api/cart/me/?comuna=abc")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# POST add
# ---------------------------------------------------------------------------


def test_add_new_product(authenticated_client, user, product_factory):
    """POST /api/cart/me/ adds a new product to the cart."""
    product = product_factory(price=10000)
    payload = _cart_payload(product.id, 2)

    response = authenticated_client.post("/api/cart/me/", payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["monto_total_final"] == 20000
    assert data["subtotal"] == 20000
    assert data["shipping_cost"] == 3000
    assert data["total"] == 23000
    assert data["free_shipping_threshold"] == 30000


def test_add_existing_product(authenticated_client, cart_factory, cart_item_factory, product_factory, user):
    """POST /api/cart/me/ accumulates quantity atomically via F() expression."""
    cart = cart_factory(user=user)
    product = product_factory()
    cart_item_factory(cart=cart, product=product, quantity=2)

    response = authenticated_client.post(
        "/api/cart/me/",
        _cart_payload(product.id, 3),
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    item = cart.items.get(product=product)
    item.refresh_from_db()
    assert item.quantity == 5


def test_add_nonexistent_product(authenticated_client):
    """POST /api/cart/me/ with an invalid product_id returns 400."""
    response = authenticated_client.post(
        "/api/cart/me/",
        _cart_payload(99999, 1),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no existe" in response.json()["product_id"][0]


def test_add_zero_quantity(authenticated_client, product_factory):
    """POST /api/cart/me/ with quantity=0 is rejected."""
    product = product_factory()
    response = authenticated_client.post(
        "/api/cart/me/",
        _cart_payload(product.id, 0),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "quantity" in response.json()


# ---------------------------------------------------------------------------
# DELETE remove
# ---------------------------------------------------------------------------


def test_remove_partial_quantity(authenticated_client, cart_factory, cart_item_factory, product_factory, user):
    """DELETE /api/cart/me/ subtracts quantity and keeps the item."""
    cart = cart_factory(user=user)
    product = product_factory()
    cart_item_factory(cart=cart, product=product, quantity=5)

    response = authenticated_client.delete(
        "/api/cart/me/",
        _cart_payload(product.id, 2),
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    item = cart.items.get(product=product)
    item.refresh_from_db()
    assert item.quantity == 3


def test_remove_full_quantity(authenticated_client, cart_factory, cart_item_factory, product_factory, user):
    """DELETE /api/cart/me/ removes the item when quantity reaches zero."""
    cart = cart_factory(user=user)
    product = product_factory()
    cart_item_factory(cart=cart, product=product, quantity=3)

    response = authenticated_client.delete(
        "/api/cart/me/",
        _cart_payload(product.id, 3),
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert not CartItem.objects.filter(cart=cart, product=product).exists()


def test_remove_more_than_existing_quantity(authenticated_client, cart_factory, cart_item_factory, product_factory, user):
    """DELETE /api/cart/me/ removes the item when subtracting more than existing."""
    cart = cart_factory(user=user)
    product = product_factory()
    cart_item_factory(cart=cart, product=product, quantity=2)

    response = authenticated_client.delete(
        "/api/cart/me/",
        _cart_payload(product.id, 10),
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert not CartItem.objects.filter(cart=cart, product=product).exists()


def test_remove_nonexistent_item(authenticated_client, product_factory):
    """DELETE /api/cart/me/ for a product not in the cart returns 400."""
    product = product_factory()

    response = authenticated_client.delete(
        "/api/cart/me/",
        _cart_payload(product.id, 1),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no se encuentra" in response.json()["detail"]
