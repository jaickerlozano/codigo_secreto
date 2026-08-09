import time
from unittest import mock

import pytest
from django.core import signing
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status

from apps.orders.models import Order, OrderItem
from apps.orders.services import calculate_guest_quote, load_guest_quote_revision

pytestmark = pytest.mark.django_db


def items(*pairs):
    return [{"product_id": product_id, "quantity": quantity} for product_id, quantity in pairs]


def payload(value, comuna=None):
    data = {"items": value}
    if comuna is not None:
        data["comuna"] = comuna
    return data


def test_calculator_is_sorted_authoritative_and_query_bounded(product_factory, comuna_factory, django_assert_num_queries):
    first = product_factory(name="First", price=1200)
    second = product_factory(name="Second", price=3500)
    comuna = comuna_factory(shipping_cost=2400)
    with django_assert_num_queries(2):
        quote = calculate_guest_quote(items((second.id, 2), (first.id, 3)), comuna_selector=comuna.id)
    assert [line.product_id for line in quote.items] == [first.id, second.id]
    assert [line.line_total for line in quote.items] == [3600, 7000]
    assert (quote.subtotal, quote.shipping_cost, quote.total) == (10600, 2400, 13000)
    assert quote.revision.startswith("gq1.")


@pytest.mark.parametrize("value", [[], items((1, 0)), items((1, 1), (1, 2)), items((999999, 1)), items((1, "1"))])
def test_quote_rejects_invalid_item_sets(api_client, value):
    response = api_client.post("/api/orders/quote/", payload(value), format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"code": "invalid_quote", "detail": "Unable to create quote."}


def test_quote_rejects_client_prices_and_over_50_items(api_client, product_factory):
    product = product_factory(price=1000)
    priced = api_client.post("/api/orders/quote/", payload([{"product_id": product.id, "quantity": 1, "price": 1}]), format="json")
    top_level = api_client.post("/api/orders/quote/", {"items": items((product.id, 1)), "price": 1}, format="json")
    oversized = api_client.post("/api/orders/quote/", payload(items(*[(product.id + i, 1) for i in range(51)])), format="json")
    assert {priced.status_code, top_level.status_code, oversized.status_code} == {status.HTTP_400_BAD_REQUEST}


def test_quote_optional_comuna_and_create_parity(api_client, product_factory, comuna_factory):
    product = product_factory(price=2200)
    comuna = comuna_factory(shipping_cost=1900)
    item_list = items((product.id, 2))
    subtotal = api_client.post("/api/orders/quote/", payload(item_list), format="json")
    quote = api_client.post("/api/orders/quote/", payload(item_list, comuna.id), format="json")
    created = api_client.post("/api/orders/", {
        "guest_email": "guest@example.com", "guest_name": "Guest", "phone": "+56912345678",
        "comuna": comuna.id, "shipping_address": "Street 1", "guest_items": item_list,
        "confirmed_revision": quote.json()["revision"],
    }, format="json")
    assert subtotal.status_code == quote.status_code == status.HTTP_200_OK
    assert subtotal.json()["subtotal"] == 4400 and "total" not in subtotal.json()
    assert created.status_code == status.HTTP_201_CREATED
    assert tuple(created.json()[key] for key in ("subtotal", "shipping_cost", "total")) == tuple(
        quote.json()[key] for key in ("subtotal", "shipping_cost", "total")
    )


def test_quote_has_no_persistence_side_effects(api_client, product_factory, comuna_factory):
    product = product_factory(price=1000)
    comuna = comuna_factory(shipping_cost=3000)
    before = (Order.objects.count(), OrderItem.objects.count())
    response = api_client.post("/api/orders/quote/", payload(items((product.id, 2)), comuna.id), format="json")
    assert response.status_code == status.HTTP_200_OK
    assert (Order.objects.count(), OrderItem.objects.count()) == before


def test_revision_round_trip_tamper_expiry_and_fallback_keys(product_factory):
    product = product_factory(price=1000)
    revision = calculate_guest_quote(items((product.id, 1))).revision
    assert load_guest_quote_revision(revision)["version"] == "gq1"
    with pytest.raises(signing.BadSignature):
        load_guest_quote_revision(revision[:-1] + "x")
    with mock.patch("django.core.signing.time.time", return_value=time.time() + 901):
        with pytest.raises(signing.SignatureExpired):
            load_guest_quote_revision(revision)
    with override_settings(SECRET_KEY="old-secret"):
        old_revision = calculate_guest_quote(items((product.id, 1))).revision
    with override_settings(SECRET_KEY="new-secret", SECRET_KEY_FALLBACKS=["old-secret"]):
        assert load_guest_quote_revision(old_revision)["version"] == "gq1"


def test_revision_is_canonical_for_input_order(product_factory):
    first = product_factory(price=1000)
    second = product_factory(price=2000)
    assert calculate_guest_quote(items((first.id, 1), (second.id, 2))).revision == calculate_guest_quote(
        items((second.id, 2), (first.id, 1))
    ).revision


def test_quote_endpoint_is_allow_any_and_throttled(api_client, product_factory):
    product = product_factory(price=1000)
    cache.clear()
    responses = [api_client.post("/api/orders/quote/", payload(items((product.id, 1))), format="json") for _ in range(31)]
    assert responses[0].status_code == status.HTTP_200_OK
    assert responses[-1].status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_quote_schema_is_explicitly_annotated():
    from drf_spectacular.generators import SchemaGenerator
    operation = SchemaGenerator().get_schema(request=None, public=True)["paths"]["/api/orders/quote/"]["post"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/GuestQuoteResponse"
    assert {"400", "429"} <= set(operation["responses"])
