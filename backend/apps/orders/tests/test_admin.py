from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.apps import apps
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.tests.factories import UserFactory
from apps.orders.tests.factories import OrderFactory
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


class AdminPendingCancellationTests(TestCase):
    """Use the authorized manage.py test runner with synthetic admin sessions."""

    def setUp(self):
        self.staff = UserFactory(is_staff=True, is_superuser=True)
        self.order = OrderFactory(status="PENDING")
        self.reservation = apps.get_model("products", "InventoryReservation").objects.create(
            order_id=self.order.pk, status="ACTIVE", expires_at=timezone.now() + timedelta(minutes=15),
        )
        self.client.force_login(self.staff)
        self.change_url = reverse("admin:orders_order_change", args=[self.order.pk])
        self.cancel_url = reverse("admin:orders_order_cancel", args=[self.order.pk])
        self.model_admin = admin.site._registry[Order]

    def test_detail_controls_follow_status_and_object_change_permission(self):
        for state in ("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"):
            with self.subTest(state=state):
                Order.objects.filter(pk=self.order.pk).update(status=state)
                response = self.client.get(self.change_url)
                content = response.content.decode()
                self.assertEqual("Cancelar pedido" in content, state == "PENDING")
                self.assertEqual("Guardar y despachar" in content, state == "PAID")
                self.assertEqual("Marcar como entregado" in content, state == "SHIPPED")
        Order.objects.filter(pk=self.order.pk).update(status="PENDING")
        with patch.object(self.model_admin, "has_change_permission", return_value=False):
            self.assertNotContains(self.client.get(self.change_url), "Cancelar pedido")
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(self.cancel_url, {"_confirm_cancel": "1"}).status_code, 403)

    def test_staff_needs_change_permission_and_anonymous_or_nonstaff_cannot_cancel(self):
        self.staff.is_superuser = False
        self.staff.save(update_fields=["is_superuser"])
        Permission = apps.get_model("auth", "Permission")
        self.staff.user_permissions.add(Permission.objects.get(codename="view_order"))
        self.assertNotContains(self.client.get(self.change_url), "Cancelar pedido")
        for method in (self.client.get, self.client.post):
            self.assertEqual(method(self.cancel_url, {"_confirm_cancel": "1"}).status_code, 403)
        self.staff.user_permissions.add(Permission.objects.get(codename="change_order"))
        self.assertContains(self.client.get(self.change_url), "Cancelar pedido")
        self.assertEqual(self.client.get(self.cancel_url).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.post(self.cancel_url, {"_confirm_cancel": "1"}).status_code, 302)
        self.client.force_login(UserFactory(is_staff=False))
        self.assertEqual(self.client.post(self.cancel_url, {"_confirm_cancel": "1"}).status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "ACTIVE")

    def test_missing_object_is_404_and_non_mutating_methods_are_enforced(self):
        missing = reverse("admin:orders_order_cancel", args=[self.order.pk + 999])
        self.assertEqual(self.client.get(missing).status_code, 404)
        self.assertEqual(self.client.post(missing, {"_confirm_cancel": "1"}).status_code, 404)
        self.assertEqual(self.client.put(self.cancel_url).status_code, 405)
        self.assertContains(self.client.post(self.cancel_url, {}), "Confirmar cancelación")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")

    def test_csrf_is_required_on_confirmation_post(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        self.assertContains(client.get(self.cancel_url), "csrfmiddlewaretoken")
        self.assertEqual(client.post(self.cancel_url, {"_confirm_cancel": "1"}).status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")
        response = client.post(self.cancel_url, {
            "_confirm_cancel": "1", "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertRedirects(response, self.change_url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "CANCELLED")

    def test_forged_nonpending_posts_and_stale_paid_confirmation_are_rejected(self):
        self.assertContains(self.client.get(self.cancel_url), "Confirmar cancelación")
        for state in ("PAID", "SHIPPED", "DELIVERED", "CANCELLED"):
            with self.subTest(state=state):
                Order.objects.filter(pk=self.order.pk).update(status=state)
                response = self.client.post(self.cancel_url, {"_confirm_cancel": "1"}, follow=True)
                self.assertContains(response, "Solo se pueden cancelar pedidos pendientes")
                self.order.refresh_from_db()
                self.assertEqual(self.order.status, state)
                self.reservation.refresh_from_db()
                self.assertEqual(self.reservation.status, "ACTIVE")
                self.assertIsNone(self.reservation.transitioned_at)
        self.assertFalse(LogEntry.objects.filter(object_id=str(self.order.pk)).exists())

    def test_locked_service_rechecks_state_after_admin_read(self):
        stale = self.order
        Order.objects.filter(pk=self.order.pk).update(status="PAID")
        with patch.object(self.model_admin, "get_object", return_value=stale):
            response = self.client.post(self.cancel_url, {"_confirm_cancel": "1"})
        self.assertRedirects(response, self.change_url, fetch_redirect_response=False)
        self.assertContains(self.client.get(self.change_url), "el pedido ya no está pendiente")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PAID")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "ACTIVE")
        self.assertFalse(LogEntry.objects.filter(object_id=str(self.order.pk)).exists())

    @staticmethod
    def form_data(response, **updates):
        data = {field.html_name: field.value() or "" for field in response.context["adminform"].form}
        for inline in response.context["inline_admin_formsets"]:
            data.update({field.html_name: field.value() for field in inline.formset.management_form})
            for form in inline.formset.forms:
                data.update({field.html_name: field.value() or "" for field in form})
        return dict(data, **updates)

    def test_detail_dispatch_and_delivery_still_save_and_transition(self):
        Order.objects.filter(pk=self.order.pk).update(status="PAID")
        data = self.form_data(self.client.get(self.change_url), carrier="Chilexpress",
                              estimated_delivery_date="2026-08-20", _save_and_dispatch="1")
        response = self.client.post(self.change_url, data)
        self.assertEqual(response.status_code, 302, response.context["errors"] if response.status_code == 200 else "")
        self.assertRedirects(response, self.change_url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "SHIPPED")
        self.assertIsNotNone(self.order.dispatched_at)
        data = self.form_data(self.client.get(self.change_url), _mark_delivered="1")
        self.assertRedirects(self.client.post(self.change_url, data), self.change_url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "DELIVERED")
        self.assertIsNotNone(self.order.delivered_at)
        Notification = apps.get_model("orders", "NotificationDelivery")
        self.assertEqual(Notification.objects.filter(order=self.order).count(), 2)

    def test_bulk_dispatch_and_delivery_still_work(self):
        Order.objects.filter(pk=self.order.pk).update(status="PAID", estimated_delivery_date=date(2026, 8, 20))
        for action, state in (("dispatch_orders", "SHIPPED"), ("mark_orders_delivered", "DELIVERED")):
            response = self.client.post(reverse("admin:orders_order_changelist"), {
                "action": action, "_selected_action": [str(self.order.pk)], "index": "0", "select_across": "0",
            })
            self.assertEqual(response.status_code, 302)
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, state)
