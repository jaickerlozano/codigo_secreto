import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status

from apps.orders.tests.conftest import reset_order_throttle_cache
from apps.shipping.services import future_dispatch_dates


pytestmark = pytest.mark.django_db


def test_order_throttle_reset_removes_prior_test_history(
    authenticated_client,
    cart_factory,
    cart_item_factory,
    comuna_factory,
    product_factory,
    user,
):
    product = product_factory(price=1000)
    cart = cart_factory(user=user)
    cart_item_factory(cart=cart, product=product, quantity=1)
    comuna = comuna_factory(shipping_cost=3000)
    cache.set(
        f"throttle_order_create_{user.pk}",
        [timezone.now().timestamp()] * 10,
        timeout=3600,
    )

    reset_order_throttle_cache()

    response = authenticated_client.post(
        "/api/orders/",
        {
            "phone": "+56912345678",
            "comuna": comuna.id,
            "shipping_address": "Calle 123",
            "shipping_cost": comuna.shipping_cost,
            "delivery_kind": "standard",
            "requested_dispatch_date": str(future_dispatch_dates()[0]),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
