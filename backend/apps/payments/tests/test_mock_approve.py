"""Integration tests for the development-only mock payment approval (Unit 5, task 2.3).

Owner/capability authorization, fail-closed production denial, idempotent
PENDING->APPROVED / PENDING->PAID transition, and selective authenticated
cart clearing. HTTP-level acceptance lives here (real URL wiring); the
service keeps the state machine.
"""
from datetime import timedelta

import pytest
from django.core import mail
from django.db import transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.tests.factories import UserFactory
from apps.carts.models import Cart
from apps.carts.tests.factories import CartFactory, CartItemFactory
from apps.orders.tests.factories import OrderItemFactory
from apps.payments.models import Transaction
from apps.payments.services import PaymentApprovalError, PaymentStateError, approve_payment
from apps.products.models import InventoryReservation, StockMovement
from apps.products.services import ReservationLineInput, inspect, reserve
from apps.products.tests.factories import ProductFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def cart_factory():
    """Return the CartFactory class."""
    return CartFactory


@pytest.fixture
def cart_item_factory():
    """Return the CartItemFactory class."""
    return CartItemFactory


@pytest.fixture
def product_factory():
    """Return the ProductFactory class."""
    return ProductFactory


def _approve(client, transaction):
    return client.post(f"/api/payments/{transaction.id}/mock-approve/")


def _reserve_for_payment(order, product, quantity=2):
    if not order.items.exists(): OrderItemFactory(order=order, product=product, quantity=quantity, price=product.price)
    with transaction.atomic():
        reserve(order_id=order.id, lines=(ReservationLineInput(product.id, quantity),),
                expires_at=timezone.now() + timedelta(minutes=15))


class TestApprovePaymentService:
    """Service state machine: approve exactly once, replay idempotently."""

    def test_approve_marks_transaction_approved_and_order_paid(self, order_factory, transaction_factory, mock_payment_enabled):
        order = order_factory(status="PENDING", subtotal=20000, shipping_cost=3000, total=23000)
        attempt = transaction_factory(order=order)

        approved, updated = approve_payment(order=order, transaction_id=attempt.id)

        assert (approved.id, approved.status) == (attempt.id, "APPROVED")
        assert (updated.id, updated.status) == (order.id, "PAID")

    def test_approve_replay_returns_same_state_without_duplicate_effects(self, user, cart_factory, cart_item_factory, product_factory, order_factory, transaction_factory, mock_payment_enabled):
        cart = cart_factory(user=user)
        product = product_factory(price=1000)
        cart_item_factory(cart=cart, product=product, quantity=2)
        order = order_factory(user=user, status="PENDING", subtotal=2000, shipping_cost=0, total=2000)
        OrderItemFactory(order=order, product=product, quantity=2, price=1000)
        _reserve_for_payment(order, product)
        attempt = transaction_factory(order=order)

        first = approve_payment(order=order, transaction_id=attempt.id)
        second = approve_payment(order=order, transaction_id=attempt.id)

        assert (first[0].status, first[1].status) == ("APPROVED", "PAID")
        assert (second[0].status, second[1].status) == ("APPROVED", "PAID")
        cart.refresh_from_db()
        assert cart.items.count() == 0

    def test_approval_schedules_payment_confirmation_email_after_commit(self, user, order_factory, transaction_factory, mock_payment_enabled):
        from django.test import TestCase

        from apps.orders.models import NotificationDelivery
        order = order_factory(user=user, status="PENDING", total=30000)
        attempt = transaction_factory(order=order)
        mail.outbox.clear()

        with TestCase.captureOnCommitCallbacks(execute=True):
            approve_payment(order=order, transaction_id=attempt.id)
        approve_payment(order=order, transaction_id=attempt.id)  # replay: no duplicate

        delivery = NotificationDelivery.objects.get(order=order, event="payment_confirmation")
        assert delivery.status == "SENT"
        assert NotificationDelivery.objects.filter(order=order).count() == 1
        assert len(mail.outbox) == 1
        assert order.order_number in mail.outbox[0].subject
        assert "$30.000" in mail.outbox[0].body

    def test_approval_commits_once_and_rejection_retains_an_active_hold(
            self, order_factory, transaction_factory, product_factory, mock_payment_enabled):
        approved_product = product_factory(current_stock=4, supplier__phone="56912345678")
        approved_order = order_factory(status="PENDING", total=2000)
        _reserve_for_payment(approved_order, approved_product)
        approved_attempt = transaction_factory(order=approved_order)

        first = approve_payment(order=approved_order, transaction_id=approved_attempt.id)
        second = approve_payment(order=approved_order, transaction_id=approved_attempt.id)

        assert (first[0].status, first[1].status) == ("APPROVED", "PAID")
        assert (second[0].status, second[1].status) == ("APPROVED", "PAID")
        assert StockMovement.objects.filter(product=approved_product, movement_type="OUT", quantity=2).count() == 1

        rejected_product = product_factory(current_stock=4, supplier__phone="56912345678")
        rejected_order = order_factory(status="PENDING", total=2000)
        _reserve_for_payment(rejected_order, rejected_product)
        rejected_attempt = transaction_factory(order=rejected_order, status="REJECTED")
        with pytest.raises(PaymentApprovalError):
            approve_payment(order=rejected_order, transaction_id=rejected_attempt.id)
        with transaction.atomic():
            held = inspect(order_id=rejected_order.id)
        assert held.status == "ACTIVE"
        assert StockMovement.objects.filter(product=rejected_product).count() == 0

    def test_expired_reservation_cancels_without_approval(
            self, order_factory, transaction_factory, product_factory, mock_payment_enabled):
        product = product_factory(current_stock=4, supplier__phone="56912345678")
        order = order_factory(status="PENDING", total=2000)
        _reserve_for_payment(order, product)
        attempt = transaction_factory(order=order)
        InventoryReservation.objects.filter(order_id=order.id).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        with pytest.raises(PaymentStateError):
            approve_payment(order=order, transaction_id=attempt.id)

        order.refresh_from_db()
        attempt.refresh_from_db()
        reservation = InventoryReservation.objects.get(order_id=order.id)
        assert (order.status, attempt.status) == ("CANCELLED", "PENDING")
        assert (reservation.status, reservation.release_reason) == ("RELEASED", "EXPIRED")
        assert StockMovement.objects.filter(product=product).count() == 0


class TestMockApproveView:
    """Approval acceptance through the real URL stack."""

    def test_owner_approval_returns_approved_state(self, authenticated_client, user, order_factory, transaction_factory, mock_payment_enabled):
        """The owning user approves once and receives the approved state."""
        order = order_factory(user=user, status="PENDING", total=30000)
        attempt = transaction_factory(order=order)

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"transaction_id": attempt.id, "order_id": order.id,
                                   "status": "APPROVED", "order_status": "PAID"}
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert attempt.status == "APPROVED" and order.status == "PAID"

    def test_repeated_approval_is_idempotent(self, authenticated_client, user, order_factory, transaction_factory, cart_factory, cart_item_factory, product_factory, mock_payment_enabled):
        """Replaying approval returns the same state without duplicate effects."""
        cart = cart_factory(user=user)
        product = product_factory(price=1000)
        cart_item_factory(cart=cart, product=product, quantity=2)
        order = order_factory(user=user, status="PENDING", subtotal=2000, shipping_cost=0, total=2000)
        OrderItemFactory(order=order, product=product, quantity=2, price=1000)
        _reserve_for_payment(order, product)
        attempt = transaction_factory(order=order)

        first, second = _approve(authenticated_client, attempt), _approve(authenticated_client, attempt)

        assert first.status_code == second.status_code == status.HTTP_200_OK
        assert first.json() == second.json()
        assert Transaction.objects.filter(order=order).count() == 1
        order.refresh_from_db()
        cart.refresh_from_db()
        assert order.status == "PAID" and cart.items.count() == 0

    @pytest.mark.parametrize("debug,provider", [(False, "mock"), (True, None), (True, "stripe")])
    def test_approval_denied_when_mock_not_explicitly_enabled(self, authenticated_client, user, order_factory, transaction_factory, debug, provider):
        """Production, absent and unknown providers fail closed with a masked 503."""
        order = order_factory(user=user, status="PENDING", total=30000)
        attempt = transaction_factory(order=order)
        with override_settings(DEBUG=debug, PAYMENT_PROVIDER=provider):
            response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json() == {"detail": "Payment service unavailable."}
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert attempt.status == "PENDING" and order.status == "PENDING"

    def test_cross_owner_approval_is_masked(self, user, order_factory, transaction_factory, mock_payment_enabled):
        """Another customer cannot approve the order and learns nothing."""
        order = order_factory(user=user, status="PENDING", total=30000)
        attempt = transaction_factory(order=order)
        other = APIClient()
        other.force_authenticate(user=UserFactory.create())

        response = _approve(other, attempt)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Not found."}
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert attempt.status == "PENDING" and order.status == "PENDING"

    def test_forged_transaction_id_is_masked(self, api_client):
        """Unknown transaction identifiers are indistinguishable from denied access."""
        response = api_client.post("/api/payments/99999/mock-approve/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Not found."}

    def test_approval_without_credentials_is_masked(self, api_client, order_factory, transaction_factory):
        """An anonymous caller without capability cannot approve an owned order."""
        order = order_factory(status="PENDING", total=30000)
        attempt = transaction_factory(order=order)

        response = _approve(api_client, attempt)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Not found."}
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert attempt.status == "PENDING" and order.status == "PENDING"

    def test_guest_cookie_authorizes_approval_without_server_cart(self, api_client, order_factory, transaction_factory, mock_payment_enabled):
        """A guest with a valid exchanged cookie approves; the guest cart stays client-side."""
        order = order_factory(user=None, status="PENDING", total=30000)
        raw_token = order.issue_guest_access()
        exchange = api_client.post(
            f"/api/orders/by-order-number/{order.order_number}/access/",
            {}, format="json", HTTP_X_ORDER_CAPABILITY=raw_token,
        )
        api_client.cookies["guest_order_access"] = exchange.cookies["guest_order_access"].value
        attempt = transaction_factory(order=order)

        response = _approve(api_client, attempt)

        assert response.status_code == status.HTTP_200_OK
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert attempt.status == "APPROVED" and order.status == "PAID"
        assert Cart.objects.count() == 0

        from django.core.cache import cache
        from rest_framework.settings import api_settings
        cache.clear()
        api_settings.DEFAULT_THROTTLE_RATES['payment_approve'] = '2/min'
        assert _approve(api_client, attempt).status_code == 200
        assert _approve(api_client, attempt).status_code == 200
        assert _approve(api_client, attempt).status_code == 429

    @pytest.mark.parametrize("attempt_kwargs", [
        {"status": "REJECTED"},
        {"provider": None},
    ])
    def test_unapprovable_transactions_fail_safely(self, authenticated_client, user, order_factory, transaction_factory, mock_payment_enabled, attempt_kwargs):
        """REJECTED and non-mock transactions are rejected without state change."""
        order = order_factory(user=user, status="PENDING", total=30000)
        attempt = transaction_factory(order=order, **attempt_kwargs)

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no puede ser aprobada" in str(response.json()).lower()
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert order.status == "PENDING"

    @pytest.mark.parametrize("order_status", ["SHIPPED", "PAID"])
    def test_non_pending_order_cannot_be_approved(self, authenticated_client, user, order_factory, transaction_factory, mock_payment_enabled, order_status):
        """Approval of a non-PENDING order is rejected with no state change."""
        order = order_factory(user=user, status=order_status, total=30000)
        attempt = transaction_factory(order=order)

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no se puede pagar" in str(response.json()).lower()
        attempt.refresh_from_db()
        order.refresh_from_db()
        assert attempt.status == "PENDING" and order.status == order_status

    def test_approved_transaction_on_pending_order_fails_safely(self, authenticated_client, user, order_factory, transaction_factory, mock_payment_enabled):
        """An already-approved transaction never silently completes a PENDING order."""
        order = order_factory(user=user, status="PENDING", total=30000)
        attempt = transaction_factory(order=order, status="APPROVED")

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        order.refresh_from_db()
        assert order.status == "PENDING"

    def test_approval_clears_only_purchased_cart_quantities(self, authenticated_client, user, order_factory, transaction_factory, cart_factory, cart_item_factory, product_factory, mock_payment_enabled):
        """Equal purchased quantities remove the row; unrelated items stay intact."""
        cart = cart_factory(user=user)
        bought = product_factory(price=1000)
        unrelated = product_factory(price=500)
        cart_item_factory(cart=cart, product=bought, quantity=2)
        cart_item_factory(cart=cart, product=unrelated, quantity=3)
        order = order_factory(user=user, status="PENDING", subtotal=2000, shipping_cost=0, total=2000)
        OrderItemFactory(order=order, product=bought, quantity=2, price=1000)
        _reserve_for_payment(order, bought)
        attempt = transaction_factory(order=order)

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_200_OK
        cart.refresh_from_db()
        assert cart.items.count() == 1
        remaining = cart.items.get()
        assert remaining.product_id == unrelated.id and remaining.quantity == 3

    def test_approval_decrements_cart_quantity_above_purchased(self, authenticated_client, user, order_factory, transaction_factory, cart_factory, cart_item_factory, product_factory, mock_payment_enabled):
        """A cart with more units than purchased keeps the excess."""
        cart = cart_factory(user=user)
        product = product_factory(price=1000)
        cart_item_factory(cart=cart, product=product, quantity=5)
        order = order_factory(user=user, status="PENDING", subtotal=2000, shipping_cost=0, total=2000)
        OrderItemFactory(order=order, product=product, quantity=2, price=1000)
        _reserve_for_payment(order, product)
        attempt = transaction_factory(order=order)

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_200_OK
        cart.refresh_from_db()
        assert cart.items.count() == 1
        assert cart.items.get().quantity == 3

    def test_approval_missing_purchased_product_leaves_cart_intact(self, authenticated_client, user, order_factory, transaction_factory, cart_factory, cart_item_factory, product_factory, mock_payment_enabled):
        """A purchased product absent from the cart leaves the cart untouched."""
        cart = cart_factory(user=user)
        other = product_factory(price=500)
        cart_item_factory(cart=cart, product=other, quantity=3)
        purchased = product_factory(price=1000)
        order = order_factory(user=user, status="PENDING", subtotal=2000, shipping_cost=0, total=2000)
        OrderItemFactory(order=order, product=purchased, quantity=2, price=1000)
        _reserve_for_payment(order, purchased)
        attempt = transaction_factory(order=order)

        response = _approve(authenticated_client, attempt)

        assert response.status_code == status.HTTP_200_OK
        cart.refresh_from_db()
        assert cart.items.count() == 1
        assert cart.items.get().quantity == 3
