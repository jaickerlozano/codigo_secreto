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
from django.urls import reverse

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
    @pytest.fixture
    def admin_client(self, client, paid_order):
        staff = paid_order.user
        staff.is_staff = True
        staff.is_superuser = True
        staff.save(update_fields=["is_staff", "is_superuser"])
        client.force_login(staff)
        return client

    @staticmethod
    def change_form_data(response, **updates):
        data = {}
        for field in response.context["adminform"].form:
            data[field.html_name] = field.value() or ""
        for inline_formset in response.context["inline_admin_formsets"]:
            for field in inline_formset.formset.management_form:
                data[field.html_name] = field.value()
            for form in inline_formset.formset.forms:
                for field in form:
                    data[field.html_name] = field.value() or ""
        data.update(updates)
        return data

    @staticmethod
    def change_url(order):
        return reverse("admin:orders_order_change", args=[order.id])

    @pytest.mark.parametrize("status,visible", [("PAID", True), ("PENDING", False), ("SHIPPED", False)])
    def test_change_form_shows_dispatch_submit_only_for_paid_orders(self, paid_order, order_factory, admin_client, status, visible):
        order = order_factory(status=status, user=paid_order.user)

        response = admin_client.get(self.change_url(order))

        assert ("Guardar y despachar" in response.content.decode()) is visible

    def test_change_form_hides_dispatch_submit_from_unauthorized_users(self, paid_order, client):
        response = client.get(self.change_url(paid_order), follow=True)

        assert response.status_code == 200
        assert "Guardar y despachar" not in response.content.decode()

    def test_change_form_saves_metadata_then_dispatches_once(self, paid_order, admin_client):
        response = admin_client.get(self.change_url(paid_order))
        data = self.change_form_data(
            response,
            carrier="Chilexpress",
            estimated_delivery_date="2026-08-20",
            _save_and_dispatch="Guardar y despachar",
        )

        with TestCase.captureOnCommitCallbacks(execute=True):
            response = admin_client.post(self.change_url(paid_order), data, follow=True)

        paid_order.refresh_from_db()
        assert response.status_code == 200
        assert (paid_order.status, paid_order.dispatched_at is not None) == ("SHIPPED", True)
        assert (response.context["original"].status, response.context["original"].dispatched_at is not None) == ("SHIPPED", True)
        assert NotificationDelivery.objects.filter(order=paid_order, event="dispatch").count() == 1
        assert "guardado y despachado correctamente" in response.content.decode()

    def test_regular_save_updates_metadata_without_dispatching(self, paid_order, admin_client):
        response = admin_client.get(self.change_url(paid_order))
        data = self.change_form_data(response, estimated_delivery_date="2026-08-20", _save="Guardar")

        admin_client.post(self.change_url(paid_order), data)

        paid_order.refresh_from_db()
        assert paid_order.status == "PAID"
        assert paid_order.estimated_delivery_date == date(2026, 8, 20)
        assert not NotificationDelivery.objects.filter(order=paid_order, event="dispatch").exists()

    @pytest.mark.parametrize(
        "updates,error",
        [
            ({"carrier": "", "estimated_delivery_date": "2026-08-20"}, "transportista es obligatorio"),
            ({"carrier": "Chilexpress", "estimated_delivery_date": ""}, "fecha estimada de entrega es obligatoria"),
        ],
    )
    def test_change_form_rejects_invalid_dispatch_metadata(self, paid_order, admin_client, updates, error):
        response = admin_client.get(self.change_url(paid_order))
        data = self.change_form_data(response, **updates, _save_and_dispatch="Guardar y despachar")

        response = admin_client.post(self.change_url(paid_order), data, follow=True)

        paid_order.refresh_from_db()
        assert paid_order.status == "PAID"
        assert not NotificationDelivery.objects.filter(order=paid_order, event="dispatch").exists()
        assert error in response.content.decode()

    def test_change_form_duplicate_submission_keeps_single_dispatch_notification(self, paid_order, admin_client):
        response = admin_client.get(self.change_url(paid_order))
        data = self.change_form_data(
            response,
            carrier="Chilexpress",
            estimated_delivery_date="2026-08-20",
            _save_and_dispatch="Guardar y despachar",
        )

        with TestCase.captureOnCommitCallbacks(execute=True):
            admin_client.post(self.change_url(paid_order), data)
            response = admin_client.post(self.change_url(paid_order), data, follow=True)

        paid_order.refresh_from_db()
        assert paid_order.status == "SHIPPED"
        assert NotificationDelivery.objects.filter(order=paid_order, event="dispatch").count() == 1
        assert "no está listo para despacho" in response.content.decode()

    def test_change_form_email_failure_preserves_shipment_and_failed_notification(self, paid_order, admin_client):
        response = admin_client.get(self.change_url(paid_order))
        data = self.change_form_data(
            response,
            carrier="Chilexpress",
            estimated_delivery_date="2026-08-20",
            _save_and_dispatch="Guardar y despachar",
        )

        with mock.patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("SMTP down")):
            with TestCase.captureOnCommitCallbacks(execute=True):
                admin_client.post(self.change_url(paid_order), data)

        paid_order.refresh_from_db()
        delivery = NotificationDelivery.objects.get(order=paid_order, event="dispatch")
        assert paid_order.status == "SHIPPED"
        assert (delivery.status, delivery.attempts, delivery.next_retry_at is not None) == ("FAILED", 1, True)

    def test_bulk_dispatch_action_remains_available(self, paid_order, admin_client):
        paid_order.carrier = "Chilexpress"
        paid_order.estimated_delivery_date = date(2026, 8, 20)
        paid_order.save(update_fields=["carrier", "estimated_delivery_date"])

        with TestCase.captureOnCommitCallbacks(execute=True):
            response = admin_client.post(
                reverse("admin:orders_order_changelist"),
                {
                    "action": "dispatch_orders",
                    "_selected_action": [str(paid_order.id)],
                    "index": "0",
                    "select_across": "0",
                },
                follow=True,
            )

        paid_order.refresh_from_db()
        assert response.status_code == 200
        assert paid_order.status == "SHIPPED"
        assert NotificationDelivery.objects.filter(order=paid_order, event="dispatch").count() == 1

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
