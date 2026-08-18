"""Unit D — order dispatch validation and snapshot (issue #78): Santiago
standard-date eligibility, regional option id, special dates, stale/ineligible
rejection, snapshot, and preserved price/quote/ownership/idempotency."""
from datetime import timedelta
from unittest import mock

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status

from apps.orders.models import Order
from apps.orders.services import calculate_guest_quote
from apps.shipping.services import (
    SHIPPING_AUTHORITY_COMUNA,
    ShippingPriceSnapshot,
    future_dispatch_dates,
)
from apps.shipping.tests.factories import RegionFactory, RegionalShippingOptionFactory


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def _future_dispatch_date():
    return future_dispatch_dates()[0]  # next future Tuesday/Thursday


def _future_non_dispatch_date():
    candidate = timezone.localdate() + timedelta(days=1)
    while candidate.weekday() in (1, 3):
        candidate += timedelta(days=1)
    return candidate


def _auth_payload(comuna, **overrides):
    payload = {"phone": "+56912345678", "comuna": comuna.id, "shipping_address": "Calle 123"}
    payload.update(overrides)
    return payload


def _seed_cart(cart_factory, cart_item_factory, product_factory, user):
    cart = cart_factory(user=user)
    product = product_factory(price=1000, current_stock=10)
    cart_item_factory(cart=cart, product=product, quantity=1)


def test_santiago_standard_date_is_snapshotted(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    dispatch_date = _future_dispatch_date()
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(dispatch_date)),
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert order.delivery_kind == "standard"
    assert order.requested_dispatch_date == dispatch_date
    assert order.carrier == "Chilexpress"
    assert order.shipping_cost == 3000


@pytest.mark.parametrize(
    "dispatch_date_factory",
    [
        lambda: timezone.localdate(),                      # today
        lambda: timezone.localdate() - timedelta(days=1),  # past
        _future_non_dispatch_date,                          # non-Tuesday/Thursday
    ],
    ids=["today", "past", "non_dispatch_weekday"],
)
def test_santiago_standard_ineligible_dates_are_rejected(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory, dispatch_date_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(dispatch_date_factory())),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "delivery_schedule_ineligible"
    assert Order.objects.count() == 0


def test_santiago_special_future_date_is_snapshotted(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    special_date = _future_non_dispatch_date()
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="special", requested_dispatch_date=str(special_date)),
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert order.delivery_kind == "special"
    assert order.requested_dispatch_date == special_date
    assert order.special_delivery_agreed_at is None


def test_santiago_special_past_date_is_rejected(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(
            comuna, delivery_kind="special",
            requested_dispatch_date=str(timezone.localdate() - timedelta(days=1)),
        ),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "delivery_schedule_ineligible"
    assert Order.objects.count() == 0


def test_santiago_rejects_regional_shipping_option(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(
            comuna, delivery_kind="standard",
            requested_dispatch_date=str(_future_dispatch_date()), shipping_option_id=1,
        ),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "delivery_schedule_ineligible"
    assert Order.objects.count() == 0


def test_regional_shipping_option_snapshots_carrier(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)
    option = RegionalShippingOptionFactory(key="regional", carrier="CS Logistics", tariff=5500)
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", shipping_option_id=option.id),
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert order.delivery_kind == "standard"
    assert order.requested_dispatch_date is None
    assert order.carrier == "CS Logistics"
    assert order.shipping_cost == 5500


def test_regional_stale_shipping_option_is_conflict(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)
    RegionalShippingOptionFactory(key="regional", carrier="CS Logistics", tariff=5500)
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", shipping_option_id=99999),
        format="json",
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["code"] == "delivery_option_stale"
    assert Order.objects.count() == 0


def test_regional_rejects_requested_dispatch_date(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)
    RegionalShippingOptionFactory(key="regional", carrier="CS Logistics", tariff=5500)
    response = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(_future_dispatch_date())),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "delivery_schedule_ineligible"
    assert Order.objects.count() == 0


def test_guest_special_date_is_snapshotted_with_quote_identity(api_client, product_factory, comuna_factory):
    product = product_factory(price=1000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)
    special_date = _future_non_dispatch_date()
    response = api_client.post(
        "/api/orders/",
        {
            "guest_email": "guest@example.com",
            "guest_name": "Invitado",
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "guest_items": [{"product_id": product.id, "quantity": 1}],
            "confirmed_revision": calculate_guest_quote(
                [{"product_id": product.id, "quantity": 1}], comuna_selector=comuna.id
            ).revision,
            "delivery_kind": "special",
            "requested_dispatch_date": str(special_date),
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert order.user is None
    assert order.guest_email == "guest@example.com"
    assert order.delivery_kind == "special"
    assert order.requested_dispatch_date == special_date
    assert order.total == 4000


def test_replay_same_delivery_intent_returns_frozen_order(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    payload = _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(_future_dispatch_date()))
    first = authenticated_client.post("/api/orders/", payload, format="json", HTTP_IDEMPOTENCY_KEY="dispatch-replay-key")
    second = authenticated_client.post("/api/orders/", payload, format="json", HTTP_IDEMPOTENCY_KEY="dispatch-replay-key")
    assert first.status_code == second.status_code == status.HTTP_201_CREATED
    assert first.json()["id"] == second.json()["id"]
    assert Order.objects.count() == 1
    order = Order.objects.get(id=first.json()["id"])
    assert order.delivery_kind == "standard"
    assert order.requested_dispatch_date is not None


# --- Correction: mandatory delivery selection (gap 1) ---


def test_santiago_standard_missing_date_is_rejected(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    response = authenticated_client.post(
        "/api/orders/", _auth_payload(comuna, delivery_kind="standard"), format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "delivery_schedule_ineligible"
    assert Order.objects.count() == 0


def test_regional_missing_option_is_rejected(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)
    RegionalShippingOptionFactory(key="regional", carrier="CS Logistics", tariff=5500)
    response = authenticated_client.post(
        "/api/orders/", _auth_payload(comuna, delivery_kind="standard"), format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "delivery_schedule_ineligible"
    assert Order.objects.count() == 0


# --- Correction: delivery-intent idempotency (gap 2) ---


def test_changed_delivery_kind_conflicts(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    first = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(_future_dispatch_date())),
        format="json", HTTP_IDEMPOTENCY_KEY="dispatch-kind-key",
    )
    assert first.status_code == status.HTTP_201_CREATED
    conflict = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="special", requested_dispatch_date=str(_future_non_dispatch_date())),
        format="json", HTTP_IDEMPOTENCY_KEY="dispatch-kind-key",
    )
    assert conflict.status_code == status.HTTP_409_CONFLICT
    assert conflict.json()["code"] == "checkout_key_conflict"
    assert Order.objects.count() == 1


def test_changed_dispatch_date_conflicts(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=3000)
    first, second = future_dispatch_dates()[:2]
    first_resp = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(first)),
        format="json", HTTP_IDEMPOTENCY_KEY="dispatch-date-key",
    )
    assert first_resp.status_code == status.HTTP_201_CREATED
    conflict = authenticated_client.post(
        "/api/orders/",
        _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(second)),
        format="json", HTTP_IDEMPOTENCY_KEY="dispatch-date-key",
    )
    assert conflict.status_code == status.HTTP_409_CONFLICT
    assert conflict.json()["code"] == "checkout_key_conflict"
    assert Order.objects.count() == 1


def test_changed_regional_option_carrier_conflicts(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(region=RegionFactory(name="Valparaiso"), shipping_cost=9000)
    option = RegionalShippingOptionFactory(key="regional", carrier="CS Logistics", tariff=5500)
    payload = _auth_payload(comuna, delivery_kind="standard", shipping_option_id=option.id)
    first = authenticated_client.post(
        "/api/orders/", payload, format="json", HTTP_IDEMPOTENCY_KEY="dispatch-option-key"
    )
    assert first.status_code == status.HTTP_201_CREATED
    option.carrier = "DHL"
    option.save(update_fields=["carrier"])
    conflict = authenticated_client.post(
        "/api/orders/", payload, format="json", HTTP_IDEMPOTENCY_KEY="dispatch-option-key"
    )
    assert conflict.status_code == status.HTTP_409_CONFLICT
    assert conflict.json()["code"] == "checkout_key_conflict"
    assert Order.objects.count() == 1


# --- Correction: locked price snapshot (gap 3) ---


def test_authenticated_order_uses_locked_price_not_prelock(
    authenticated_client, cart_factory, cart_item_factory, product_factory, user, comuna_factory
):
    _seed_cart(cart_factory, cart_item_factory, product_factory, user)
    comuna = comuna_factory(shipping_cost=5000)
    stale = ShippingPriceSnapshot(price=3000, comuna_id=comuna.id, authority=SHIPPING_AUTHORITY_COMUNA)
    with mock.patch("apps.orders.serializers.resolve_shipping_price", return_value=stale):
        response = authenticated_client.post(
            "/api/orders/",
            _auth_payload(comuna, delivery_kind="standard", requested_dispatch_date=str(_future_dispatch_date())),
            format="json",
        )
    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert order.shipping_cost == 5000
    assert order.total == 1000 + 5000
