from datetime import timedelta

import pytest
from django.apps import apps
from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.tests.factories import UserFactory
from apps.orders.admin import OrderAdmin
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory, OrderItemFactory
from apps.products.tests.factories import ProductFactory
from apps.products.models import InventoryReservation, StockMovement
from apps.products.services import ReservationLineInput, reserve


pytestmark = pytest.mark.django_db


def _reserved_order(order_factory, order_item_factory, product_factory, **kwargs):
    product = product_factory(current_stock=4, supplier__phone="56912345678")
    order = order_factory(status="PENDING", **kwargs)
    order_item_factory(order=order, product=product, quantity=2, price=product.price)
    with transaction.atomic():
        reserve(order_id=order.id, lines=(ReservationLineInput(product.id, 2),),
                expires_at=timezone.now() + timedelta(minutes=15))
    return order, product


def _cancel(client, order, token=None):
    headers = {"HTTP_X_ORDER_CAPABILITY": token} if token else {}
    return client.post(f"/api/orders/by-order-number/{order.order_number}/cancel/", {}, format="json", **headers)


def test_owner_and_guest_cancellation_release_each_reservation_once(
        authenticated_client, user, order_factory, order_item_factory, product_factory):
    owner_order, owner_product = _reserved_order(order_factory, order_item_factory, product_factory, user=user)

    owner_response = _cancel(authenticated_client, owner_order)

    owner_order.refresh_from_db()
    owner_reservation = InventoryReservation.objects.get(order_id=owner_order.id)
    assert owner_response.status_code == status.HTTP_200_OK
    assert (owner_order.status, owner_reservation.status, owner_reservation.release_reason) == ("CANCELLED", "RELEASED", "CANCELLED")
    assert _cancel(authenticated_client, owner_order).status_code == status.HTTP_409_CONFLICT
    assert StockMovement.objects.filter(product=owner_product).count() == 0

    guest_order, guest_product = _reserved_order(order_factory, order_item_factory, product_factory, user=None)
    guest_response = _cancel(APIClient(), guest_order, guest_order.issue_guest_access())

    guest_order.refresh_from_db()
    guest_reservation = InventoryReservation.objects.get(order_id=guest_order.id)
    assert guest_response.status_code == status.HTTP_200_OK
    assert (guest_order.status, guest_reservation.status, guest_reservation.release_reason) == ("CANCELLED", "RELEASED", "CANCELLED")
    assert StockMovement.objects.filter(product=guest_product).count() == 0


def test_cancellation_masks_missing_invalid_cross_account_and_staff_api_access(
        api_client, staff_client, order_factory, order_item_factory, product_factory):
    order, _ = _reserved_order(order_factory, order_item_factory, product_factory, user=None)
    other_client = APIClient()
    other_client.force_authenticate(user=UserFactory.create())

    responses = [
        _cancel(api_client, order),
        _cancel(api_client, order, "invalid-capability"),
        _cancel(other_client, order),
        _cancel(staff_client, order),
    ]

    assert [response.status_code for response in responses] == [status.HTTP_404_NOT_FOUND] * 4
    order.refresh_from_db()
    reservation = InventoryReservation.objects.get(order_id=order.id)
    assert (order.status, reservation.status) == ("PENDING", "ACTIVE")


def test_admin_cancellation_releases_only_pending_orders(
        rf, staff_user, order_factory, order_item_factory, product_factory):
    pending, _ = _reserved_order(order_factory, order_item_factory, product_factory)
    paid, _ = _reserved_order(order_factory, order_item_factory, product_factory)
    paid.status = "PAID"
    paid.save(update_fields=["status"])
    request = rf.get("/admin/orders/order/")
    request.user = staff_user
    request.session = {}
    request._messages = FallbackStorage(request)
    admin = OrderAdmin(Order, AdminSite())

    admin.cancel_pending_orders(request, Order.objects.filter(id__in=[pending.id, paid.id]))

    pending.refresh_from_db()
    paid.refresh_from_db()
    assert (pending.status, InventoryReservation.objects.get(order_id=pending.id).status) == ("CANCELLED", "RELEASED")
    assert (paid.status, InventoryReservation.objects.get(order_id=paid.id).status) == ("PAID", "ACTIVE")


class AdminDetailInventoryCancellationTests(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory(is_staff=True, is_superuser=True))
        self.Reservation = apps.get_model("products", "InventoryReservation")
        self.Movement = apps.get_model("products", "StockMovement")

    def reserved_order(self):
        return _reserved_order(OrderFactory, OrderItemFactory, ProductFactory)

    def test_confirmation_and_repeated_posts_release_once_without_stock_or_metadata_changes(self):
        order, product = self.reserved_order()
        cancel_url = reverse("admin:orders_order_cancel", args=[order.pk])
        change_url = reverse("admin:orders_order_change", args=[order.pk])
        original_metadata = (order.carrier, order.payment_method, order.guest_access_version)
        response = self.client.get(cancel_url)
        self.assertContains(response, "Confirmar cancelación")
        self.assertContains(response, "Volver sin cancelar")
        self.assertContains(response, 'method="post"')
        order.refresh_from_db()
        reservation = self.Reservation.objects.get(order_id=order.pk)
        self.assertEqual((order.status, reservation.status), ("PENDING", "ACTIVE"))
        self.assertFalse(LogEntry.objects.filter(object_id=str(order.pk)).exists())

        response = self.client.post(cancel_url, {
            "_confirm_cancel": "1", "carrier": "", "payment_method": "forged", "status": "PAID",
        }, follow=True)
        self.assertContains(response, "cancelado correctamente")
        order.refresh_from_db()
        reservation.refresh_from_db()
        self.assertEqual((order.status, reservation.status, reservation.release_reason),
                         ("CANCELLED", "RELEASED", "CANCELLED"))
        self.assertEqual((order.carrier, order.payment_method, order.guest_access_version), original_metadata)
        released_at = reservation.transitioned_at
        self.assertIsNotNone(released_at)
        self.assertRedirects(self.client.post(cancel_url, {"_confirm_cancel": "1"}), change_url)
        reservation.refresh_from_db()
        self.assertEqual(reservation.transitioned_at, released_at)
        product.refresh_from_db()
        self.assertEqual(product.current_stock, 4)
        self.assertFalse(self.Movement.objects.filter(product=product).exists())
        log = LogEntry.objects.get(object_id=str(order.pk))
        self.assertIn("Pedido pendiente cancelado", log.change_message)
        self.assertTrue(log.is_change())

    def test_missing_reservation_reports_error_without_mutation_on_repeated_attempts(self):
        product = ProductFactory(current_stock=4)
        order = OrderFactory(status="PENDING")
        OrderItemFactory(order=order, product=product, price=product.price)
        original_updated_at = order.updated_at
        cancel_url = reverse("admin:orders_order_cancel", args=[order.pk])
        change_url = reverse("admin:orders_order_change", args=[order.pk])
        self.assertContains(self.client.get(cancel_url), "Confirmar cancelación")

        for attempt in range(2):
            with self.subTest(attempt=attempt):
                response = self.client.post(cancel_url, {"_confirm_cancel": "1"})
                self.assertRedirects(response, change_url, fetch_redirect_response=False)
                detail = self.client.get(change_url)
                self.assertContains(detail, "la reserva de inventario es inconsistente")
                self.assertContains(detail, "El pedido no fue modificado")
                order.refresh_from_db()
                product.refresh_from_db()
                self.assertEqual((order.status, order.updated_at), ("PENDING", original_updated_at))
                self.assertEqual(product.current_stock, 4)
                self.assertFalse(self.Reservation.objects.filter(order_id=order.pk).exists())
                self.assertFalse(self.Movement.objects.filter(product=product).exists())
                self.assertFalse(LogEntry.objects.filter(object_id=str(order.pk)).exists())
                self.assertFalse(apps.get_model("orders", "NotificationDelivery").objects.filter(order=order).exists())

    def test_bulk_cancellation_still_releases_only_pending_reservations(self):
        pending, pending_product = self.reserved_order()
        paid, paid_product = self.reserved_order()
        Order.objects.filter(pk=paid.pk).update(status="PAID")
        response = self.client.post(reverse("admin:orders_order_changelist"), {
            "action": "cancel_pending_orders", "_selected_action": [str(pending.pk), str(paid.pk)],
            "index": "0", "select_across": "0",
        }, follow=True)
        self.assertContains(response, "1 pedido(s) pendiente(s) cancelado(s)")
        pending.refresh_from_db()
        paid.refresh_from_db()
        self.assertEqual((pending.status, self.Reservation.objects.get(order_id=pending.pk).status),
                         ("CANCELLED", "RELEASED"))
        self.assertEqual((paid.status, self.Reservation.objects.get(order_id=paid.pk).status), ("PAID", "ACTIVE"))
        for product in (pending_product, paid_product):
            product.refresh_from_db()
            self.assertEqual(product.current_stock, 4)
            self.assertFalse(self.Movement.objects.filter(product=product).exists())
