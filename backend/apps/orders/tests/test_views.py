import pytest
from rest_framework import status

from apps.orders.models import Order


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


def test_create_order_allow_any(api_client, product_factory, comuna_factory):
    """POST /api/orders/ is accessible without authentication for guests."""
    product = product_factory(price=1000)
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
            "guest_items": [{"product_id": product.id, "quantity": 2}],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "order_number" in data
    assert data["order_number"].startswith("CS-")


def test_create_order_by_comuna_name(api_client, product_factory, comuna_factory):
    """Guest checkout can resolve the comuna by name + region instead of ID."""
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)

    response = api_client.post(
        "/api/orders/",
        {
            "guest_email": "guest@example.com",
            "guest_name": "Invitado",
            "phone": "+56912345678",
            "comuna_name": comuna.name,
            "region_name": comuna.region.name,
            "shipping_address": "Calle 123",
            "payment_method": "mercadopago",
            "guest_items": [{"product_id": product.id, "quantity": 1}],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["comuna"] == comuna.id
    assert data["payment_method"] == "mercadopago"
    assert data["order_number"].startswith("CS-")


def _results(response):
    """Return the paginated results list from a DRF list response."""
    return response.json()["results"]


def test_list_orders_authenticated(authenticated_client, order_factory, user):
    """LIST /api/orders/ returns only the authenticated user's orders."""
    order1 = order_factory(user=user)
    order_factory()  # Other user

    response = authenticated_client.get("/api/orders/")

    assert response.status_code == status.HTTP_200_OK
    results = _results(response)
    assert len(results) == 1
    assert results[0]["id"] == order1.id


def test_list_orders_staff(staff_client, order_factory):
    """Staff users can see all orders in LIST /api/orders/."""
    order1 = order_factory()
    order2 = order_factory()

    response = staff_client.get("/api/orders/")

    assert response.status_code == status.HTTP_200_OK
    results = _results(response)
    assert len(results) == 2
    assert {item["id"] for item in results} == {order1.id, order2.id}


def test_list_orders_requires_authentication(api_client):
    """LIST /api/orders/ requires authentication."""
    response = api_client.get("/api/orders/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_own_order(authenticated_client, order_factory, user):
    """Authenticated users can retrieve their own orders."""
    order = order_factory(user=user)

    response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == order.id


def test_retrieve_other_order(authenticated_client, order_factory):
    """Authenticated users cannot retrieve orders that belong to someone else."""
    order = order_factory()

    response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_order_calculates_totals(authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    """Order total is calculated server-side from cart subtotal + comuna shipping cost."""
    cart = cart_factory(user=user)
    product = product_factory(price=10000)
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=5000)

    response = authenticated_client.post("/api/orders/", _order_payload(comuna), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["subtotal"] == 20000
    assert data["shipping_cost"] == 5000
    assert data["total"] == 25000
    assert data["payment_method"] == "webpay"


def test_order_clears_cart_after_creation(authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    """Authenticated checkout deletes all cart items after order creation."""
    cart = cart_factory(user=user)
    product = product_factory(price=5000)
    cart_item_factory(cart=cart, product=product, quantity=3)
    comuna = comuna_factory(shipping_cost=2000)

    response = authenticated_client.post("/api/orders/", _order_payload(comuna), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    cart.refresh_from_db()
    assert cart.items.count() == 0


def test_order_readonly_fields_ignored(authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    """Client-sent subtotal/total/status are ignored and recalculated server-side."""
    cart = cart_factory(user=user)
    product = product_factory(price=1000)
    cart_item_factory(cart=cart, product=product, quantity=1)
    comuna = comuna_factory(shipping_cost=3000)

    payload = _order_payload(comuna)
    payload["subtotal"] = 999999
    payload["total"] = 999999
    payload["status"] = "PAID"

    response = authenticated_client.post("/api/orders/", payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert order.subtotal == 1000
    assert order.total == 4000
    assert order.status == "PENDING"


def test_order_retrieve_shows_nested_items(authenticated_client, order_factory, order_item_factory, product_factory, user):
    """Order retrieve includes nested items with frozen name, price and subtotal."""
    product = product_factory(name="Lubricante Y", price=8000)
    order = order_factory(user=user)
    order_item_factory(order=order, product=product, product_name="Lubricante Y", price=8000, quantity=2)

    response = authenticated_client.get(f"/api/orders/{order.id}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_name"] == "Lubricante Y"
    assert item["price"] == 8000
    assert item["quantity"] == 2
    assert item["subtotal"] == 16000


def test_guest_can_retrieve_own_order_by_order_number(api_client, order_factory):
    """Guest users can retrieve their own guest orders by order_number."""
    order = order_factory(user=None, guest_email="guest@example.com", guest_name="Invitado")

    response = api_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["order_number"] == order.order_number
    assert data["guest_email"] == "guest@example.com"


def test_authenticated_user_can_retrieve_own_order_by_order_number(authenticated_client, order_factory, user):
    """Authenticated users can retrieve their own orders by order_number."""
    order = order_factory(user=user)

    response = authenticated_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order_number"] == order.order_number


def test_authenticated_user_cannot_retrieve_other_order_by_order_number(authenticated_client, order_factory):
    """Authenticated users cannot retrieve orders that belong to someone else."""
    order = order_factory()  # Different user

    response = authenticated_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_guest_cannot_retrieve_authenticated_order_by_order_number(api_client, order_factory, user):
    """Guest users cannot retrieve orders that require authentication."""
    order = order_factory(user=user)

    response = api_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_order_by_order_number_not_found(api_client):
    """Requesting a non-existent order_number returns 404."""
    response = api_client.get("/api/orders/by-order-number/CS-999999/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_order_by_order_number_includes_comuna_and_region_names(api_client, order_factory, comuna_factory):
    """Guest order retrieve by order_number includes comuna_name and region_name."""
    comuna = comuna_factory(name="Providencia", shipping_cost=3000)
    order = order_factory(
        user=None,
        guest_email="guest@example.com",
        guest_name="Invitado",
        comuna=comuna,
    )

    response = api_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["comuna_name"] == comuna.name
    assert data["region_name"] == comuna.region.name
