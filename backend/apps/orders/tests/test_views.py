import hashlib

import pytest
from django.utils import timezone
from rest_framework import status

from apps.orders.models import Order
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


def test_create_order_allow_any(api_client, product_factory, comuna_factory):
    """POST /api/orders/ is accessible without authentication for guests."""
    product = product_factory(price=1000)
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
    assert "order_number" in data
    assert data["order_number"].startswith("CS-")
    assert data["guest_access"]["token"]
    order = Order.objects.get(id=data["id"])
    assert order.guest_access_digest == hashlib.sha256(data["guest_access"]["token"].encode()).hexdigest()


def test_create_order_by_comuna_name(api_client, product_factory, comuna_factory):
    """Guest checkout can resolve the comuna by name + region instead of ID."""
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)
    revision = calculate_guest_quote(
        [{"product_id": product.id, "quantity": 1}], comuna_selector=comuna.id
    ).revision

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
            "confirmed_revision": revision,
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


def _exchange(client, order, token):
    return client.post(
        f"/api/orders/by-order-number/{order.order_number}/access/",
        {}, format="json", HTTP_X_ORDER_CAPABILITY=token,
    )


def _use_guest_cookie(client, response):
    client.cookies['guest_order_access'] = response.cookies['guest_order_access'].value


def test_secure_guest_access_boundaries(api_client, order_factory):
    order, foreign = order_factory(user=None), order_factory(user=None)
    assert api_client.get(f"/api/orders/by-order-number/{order.order_number}/").status_code == 404
    raw = order.issue_guest_access()
    exchange = _exchange(api_client, order, raw)
    cookie = exchange.cookies['guest_order_access']
    assert exchange.status_code == 204 and cookie['httponly'] and cookie['samesite'] == 'Strict'
    assert raw not in cookie.value
    _use_guest_cookie(api_client, exchange)
    assert api_client.get(f"/api/orders/by-order-number/{order.order_number}/").status_code == 200
    order.revoke_guest_access()
    assert api_client.get(f"/api/orders/by-order-number/{order.order_number}/").status_code == 404
    foreign_raw = foreign.issue_guest_access()
    for bad in ('wrong', 'malformed', foreign_raw):
        assert _exchange(api_client, order, bad).status_code == 404
    query = api_client.post(
        f"/api/orders/by-order-number/{order.order_number}/access/?capability={foreign_raw}", {}, format='json'
    )
    path = api_client.post(
        f"/api/orders/by-order-number/{order.order_number}/access/{foreign_raw}/", {}, format='json'
    )
    assert query.status_code == path.status_code == 404
    for state in ('expired', 'revoked'):
        candidate = order_factory(user=None)
        token = candidate.issue_guest_access()
        if state == 'expired':
            candidate.guest_access_expires_at = timezone.now() - timezone.timedelta(seconds=1)
            candidate.save(update_fields=['guest_access_expires_at'])
        else:
            candidate.revoke_guest_access()
        assert _exchange(api_client, candidate, token).status_code == 404


def test_owner_and_staff_can_retrieve_order_by_number(authenticated_client, staff_client, order_factory, user):
    own, staff_order = order_factory(user=user), order_factory()
    assert authenticated_client.get(f"/api/orders/by-order-number/{own.order_number}/").status_code == 200
    assert staff_client.get(f"/api/orders/by-order-number/{staff_order.order_number}/").status_code == 200


def test_authenticated_user_can_retrieve_own_order_by_order_number(authenticated_client, order_factory, user):
    """Authenticated users can retrieve their own orders by order_number."""
    order = order_factory(user=user)

    response = authenticated_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order_number"] == order.order_number


def test_authenticated_user_cannot_retrieve_other_order_by_order_number(authenticated_client, order_factory):
    """Authenticated users cannot retrieve orders that belong to someone else."""
    order = order_factory()

    response = authenticated_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Not found.'}


def test_guest_cannot_retrieve_authenticated_order_by_order_number(api_client, order_factory, user):
    """A guest cannot retrieve an authenticated order by number alone."""
    order = order_factory(user=user)

    response = api_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not found."}


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

    raw_token = order.issue_guest_access()
    exchange = api_client.post(
        f"/api/orders/by-order-number/{order.order_number}/access/",
        {},
        format="json",
        HTTP_X_ORDER_CAPABILITY=raw_token,
    )
    api_client.cookies["guest_order_access"] = exchange.cookies["guest_order_access"].value
    response = api_client.get(f"/api/orders/by-order-number/{order.order_number}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["comuna_name"] == comuna.name
    assert data["region_name"] == comuna.region.name
