from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.tests.factories import UserFactory
from apps.orders.admin import OrderAdmin
from apps.orders.models import Order
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
