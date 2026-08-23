import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.orders.admin import OrderAdmin
from apps.orders.models import Order, OrderItem

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


def test_admin_order_change_handles_historical_item_with_missing_frozen_values(
    order_factory, order_item_factory, staff_user, order_admin, admin_request, monkeypatch
):
    """The change page renders a blank subtotal for an anomalous stored snapshot."""
    order = order_factory()
    item = order_item_factory(order=order, price=1000, quantity=2)
    original_from_db = OrderItem.from_db.__func__

    def malformed_from_db(cls, db, field_names, values):
        instance = original_from_db(cls, db, field_names, values)
        if instance.pk == item.pk:
            instance.price = None
            instance.quantity = None
        return instance

    monkeypatch.setattr(OrderItem, "from_db", classmethod(malformed_from_db))
    admin_request.user = staff_user

    response = order_admin.change_view(admin_request, str(order.pk))

    assert response.status_code == 200
    response.render()
    assert 'class="field-subtotal"' in response.content.decode()
    assert "No disponible" in response.content.decode()
