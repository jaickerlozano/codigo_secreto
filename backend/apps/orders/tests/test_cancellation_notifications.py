"""Cancellation uses the durable pipeline without adding guest tracking access."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.apps import apps
from django.core import mail
from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication.tests.factories import UserFactory
from apps.orders.models import NotificationDelivery
from apps.orders.notifications import attempt_delivery, retry_delivery, schedule_delivery
from apps.orders.services import PendingCancellationError, cancel_pending_order
from apps.orders.tests.factories import OrderFactory, OrderItemFactory
from apps.products.services import InventoryReservationError, ReservationLineInput, reserve
from apps.products.tests.factories import ProductFactory


@pytest.fixture(autouse=True)
def locmem_email(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def _reserved_order(**kwargs):
    product = ProductFactory(current_stock=4)
    order = OrderFactory(**kwargs)
    OrderItemFactory(order=order, product=product, quantity=2)
    with transaction.atomic():
        reserve(order_id=order.id, lines=(ReservationLineInput(product.id, 2),),
                expires_at=timezone.now() + timedelta(minutes=15))
    return order, product


def _assert_released(order, product):
    order.refresh_from_db()
    product.refresh_from_db()
    reservation = apps.get_model("products", "InventoryReservation").objects.get(order_id=order.id)
    assert (order.status, reservation.status, reservation.release_reason) == ("CANCELLED", "RELEASED", "CANCELLED")
    assert product.current_stock == 4
    assert not apps.get_model("products", "StockMovement").objects.filter(product=product).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("guest", [True, False])
def test_customer_cancellation_sends_neutral_notice_only_after_commit(guest):
    user = None if guest else UserFactory(email="account@example.test")
    order, product = _reserved_order(user=user, guest_email="guest@example.test" if guest else None)
    token = order.issue_guest_access() if guest else None
    access_before = (order.guest_access_digest, order.guest_access_version, order.guest_email_access_version)
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    headers = {"HTTP_X_ORDER_CAPABILITY": token} if guest else {}
    url = f"/api/orders/by-order-number/{order.order_number}/cancel/"

    with patch("apps.orders.services.issue_guest_email_access_ticket") as issue_ticket:
        with transaction.atomic():
            response = client.post(url, {'cancellation_reason': 'EXPIRED', 'notify': False}, format="json", **headers)
            assert response.status_code == 200
            delivery = NotificationDelivery.objects.get(order=order, event="cancelled")
            assert (delivery.status, delivery.attempts) == ("PENDING", 0)
            assert not mail.outbox
        issue_ticket.assert_not_called()
    _assert_released(order, product)
    assert order.cancellation_reason == 'BUYER'
    delivery.refresh_from_db()
    assert (delivery.status, delivery.attempts) == ("SENT", 1)
    assert (order.guest_access_digest, order.guest_access_version, order.guest_email_access_version) == access_before
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["guest@example.test" if guest else "account@example.test"]
    assert message.subject == f"Tu pedido {order.order_number} fue cancelado"
    assert message.body == f"Hola, tu pedido {order.order_number} fue cancelado.\nEste pedido no será despachado."
    assert "#access=" not in message.body and "/order/" not in message.body
    assert client.post(url, {}, format="json", **headers).status_code == 409
    assert schedule_delivery(order, "cancelled").pk == delivery.pk
    attempt_delivery(delivery.pk, trigger="manual")
    assert NotificationDelivery.objects.filter(order=order).count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("trigger", ["manual", "automatic"])
def test_smtp_failure_preserves_cancellation_and_retry_succeeds(trigger):
    order, product = _reserved_order(user=None, guest_email="guest@example.test")
    with patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("SMTP unavailable")):
        cancel_pending_order(order_id=order.pk)
    _assert_released(order, product)
    delivery = NotificationDelivery.objects.get(order=order, event="cancelled")
    assert (delivery.status, delivery.attempts) == ("FAILED", 1)
    assert delivery.next_retry_at is not None
    assert not mail.outbox
    if trigger == "manual":
        retry_delivery(delivery.pk)
    else:
        attempt_delivery(delivery.pk, now=delivery.next_retry_at)
    delivery.refresh_from_db()
    assert (delivery.status, delivery.attempts) == ("SENT", 2)
    assert len(mail.outbox) == 1
    _assert_released(order, product)


@pytest.mark.django_db(transaction=True)
def test_outer_rollback_discards_cancellation_delivery_and_callback():
    order, product = _reserved_order(user=None)
    with pytest.raises(RuntimeError, match="rollback"):
        with transaction.atomic():
            cancel_pending_order(order_id=order.pk)
            assert NotificationDelivery.objects.filter(order=order, event="cancelled").exists()
            assert not mail.outbox
            raise RuntimeError("rollback")
    order.refresh_from_db()
    reservation = apps.get_model("products", "InventoryReservation").objects.get(order_id=order.pk)
    assert (order.status, reservation.status) == ("PENDING", "ACTIVE")
    assert not NotificationDelivery.objects.filter(order=order).exists()
    assert not mail.outbox


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("status", ["PAID", "SHIPPED", "DELIVERED", "CANCELLED"])
def test_ineligible_order_never_schedules_or_sends(status):
    order, _ = _reserved_order(status=status)
    with pytest.raises(PendingCancellationError):
        cancel_pending_order(order_id=order.pk)
    order.refresh_from_db()
    assert order.status == status
    assert not NotificationDelivery.objects.filter(order=order).exists()
    assert not mail.outbox


@pytest.mark.django_db(transaction=True)
def test_missing_reservation_never_schedules_or_sends():
    order = OrderFactory()
    with pytest.raises(InventoryReservationError):
        cancel_pending_order(order_id=order.pk)
    order.refresh_from_db()
    assert order.status == "PENDING"
    assert not NotificationDelivery.objects.filter(order=order).exists()
    assert not mail.outbox


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("guest", [True, False])
def test_missing_recipient_is_retryable_without_inventing_an_address(guest):
    user = None if guest else UserFactory(email="")
    order, product = _reserved_order(user=user, guest_email=None)
    cancel_pending_order(order_id=order.pk)
    _assert_released(order, product)
    delivery = NotificationDelivery.objects.get(order=order, event="cancelled")
    assert (delivery.status, delivery.attempts) == ("FAILED", 1)
    assert delivery.last_error == "El pedido no tiene correo de contacto."
    assert delivery.next_retry_at is not None and not mail.outbox
    retry_delivery(delivery.pk)
    delivery.refresh_from_db()
    assert (delivery.status, delivery.attempts) == ("FAILED", 2)
    assert not mail.outbox
    if guest:
        order.guest_email = "guest@example.test"
        order.save(update_fields=["guest_email"])
    else:
        user.email = "account@example.test"
        user.save(update_fields=["email"])
    retry_delivery(delivery.pk)
    delivery.refresh_from_db()
    assert (delivery.status, delivery.attempts) == ("SENT", 3)
    assert mail.outbox[0].to == ["guest@example.test" if guest else "account@example.test"]


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AdminCancellationEmailTests(TestCase):
    def test_detail_cancellation_delivers_once_when_commit_callbacks_run(self):
        self.client.force_login(UserFactory(is_staff=True, is_superuser=True))
        order, product = _reserved_order(user=None, guest_email="guest@example.test")
        url = reverse("admin:orders_order_cancel", args=[order.pk])
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(url, {"_confirm_cancel": "1"})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)
        _assert_released(order, product)
        self.assertEqual(order.cancellation_reason, 'ADMIN')
        delivery = NotificationDelivery.objects.get(order=order, event="cancelled")
        self.assertEqual((delivery.status, delivery.attempts), ("SENT", 1))
        self.assertEqual(mail.outbox[0].to, ["guest@example.test"])
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.client.post(url, {"_confirm_cancel": "1"})
        self.assertEqual(callbacks, [])
        self.assertEqual(NotificationDelivery.objects.filter(order=order).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
