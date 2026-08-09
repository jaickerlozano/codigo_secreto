import pytest
from rest_framework import status

from apps.orders.models import Order, OrderItem
from apps.orders.services import calculate_guest_quote


pytestmark = pytest.mark.django_db


def _order_payload(comuna, **overrides):
    """Return a base payload for POST /api/orders/."""
    payload = {
        "phone": "+56912345678",
        "comuna": comuna.id,
        "shipping_address": "Calle 123",
        "shipping_cost": comuna.shipping_cost,
    }
    payload.update(overrides)
    return payload


def test_create_order_authenticated(authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    """Ruta A: authenticated order created from cart clears the cart."""
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=10)
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=3000)

    response = authenticated_client.post("/api/orders/", _order_payload(comuna), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    cart.refresh_from_db()
    assert cart.items.count() == 0

    order = Order.objects.get(id=response.json()["id"])
    assert order.items.count() == 1
    assert order.total == 5000  # (2*1000) + 3000
    assert order.user == user
    assert response.json()["guest_access"] is None


def _detail_contains(response_data, substring):
    """Return True if ``substring`` appears in a string or list of strings."""
    detail = response_data.get("detail", [])
    if isinstance(detail, str):
        return substring in detail
    return any(substring in item for item in detail)


def test_create_order_empty_cart(authenticated_client, user, comuna_factory):
    """Ruta A: creating an order with an empty cart returns a validation error."""
    comuna = comuna_factory(shipping_cost=3000)

    response = authenticated_client.post("/api/orders/", _order_payload(comuna), format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert _detail_contains(response.json(), "carrito vacío")


def test_order_frozen_prices(order_factory, order_item_factory, product_factory):
    """Changing a Product price after ordering does not affect OrderItem."""
    product = product_factory(price=1000)
    order = order_factory()
    item = order_item_factory(order=order, product=product, price=1000, quantity=2)

    product.price = 2000
    product.save()

    item.refresh_from_db()
    assert item.price == 1000
    assert item.subtotal == 2000


def test_create_order_guest(api_client, product_factory, comuna_factory):
    """Ruta B: guest checkout creates an order from guest_items."""
    product = product_factory(price=1000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)
    revision = calculate_guest_quote(
        [{"product_id": product.id, "quantity": 2}], comuna_selector=comuna.id
    ).revision

    response = api_client.post(
        "/api/orders/",
        {
            "guest_email": "guest@example.com",
            "guest_name": "Invitado",
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "shipping_cost": 3000,
            "guest_items": [{"product_id": product.id, "quantity": 2}],
            "confirmed_revision": revision,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["guest_email"] == "guest@example.com"
    assert "order_number" in data
    assert data["order_number"].startswith("CS-")
    order = Order.objects.get(id=data["id"])
    assert order.user is None
    assert order.items.count() == 1
    assert order.total == 5000



def test_guest_missing_email(api_client, comuna_factory):
    """Ruta B: missing guest_email and guest_name returns a validation error."""
    comuna = comuna_factory(shipping_cost=3000)

    response = api_client.post(
        "/api/orders/",
        {
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "shipping_cost": 3000,
            "guest_items": [],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert _detail_contains(response.json(), "correo y el nombre son obligatorios")


def test_guest_missing_items(api_client, comuna_factory):
    """Ruta B: missing guest_items returns a validation error."""
    comuna = comuna_factory(shipping_cost=3000)

    response = api_client.post(
        "/api/orders/",
        {
            "guest_email": "guest@example.com",
            "guest_name": "Invitado",
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "shipping_cost": 3000,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "guest_items" in response.json()


def test_guest_invalid_product(api_client, comuna_factory):
    """Ruta B: invalid product_id in guest_items returns a validation error."""
    comuna = comuna_factory(shipping_cost=3000)

    response = api_client.post(
        "/api/orders/",
        {
            "guest_email": "guest@example.com",
            "guest_name": "Invitado",
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "shipping_cost": 3000,
            "guest_items": [{"product_id": 99999, "quantity": 1}],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "guest_items" in response.json()


def test_guest_rejects_zero_quantity(api_client, product_factory, comuna_factory):
    """Guest creation rejects non-positive quantities atomically."""
    product = product_factory(price=5000)
    comuna = comuna_factory(shipping_cost=2000)

    response = api_client.post(
        "/api/orders/",
        {
            "guest_email": "guest@example.com",
            "guest_name": "Invitado",
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "shipping_cost": 2000,
            "guest_items": [
                {"product_id": product.id, "quantity": 0},
                {"product_id": product.id, "quantity": 1},
            ],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Order.objects.count() == 0
