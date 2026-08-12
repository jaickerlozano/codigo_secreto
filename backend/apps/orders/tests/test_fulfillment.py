"""Fulfillment dispatch lifecycle and durable notification delivery (Unit 6, task 2.4).

Staff dispatch requires carrier and estimated date (tracking optional), invalid
fulfillment leaves state unchanged, and payment/dispatch emails are sent only
after valid transitions with failure containment and Admin retry.
"""
from datetime import date
from unittest import mock

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import TestCase

from apps.orders.admin import NotificationDeliveryAdmin, OrderAdmin
from apps.orders.models import NotificationDelivery, Order
from apps.orders.notifications import attempt_delivery, retry_delivery
from apps.orders.services import InvalidFulfillmentError, fulfill_dispatch

pytestmark = pytest.mark.django_db

DISPATCH_ARGS = {"carrier": "Chilexpress", "estimated_delivery_date": date(2026, 8, 20)}


@pytest.fixture(autouse=True)
def _clear_mail_outbox():
    mail.outbox.clear()


@pytest.fixture
def order_admin():
    return OrderAdmin(Order, AdminSite())


@pytest.fixture
def admin_request(rf):
    request = rf.get("/admin/orders/order/")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


class TestFulfillDispatch:
    @pytest.mark.parametrize("guest", [False, True])
    def test_dispatch_transitions_to_shipped_and_sends_accurate_email_after_commit(self, order_factory, guest):
        kwargs = {"status": "PAID", "total": 10000}
        kwargs.update({"user": None, "guest_email": "guest@example.com"} if guest else {})
        order = order_factory(**kwargs)

        with TestCase.captureOnCommitCallbacks(execute=True):
            order = fulfill_dispatch(order=order, tracking_number="TRK-1", **DISPATCH_ARGS)

        assert (order.status, order.dispatched_at is not None) == ("SHIPPED", True)
        assert (order.carrier, order.estimated_delivery_date, order.tracking_number) == (
            "Chilexpress", date(2026, 8, 20), "TRK-1")
        delivery = NotificationDelivery.objects.get(order=order, event="dispatch")
        assert delivery.status == "SENT"
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == (["guest@example.com"] if guest else [order.user.email])
        assert order.order_number in mail.outbox[0].subject
        assert "Chilexpress" in mail.outbox[0].body
        assert "20/08/2026" in mail.outbox[0].body

    @pytest.mark.parametrize("kwargs", [{"carrier": ""}, {"estimated_delivery_date": None}])
    def test_dispatch_requires_carrier_and_estimated_date(self, paid_order, kwargs):
        with pytest.raises(InvalidFulfillmentError):
            fulfill_dispatch(order=paid_order, **dict(DISPATCH_ARGS, **kwargs))

        paid_order.refresh_from_db()
        assert paid_order.status == "PAID"
        assert not NotificationDelivery.objects.filter(order=paid_order).exists()

    @pytest.mark.parametrize("status", ["PENDING", "SHIPPED", "CANCELLED"])
    def test_dispatch_rejects_orders_not_in_preparation(self, order_factory, status):
        order = order_factory(status=status, total=10000)
        with pytest.raises(InvalidFulfillmentError):
            fulfill_dispatch(order=order, **DISPATCH_ARGS)

        order.refresh_from_db()
        assert order.status == status and not NotificationDelivery.objects.filter(order=order).exists()

    def test_email_failure_is_contained_and_retry_resends(self, paid_order):
        order = fulfill_dispatch(order=paid_order, **DISPATCH_ARGS)
        delivery = NotificationDelivery.objects.get(order=order, event="dispatch")
        with mock.patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("SMTP down")):
            attempt_delivery(delivery.id)
        delivery.refresh_from_db()
        assert (delivery.status, delivery.attempts) == ("FAILED", 1)
        assert "SMTP down" in delivery.last_error
        assert delivery.next_retry_at is not None
        order.refresh_from_db()
        assert order.status == "SHIPPED"  # domain state persists despite the failure

        retry_delivery(delivery.id)
        delivery.refresh_from_db()
        assert (delivery.status, delivery.attempts, delivery.sent_at is not None) == ("SENT", 2, True)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [paid_order.user.email]

        retry_delivery(delivery.id)  # retry skips already-sent deliveries
        delivery.refresh_from_db()
        assert (delivery.status, delivery.attempts) == ("SENT", 2)
        assert len(mail.outbox) == 1


class TestFulfillmentAdmin:
    @pytest.mark.parametrize("prepared", [True, False])
    def test_admin_dispatch_action_dispatches_or_reports(self, paid_order, order_admin, admin_request, prepared):
        if prepared:
            paid_order.carrier = "Chilexpress"
            paid_order.estimated_delivery_date = date(2026, 8, 20)
            paid_order.save(update_fields=["carrier", "estimated_delivery_date"])

        order_admin.dispatch_orders(admin_request, Order.objects.filter(id=paid_order.id))

        paid_order.refresh_from_db()
        if prepared:
            assert paid_order.status == "SHIPPED" and paid_order.dispatched_at is not None
            assert NotificationDelivery.objects.filter(order=paid_order, event="dispatch").exists()
        else:
            assert paid_order.status == "PAID"
            assert any("No se pudo despachar" in str(message.message) for message in admin_request._messages)

    def test_admin_retry_action_resends_failed_notifications(self, paid_order, admin_request):
        fulfill_dispatch(order=paid_order, **DISPATCH_ARGS)
        delivery = NotificationDelivery.objects.get(order=paid_order, event="dispatch")
        with mock.patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("SMTP down")):
            attempt_delivery(delivery.id)

        NotificationDeliveryAdmin(NotificationDelivery, AdminSite()).retry_failed(
            admin_request, NotificationDelivery.objects.filter(id=delivery.id))

        delivery.refresh_from_db()
        assert delivery.status == "SENT"
        assert len(mail.outbox) == 1
