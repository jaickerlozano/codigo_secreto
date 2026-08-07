import pytest
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import authorize_order_access

pytestmark = pytest.mark.django_db


def test_authorize_owner_returns_order(order_factory, user):
    order = order_factory(user=user)
    result = authorize_order_access(order.order_number, user=user)
    assert isinstance(result, Order)
    assert result.id == order.id


def test_authorize_staff_returns_any_order(order_factory, staff_user):
    order = order_factory()
    assert authorize_order_access(order.order_number, user=staff_user).id == order.id


def test_authorize_valid_capability_returns_order(order_factory):
    order = order_factory(user=None)
    raw = order.issue_guest_access()
    assert authorize_order_access(order.order_number, capability=raw).id == order.id


def test_authorize_missing_order_returns_none():
    assert authorize_order_access("CS-NONEXISTENT", user=None) is None


def test_authorize_no_user_no_capability_returns_none(order_factory):
    order = order_factory(user=None)
    assert authorize_order_access(order.order_number, user=None) is None


def test_authorize_authenticated_non_owner_returns_none(order_factory, user):
    order = order_factory()
    assert authorize_order_access(order.order_number, user=user) is None


def test_authorize_wrong_capability_returns_none(order_factory):
    order = order_factory(user=None)
    order.issue_guest_access()
    assert authorize_order_access(order.order_number, capability="wrong-token") is None


def test_authorize_expired_capability_returns_none(order_factory):
    order = order_factory(user=None)
    raw = order.issue_guest_access()
    order.guest_access_issued_at = timezone.now() - timezone.timedelta(days=91)
    order.guest_access_expires_at = order.guest_access_issued_at + timezone.timedelta(days=90)
    order.save()
    assert authorize_order_access(order.order_number, capability=raw) is None


def test_authorize_revoked_capability_returns_none(order_factory):
    order = order_factory(user=None)
    raw = order.issue_guest_access()
    order.revoke_guest_access()
    assert authorize_order_access(order.order_number, capability=raw) is None


def test_authorize_capability_on_owned_order_ignored(order_factory, user):
    order = order_factory(user=user)
    raw = order.issue_guest_access()
    assert authorize_order_access(order.order_number, capability=raw, user=None) is None
