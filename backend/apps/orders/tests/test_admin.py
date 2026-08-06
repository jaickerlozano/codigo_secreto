import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.orders.admin import OrderAdmin
from apps.orders.models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def order_admin():
    return OrderAdmin(Order, AdminSite())


@pytest.fixture
def admin_request(rf):
    request = rf.get("/admin/orders/order/")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


def test_admin_revoke_action_sets_revoked_at(order_factory, order_admin, admin_request):
    order = order_factory(user=None)
    order.issue_guest_access()
    order_admin.revoke_guest_access(admin_request, Order.objects.filter(id=order.id))
    order.refresh_from_db()
    assert order.guest_access_revoked_at is not None


def test_admin_rotate_action_issues_new_token(order_factory, order_admin, admin_request):
    order = order_factory(user=None)
    old_raw = order.issue_guest_access()
    order_admin.rotate_guest_access(admin_request, Order.objects.filter(id=order.id))
    order.refresh_from_db()
    assert order.verify_guest_access(old_raw) is False
    assert order.guest_access_version == 2
