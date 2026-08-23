import hashlib
import secrets
from datetime import date

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone

from apps.orders.models import Order, OrderItem


pytestmark = pytest.mark.django_db


def test_order_total_calculation(order_factory, order_item_factory):
    """subtotal + shipping_cost = total."""
    order = order_factory(subtotal=0, shipping_cost=3000, total=3000)
    order_item_factory(order=order, quantity=2, price=1000)
    order_item_factory(order=order, quantity=1, price=5000)

    order.subtotal = sum(item.subtotal for item in order.items.all())
    order.total = order.subtotal + order.shipping_cost
    order.save()
    order.refresh_from_db()

    assert order.subtotal == 7000  # (2*1000) + (1*5000)
    assert order.total == 10000  # 7000 + 3000


def test_order_item_subtotal(order_item_factory, product_factory):
    """OrderItem.subtotal equals quantity multiplied by frozen price."""
    product = product_factory(price=3500)
    item = order_item_factory(product=product, quantity=3, price=3500)

    assert item.subtotal == 10500


@pytest.mark.parametrize(
    ("price", "quantity"),
    [(None, 3), (3500, None), (None, None)],
)
def test_order_item_subtotal_is_unavailable_when_frozen_value_is_missing(
    order_item_factory, price, quantity
):
    """Historical incomplete snapshots do not produce a fabricated subtotal."""
    item = order_item_factory.build(price=price, quantity=quantity)

    assert item.subtotal is None


def test_order_str(order_factory):
    """Order.__str__ includes the order id, status and total."""
    order = order_factory(total=15000)

    expected = f"Pedido #{order.id} - Pendiente de Pago ($15,000)"
    assert str(order) == expected


def test_order_item_str(order_factory, order_item_factory, product_factory):
    """OrderItem.__str__ includes quantity, product name and order id."""
    product = product_factory(name="Vibrador X")
    order = order_factory()
    item = order_item_factory(order=order, product=product, product_name="Vibrador X", quantity=2)

    expected = f"2 x Vibrador X (Pedido #{order.id})"
    assert str(item) == expected


def test_order_default_status(order_factory):
    """New orders default to PENDING status."""
    order = order_factory()

    assert order.status == "PENDING"


def test_user_delete_preserves_order(order_factory, user):
    """Deleting a user sets order.user to NULL (SET_NULL)."""
    order = order_factory(user=user)

    user.delete()
    order.refresh_from_db()

    assert order.user is None
    assert Order.objects.filter(id=order.id).exists()


def test_comuna_delete_protected(order_factory):
    """Deleting a comuna with related orders raises ProtectedError."""
    order = order_factory()

    with pytest.raises(ProtectedError):
        order.comuna.delete()


def test_guest_access_token_issued_once(order_factory):
    """Issuing a guest access token returns a raw value and persists its digest."""
    order = order_factory()
    raw = order.issue_guest_access()
    order.refresh_from_db()
    assert raw and len(raw) >= 32
    assert order.guest_access_digest is not None
    assert order.guest_access_version == 1
    assert order.guest_access_expires_at > order.guest_access_issued_at


def test_guest_access_digest_is_sha256_hex(order_factory):
    """Stored digest is the SHA-256 hex digest of the raw token."""
    order = order_factory()
    raw = order.issue_guest_access()
    order.refresh_from_db()
    expected = hashlib.sha256(raw.encode()).hexdigest()
    assert order.guest_access_digest == expected
    assert len(order.guest_access_digest) == 64


def test_guest_access_verifies_with_constant_time(order_factory):
    """Correct token verifies; wrong token fails without leaking via timing."""
    order = order_factory()
    raw = order.issue_guest_access()
    assert order.verify_guest_access(raw) is True
    assert order.verify_guest_access(raw + "x") is False
    assert order.verify_guest_access("") is False


def test_guest_access_expires_after_90_days(order_factory):
    """A token older than 90 days is rejected."""
    order = order_factory()
    raw = order.issue_guest_access()
    order.guest_access_issued_at = timezone.now() - timezone.timedelta(days=91)
    order.guest_access_expires_at = order.guest_access_issued_at + timezone.timedelta(days=90)
    order.save()
    assert order.verify_guest_access(raw) is False


def test_guest_access_revocation(order_factory):
    """Revoked token is rejected even if not expired."""
    order = order_factory()
    raw = order.issue_guest_access()
    order.revoke_guest_access()
    order.refresh_from_db()
    assert order.guest_access_revoked_at is not None
    assert order.verify_guest_access(raw) is False


def test_guest_access_rotation_bumps_version(order_factory):
    """Rotation revokes the current token and issues a new one with a higher version."""
    order = order_factory()
    old_raw = order.issue_guest_access()
    new_raw = order.rotate_guest_access()
    order.refresh_from_db()
    assert new_raw != old_raw
    assert order.guest_access_version == 2
    assert order.verify_guest_access(old_raw) is False
    assert order.verify_guest_access(new_raw) is True


def test_order_checkout_key_unique(order_factory):
    """Two orders with the same checkout_key are rejected."""
    order_factory(checkout_key="checkout-1")

    with pytest.raises(IntegrityError):
        order_factory(checkout_key="checkout-1")


def test_order_checkout_key_may_be_null_or_distinct(order_factory):
    """Orders without a checkout_key or with distinct keys are allowed."""
    first = order_factory(checkout_key=None)
    second = order_factory(checkout_key=None)
    third = order_factory(checkout_key="checkout-2")

    ids = {first.id, second.id, third.id}
    assert Order.objects.filter(id__in=ids).count() == 3
    assert first.checkout_key is None
    assert third.checkout_key == "checkout-2"


def test_order_delivery_fields_defaults(order_factory):
    """New orders default to standard delivery with no dispatch data."""
    order = order_factory()
    order.refresh_from_db()

    assert order.delivery_kind == "standard"
    assert order.requested_dispatch_date is None
    assert order.special_delivery_agreed_at is None
    assert order.estimated_delivery_date is None
    assert order.dispatched_at is None


def test_order_special_delivery_fields_roundtrip(order_factory):
    """Special delivery request date and agreement timestamp persist."""
    order = order_factory(
        delivery_kind="special",
        requested_dispatch_date=date(2026, 8, 25),
        special_delivery_agreed_at=timezone.now(),
    )
    order.refresh_from_db()

    assert order.delivery_kind == "special"
    assert order.requested_dispatch_date == date(2026, 8, 25)
    assert order.special_delivery_agreed_at is not None


def test_order_dispatch_fields_roundtrip(order_factory):
    """Dispatch record fields persist for staff fulfillment."""
    dispatch_time = timezone.now()
    order = order_factory(
        estimated_delivery_date=date(2026, 8, 28),
        dispatched_at=dispatch_time,
    )
    order.refresh_from_db()

    assert order.estimated_delivery_date == date(2026, 8, 28)
    assert order.dispatched_at == dispatch_time
