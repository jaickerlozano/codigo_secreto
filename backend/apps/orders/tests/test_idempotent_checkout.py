import hashlib
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.tests.factories import UserFactory
from apps.orders.models import Order, OrderItem
from apps.orders.services import CheckoutKeyConflictError, _race_replay_auth, calculate_guest_quote
from apps.products.models import InventoryReservation
from apps.shipping.services import DeliverySnapshot, future_dispatch_dates


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
            ).revision,
            "delivery_kind": "standard",
            "requested_dispatch_date": str(future_dispatch_dates()[0])}


def _auth_payload(comuna):
    return {"phone": "+56912345678", "comuna": comuna.id,
            "shipping_address": "Calle 123", "shipping_cost": comuna.shipping_cost,
            "delivery_kind": "standard",
            "requested_dispatch_date": str(future_dispatch_dates()[0])}


def test_auth_replay_returns_same_order_and_preserves_cart(
        authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    """An authenticated retry with the same key and cart intent returns the existing order."""
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=10)
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _auth_payload(comuna)

    first, second = _post(authenticated_client, payload, KEY), _post(authenticated_client, payload, KEY)

    assert first.status_code == second.status_code == status.HTTP_201_CREATED
    assert first.json()["id"] == second.json()["id"]
    order = Order.objects.get(id=first.json()["id"])
    assert order.checkout_key == KEY and order.user == user
    assert Order.objects.count() == 1 and order.items.count() == 1 and order.items.get().quantity == 2
    assert InventoryReservation.objects.filter(order_id=order.id).count() == 1
    assert (order.subtotal, order.shipping_cost, order.total) == (2000, 3000, 5000)
    cart.refresh_from_db()
    assert cart.items.count() == 1
    assert second.json()["guest_access"] is None


def test_auth_replay_returns_frozen_totals(
        authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    """A replay never re-prices: the frozen order wins over a live price change."""
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=10)
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _auth_payload(comuna)

    first = _post(authenticated_client, payload, KEY)
    assert first.status_code == status.HTTP_201_CREATED

    product.price = 2500
    product.save(update_fields=["price"])
    retry = _post(authenticated_client, payload, KEY)

    assert retry.status_code == status.HTTP_201_CREATED
    assert retry.json()["id"] == first.json()["id"]
    order = Order.objects.get(id=first.json()["id"])
    assert (order.subtotal, order.shipping_cost, order.total) == (2000, 3000, 5000)
    assert Order.objects.count() == 1


@pytest.mark.parametrize("conflict", ["other_owner", "changed_cart"])
def test_auth_conflicting_key_reuse_fails_safely(
        authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory, conflict):
    """Same key with another owner or a different cart intent fails without duplicates or leaks."""
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=10)
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _auth_payload(comuna)

    first = _post(authenticated_client, payload, KEY)
    assert first.status_code == status.HTTP_201_CREATED

    if conflict == "other_owner":
        other_client = APIClient()
        other_client.force_authenticate(user=UserFactory.create())
        response = _post(other_client, payload, KEY)
    else:
        cart_item_factory(cart=cart, product=product_factory(price=500), quantity=1)
        response = _post(authenticated_client, payload, KEY)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert set(response.json()) == {"code", "detail"}
    assert Order.objects.count() == 1
    assert Order.objects.get(id=first.json()["id"]).items.get().quantity == 2


def test_auth_race_replay_resolves_or_conflicts(
        user, cart_factory, cart_item_factory, product_factory, comuna_factory):
    """The IntegrityError fallback re-fetches the winner and verifies owner and intent."""
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=10)
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=3000)
    winner = Order.objects.create(user=user, checkout_key=KEY, comuna_id=comuna.id,
                                  phone="+56912345678", shipping_address="Calle 123",
                                  subtotal=2000, shipping_cost=3000, total=5000)
    OrderItem.objects.create(order=winner, product_id=product.id, product_name=product.name,
                             price=1000, quantity=2)

    delivery = DeliverySnapshot("standard", None, "Chilexpress", 3000)
    assert _race_replay_auth(KEY, user.id, comuna.id, cart.items.all(), delivery).id == winner.id
    with pytest.raises(CheckoutKeyConflictError):
        _race_replay_auth(KEY, UserFactory.create().id, comuna.id, cart.items.all(), delivery)
    assert Order.objects.count() == 1


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
    assert InventoryReservation.objects.filter(order_id=order.id).count() == 1
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

def test_checkout_reserves_atomically_and_rejects_unavailable_inventory(
        authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=2, supplier__phone="56912345678")
    cart_item_factory(cart=cart, product=product, quantity=2)
    comuna = comuna_factory(shipping_cost=3000)

    created = _post(authenticated_client, _auth_payload(comuna), KEY)

    assert created.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=created.json()["id"])
    reservation = InventoryReservation.objects.get(order_id=order.id)
    assert reservation.status == "ACTIVE"
    assert timedelta(minutes=14) < reservation.expires_at - order.created_at <= timedelta(minutes=15, seconds=1)

    other = UserFactory.create()
    other_cart = cart_factory(user=other)
    cart_item_factory(cart=other_cart, product=product, quantity=1)
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    rejected = _post(other_client, _auth_payload(comuna), "inventory-shortage")

    assert rejected.status_code == status.HTTP_409_CONFLICT
    assert Order.objects.count() == InventoryReservation.objects.count() == 1


def test_expired_key_retains_failed_order_then_replaces_after_revalidation(
        authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory):
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=1, supplier__phone="56912345678")
    cart_item_factory(cart=cart, product=product, quantity=1)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _auth_payload(comuna)
    first = _post(authenticated_client, payload, KEY)
    old = Order.objects.get(id=first.json()["id"])
    InventoryReservation.objects.filter(order_id=old.id).update(expires_at=timezone.now() - timedelta(seconds=1))
    product.current_stock = 0
    product.save(update_fields=["current_stock"])

    rejected = _post(authenticated_client, payload, KEY)

    old.refresh_from_db()
    old_reservation = InventoryReservation.objects.get(order_id=old.id)
    assert rejected.status_code == status.HTTP_409_CONFLICT
    assert (old.status, old.checkout_key) == ("CANCELLED", KEY)
    assert (old_reservation.status, old_reservation.release_reason) == ("RELEASED", "EXPIRED")
    assert Order.objects.count() == InventoryReservation.objects.count() == 1

    product.current_stock = 1
    product.save(update_fields=["current_stock"])
    replacement = _post(authenticated_client, payload, KEY)

    old.refresh_from_db()
    new = Order.objects.get(id=replacement.json()["id"])
    assert replacement.status_code == status.HTTP_201_CREATED
    assert (old.status, old.checkout_key) == ("CANCELLED", None)
    assert new.id != old.id and new.checkout_key == KEY
    assert InventoryReservation.objects.get(order_id=new.id).status == "ACTIVE"
