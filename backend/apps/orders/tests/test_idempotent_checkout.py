import hashlib

import pytest
from django.core.cache import cache
from rest_framework import status

from apps.orders.models import Order
from apps.orders.services import calculate_guest_quote


pytestmark = pytest.mark.django_db

KEY = "checkout-session-abc123"


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    """Start each test with a clean throttle window (suite convention)."""
    cache.clear()
    yield


def _post(client, payload, key=None):
    return client.post("/api/orders/", payload, format="json",
                       **({"HTTP_IDEMPOTENCY_KEY": key} if key else {}))


def _guest_payload(product, comuna, quantity=2):
    return {"guest_email": "guest@example.com", "guest_name": "Invitado",
            "phone": "+56912345678", "comuna": comuna.id, "shipping_address": "Calle 123",
            "shipping_cost": comuna.shipping_cost,
            "guest_items": [{"product_id": product.id, "quantity": quantity}],
            "confirmed_revision": calculate_guest_quote(
                [{"product_id": product.id, "quantity": quantity}], comuna_selector=comuna.id
            ).revision}


def test_guest_replay_returns_same_order_and_rotates_capability(api_client, product_factory, comuna_factory):
    """A retry with the same key and purchase intent returns the existing order."""
    product = product_factory(price=1000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _guest_payload(product, comuna)

    first, second = _post(api_client, payload, KEY), _post(api_client, payload, KEY)

    assert first.status_code == second.status_code == status.HTTP_201_CREATED
    assert first.json()["id"] == second.json()["id"]
    order = Order.objects.get(id=first.json()["id"])
    assert order.checkout_key == KEY
    assert Order.objects.count() == 1 and order.items.count() == 1 and order.items.get().quantity == 2
    first_token, second_token = first.json()["guest_access"]["token"], second.json()["guest_access"]["token"]
    assert second_token != first_token and order.guest_access_version == 2
    assert order.guest_access_digest == hashlib.sha256(second_token.encode()).hexdigest()
    assert not order.verify_guest_access(first_token)


def test_guest_replay_with_stale_revision_returns_frozen_order(api_client, product_factory, comuna_factory):
    """Replay is key-identified: the frozen order wins over a stale revision."""
    product = product_factory(price=1000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _guest_payload(product, comuna, quantity=2)
    first = _post(api_client, payload, KEY)
    assert first.status_code == status.HTTP_201_CREATED

    product.price = 2500
    product.save(update_fields=["price"])
    retry = _post(api_client, payload, KEY)

    assert retry.status_code == status.HTTP_201_CREATED
    assert retry.json()["id"] == first.json()["id"]
    order = Order.objects.get(id=first.json()["id"])
    assert (order.subtotal, order.shipping_cost, order.total) == (2000, 3000, 5000)
    assert Order.objects.count() == 1


def test_conflicting_key_reuse_fails_safely(api_client, product_factory, comuna_factory):
    """Same key with a different purchase intent fails without duplicates."""
    product = product_factory(price=1000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)
    first_payload = _guest_payload(product, comuna, quantity=2)
    conflict_payload = _guest_payload(product, comuna, quantity=3)

    first = _post(api_client, first_payload, KEY)
    assert first.status_code == status.HTTP_201_CREATED
    conflict = _post(api_client, conflict_payload, KEY)

    assert conflict.status_code == status.HTTP_409_CONFLICT
    assert set(conflict.json()) == {"code", "detail"}
    assert Order.objects.count() == 1
    assert Order.objects.get(id=first.json()["id"]).items.get().quantity == 2


def test_invalid_idempotency_key_rejected(api_client, product_factory, comuna_factory):
    """An unusable key fails closed instead of silently disabling idempotency."""
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)

    response = _post(api_client, _guest_payload(product, comuna), "k" * 65)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "idempotency" in str(response.json()["detail"]).lower()
    assert Order.objects.count() == 0
