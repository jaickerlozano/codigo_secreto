from unittest import mock

import pytest
from django.core import signing
from django.core.cache import cache
from django.db import connection
from drf_spectacular.generators import SchemaGenerator
from rest_framework import status

from apps.orders.models import Order, OrderItem
from apps.orders.services import calculate_guest_quote
from apps.products.services import resolve_product_price_snapshot as resolve_products
from apps.shipping.services import resolve_shipping_price as resolve_shipping
from apps.shipping.services import future_dispatch_dates


pytestmark = pytest.mark.django_db


def _items(*pairs):
    return [{"product_id": product_id, "quantity": quantity} for product_id, quantity in pairs]


def _guest_payload(comuna, guest_items, **extra):
    payload = {
        "guest_email": "guest@example.com",
        "guest_name": "Guest",
        "phone": "+56912345678",
        "comuna": comuna.id,
        "shipping_address": "Street 1",
        "guest_items": guest_items,
        "delivery_kind": "standard",
        "requested_dispatch_date": str(future_dispatch_dates()[0]),
    }
    payload.update(extra)
    return payload


def _revision(product, comuna, quantity=1):
    return calculate_guest_quote(
        _items((product.id, quantity)), comuna_selector=comuna.id
    ).revision


def test_matching_revision_creates_exact_quote_amounts(
    api_client, product_factory, comuna_factory
):
    product = product_factory(price=1500)
    comuna = comuna_factory(shipping_cost=2600)
    items = _items((product.id, 3))
    revision = _revision(product, comuna, quantity=3)

    response = api_client.post(
        "/api/orders/",
        _guest_payload(comuna, items, confirmed_revision=revision),
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    order = Order.objects.get(id=response.json()["id"])
    assert (order.subtotal, order.shipping_cost, order.total) == (4500, 2600, 7100)
    assert (order.items.get().price, order.items.get().quantity) == (1500, 3)


def test_price_drift_refuses_creation_without_side_effects(
    api_client, product_factory, comuna_factory
):
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)
    revision = _revision(product, comuna)
    product.price = 1800
    product.save(update_fields=["price"])
    before = (Order.objects.count(), OrderItem.objects.count())

    response = api_client.post(
        "/api/orders/",
        _guest_payload(comuna, _items((product.id, 1)), confirmed_revision=revision),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "quote_revision_stale"
    assert response.json()["refreshed_quote"]["items"][0]["unit_price"] == 1800
    assert (Order.objects.count(), OrderItem.objects.count()) == before
    assert not Order.objects.filter(guest_access_digest__isnull=False).exists()


def test_shipping_drift_refuses_creation_and_refreshes_shipping(
    api_client, product_factory, comuna_factory
):
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)
    revision = _revision(product, comuna)
    comuna.shipping_cost = 4500
    comuna.save(update_fields=["shipping_cost"])

    response = api_client.post(
        "/api/orders/",
        _guest_payload(comuna, _items((product.id, 1)), confirmed_revision=revision),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "quote_revision_stale"
    assert response.json()["refreshed_quote"]["shipping_cost"] == 4500
    assert Order.objects.count() == 0


@pytest.mark.parametrize(
    "revision_kind", ["missing", "malformed", "non_string", "input", "version"]
)
def test_invalid_revision_kinds_return_the_same_safe_contract(
    api_client, product_factory, comuna_factory, revision_kind
):
    product = product_factory(price=1000)
    other = product_factory(price=2000)
    comuna = comuna_factory(shipping_cost=3000)
    revision = _revision(product, comuna)
    revisions = {
        "missing": None,
        "malformed": "gq1.not-a-valid-signature",
        "non_string": 123,
        "input": _revision(other, comuna),
        "version": "gq2." + revision.split(".", 1)[1],
    }
    extra = {} if revisions[revision_kind] is None else {
        "confirmed_revision": revisions[revision_kind]
    }

    response = api_client.post(
        "/api/orders/",
        _guest_payload(comuna, _items((product.id, 1)), **extra),
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert set(body) == {"code", "detail", "refreshed_quote"}
    assert body["code"] == "quote_revision_stale"
    assert body["refreshed_quote"]["subtotal"] == 1000
    assert Order.objects.count() == 0


def test_expired_revision_returns_refreshed_quote(
    api_client, product_factory, comuna_factory
):
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)
    revision = _revision(product, comuna)

    with mock.patch("django.core.signing.time.time", return_value=signing.time.time() + 901):
        response = api_client.post(
            "/api/orders/",
            _guest_payload(comuna, _items((product.id, 1)), confirmed_revision=revision),
            format="json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "quote_revision_stale"
    assert Order.objects.count() == 0


def test_guest_creation_locks_products_before_shipping_inside_atomic(
    api_client, product_factory, comuna_factory
):
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)
    revision = _revision(product, comuna)
    cache.clear()
    calls = []

    def locked_products(*args, **kwargs):
        calls.append(("products", kwargs.get("for_update"), connection.in_atomic_block))
        return resolve_products(*args, **kwargs)

    def locked_shipping(*args, **kwargs):
        calls.append(("shipping", kwargs.get("for_update"), connection.in_atomic_block))
        return resolve_shipping(*args, **kwargs)

    with mock.patch("apps.orders.services.resolve_product_price_snapshot", locked_products), mock.patch(
        "apps.orders.services.resolve_shipping_price", locked_shipping
    ):
        response = api_client.post(
            "/api/orders/",
            _guest_payload(comuna, _items((product.id, 1)), confirmed_revision=revision),
            format="json",
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert calls == [("products", True, True), ("shipping", True, True)]


def test_creation_schema_describes_stale_quote_response():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/orders/"]["post"]
    response = operation["responses"]["400"]["content"]["application/json"]["schema"]
    assert response["$ref"] == "#/components/schemas/QuoteRevisionStale"
    assert schema["components"]["schemas"]["QuoteRevisionStale"]["properties"][
        "refreshed_quote"
    ]["$ref"] == "#/components/schemas/GuestQuoteResponse"
