"""Final cross-stack runtime evidence (task 4.4): guest and authenticated
purchase -> approve -> dispatch -> notification journeys. API steps run
through the real Django URL/middleware/serializer/service stack in-process
via the DRF test client (APIClient) — no browser or network E2E is claimed
and no browser runner exists in the repo. Dispatch and notification steps
invoke the public services directly (fulfill_dispatch, attempt_delivery,
retry_delivery). The existing MSW frontend journeys remain the frontend
runtime evidence layer. Production stays fail-closed: the mock provider is
enabled here only via the same DEBUG + PAYMENT_PROVIDER=mock gate.

Test-only introspection note: idempotency, security and notification proofs
that need internal row state use Django's runtime app registry
(django.apps.apps.get_model) through the local helpers below — never direct
model imports. The indirection lives only in test code; production modules
keep zero cross-app model imports, so the repository rule stays untouched.
"""
from datetime import date, timedelta
from unittest import mock

import pytest
from django.apps import apps
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.tests.factories import UserFactory
from apps.carts.tests.factories import CartFactory, CartItemFactory
from apps.orders.models import NotificationDelivery, Order
from apps.orders.notifications import attempt_delivery, retry_delivery
from apps.orders.services import fulfill_dispatch
from apps.products.tests.factories import ProductFactory
from apps.shipping.services import future_dispatch_dates

pytestmark = pytest.mark.django_db

KEY = "journey-checkout-key-001"


@pytest.fixture(autouse=True)
def _clear_runtime_state():
    """Throttle history and the mail outbox must not leak across tests."""
    from django.core.cache import cache
    cache.clear()
    mail.outbox.clear()
    yield
    cache.clear()


@pytest.fixture
def mock_payment_enabled(settings):
    """Explicitly enable the development mock provider (same gate as prod)."""
    settings.DEBUG = True
    settings.PAYMENT_PROVIDER = "mock"
    return settings


def _cart_model():
    """Resolve carts.Cart via the app registry — no cross-app model import."""
    return apps.get_model("carts", "Cart")


def _transaction_model():
    """Resolve payments.Transaction via the app registry (test-only)."""
    return apps.get_model("payments", "Transaction")


def _guest_payload(product_id, comuna_id, revision, quantity=2):
    return {
        "guest_email": "guest@journey.cl",
        "guest_name": "Invitada",
        "phone": "+56912345678",
        "comuna": comuna_id,
        "shipping_address": "Av. Providencia 1234",
        "guest_items": [{"product_id": product_id, "quantity": quantity}],
        "confirmed_revision": revision,
        "payment_method": "webpay",
        "delivery_kind": "standard",
        "requested_dispatch_date": str(future_dispatch_dates()[0]),
    }


def _auth_payload(comuna_id):
    # shipping_cost intentionally omitted: the backend resolves the snapshot.
    return {"phone": "+56987654321", "comuna": comuna_id,
            "shipping_address": "Calle 456", "payment_method": "webpay",
            "delivery_kind": "standard",
            "requested_dispatch_date": str(future_dispatch_dates()[0])}


def _quote(api_client, product_id, comuna_id, quantity=2):
    response = api_client.post("/api/orders/quote/",
                               {"items": [{"product_id": product_id, "quantity": quantity}],
                                "comuna": comuna_id}, format="json")
    assert response.status_code == status.HTTP_200_OK
    return response.json()


def test_guest_journey_purchase_approve_dispatch_and_notify(
        api_client, product_factory, comuna_factory, mock_payment_enabled):
    """Guest: catalog -> quote -> idempotent order -> capability -> initiate
    -> owned approve exactly once -> dispatch -> durable notifications."""
    product = product_factory(price=10000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)

    # 1. Product availability through the public catalog.
    listing = api_client.get("/api/products/")
    assert listing.status_code == status.HTTP_200_OK
    page = listing.json().get("results", listing.json())
    assert product.id in {item["id"] for item in page}

    # 2. Backend-authoritative quote totals (never client-calculated).
    quote = _quote(api_client, product.id, comuna.id)
    assert (quote["subtotal"], quote["shipping_cost"], quote["total"]) == (20000, 3000, 23000)

    # 3. Idempotent order creation: PENDING, frozen totals, raw capability.
    created = api_client.post("/api/orders/", _guest_payload(product.id, comuna.id, quote["revision"]),
                              format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert created.status_code == status.HTTP_201_CREATED
    order_data = created.json()
    assert order_data["status"] == "PENDING"
    assert (order_data["subtotal"], order_data["shipping_cost"], order_data["total"]) == (20000, 3000, 23000)
    first_token = order_data["guest_access"]["token"]

    # 4. Replay: same order, rotated capability, no duplicate. Replay contract:
    # every stable field matches the initial response byte-for-byte, and the
    # ONLY intentional difference is the rotated guest capability — the design
    # says "guest replay rotates its raw capability": rotate_guest_access
    # revokes the previous token and issues a fresh one (new token, new expiry).
    replayed = api_client.post("/api/orders/", _guest_payload(product.id, comuna.id, quote["revision"]),
                               format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert replayed.status_code == status.HTTP_201_CREATED
    replayed_data = replayed.json()
    stable_initial = dict(order_data)
    del stable_initial["guest_access"]
    replayed_capability = replayed_data.pop("guest_access")
    assert replayed_data == stable_initial
    second_token = replayed_capability["token"]
    assert second_token != first_token
    assert replayed_capability["expires_at"] != order_data["guest_access"]["expires_at"]
    assert Order.objects.count() == 1

    # 5. Capability exchange issues the access cookie (guest ownership).
    exchange = api_client.post(
        f"/api/orders/by-order-number/{order_data['order_number']}/access/",
        {}, format="json", HTTP_X_ORDER_CAPABILITY=second_token)
    assert exchange.status_code == status.HTTP_204_NO_CONTENT
    api_client.cookies["guest_order_access"] = exchange.cookies["guest_order_access"].value

    # 5b. Rotation revoked the PREVIOUS capability: the replacement token is
    # valid (5) while the old one is denied — masked 404 on a cookie-less client.
    stale = APIClient()
    revoked = stale.post(
        f"/api/orders/by-order-number/{order_data['order_number']}/access/",
        {}, format="json", HTTP_X_ORDER_CAPABILITY=first_token)
    assert revoked.status_code == status.HTTP_404_NOT_FOUND

    # 6. Owned lookup succeeds; a stranger without capability is masked 404.
    lookup = api_client.get(f"/api/orders/by-order-number/{order_data['order_number']}/")
    assert lookup.status_code == status.HTTP_200_OK
    assert lookup.json()["id"] == order_data["id"]
    stranger = APIClient()
    denied = stranger.get(f"/api/orders/by-order-number/{order_data['order_number']}/")
    assert denied.status_code == status.HTTP_404_NOT_FOUND

    # 7. Mock initiation (development) + idempotent replay: exact same payload.
    initiated = api_client.post("/api/payments/initiate/", {"order_id": order_data["id"]},
                                format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert initiated.status_code == status.HTTP_200_OK
    attempt = initiated.json()
    assert attempt["amount"] == 23000 and "mock-checkout" in attempt["payment_url"]
    replayed_init = api_client.post("/api/payments/initiate/", {"order_id": order_data["id"]},
                                    format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert replayed_init.status_code == status.HTTP_200_OK
    assert replayed_init.json() == attempt
    assert _transaction_model().objects.filter(order_id=order_data["id"]).count() == 1

    # 8. Owned approval exactly once: APPROVED + PAID, replay returns same state.
    with TestCase.captureOnCommitCallbacks(execute=True):
        approved = api_client.post(f"/api/payments/{attempt['transaction_id']}/mock-approve/")
    assert approved.status_code == status.HTTP_200_OK
    assert approved.json() == {"transaction_id": attempt["transaction_id"],
                               "order_id": order_data["id"],
                               "status": "APPROVED", "order_status": "PAID"}
    with TestCase.captureOnCommitCallbacks(execute=True):
        re_approved = api_client.post(f"/api/payments/{attempt['transaction_id']}/mock-approve/")
    assert re_approved.status_code == status.HTTP_200_OK
    assert re_approved.json() == approved.json()
    order = Order.objects.get(id=order_data["id"])
    assert order.status == "PAID"
    assert _transaction_model().objects.filter(order=order).count() == 1
    assert _cart_model().objects.count() == 0  # guest cart stays client-side, never server-cleared

    # 9. Durable payment confirmation notification is SENT to the guest.
    confirmation = NotificationDelivery.objects.get(order=order, event="payment_confirmation")
    assert confirmation.status == "SENT"
    assert len(mail.outbox) == 1 and order.order_number in mail.outbox[0].subject
    assert mail.outbox[0].to == ["guest@journey.cl"]

    # 10. Dispatch: PAID -> SHIPPED with required fields; delivery row PENDING.
    order = fulfill_dispatch(order=order, carrier="Chilexpress",
                             estimated_delivery_date=date.today() + timedelta(days=3),
                             tracking_number="TRK-JOURNEY")
    assert order.status == "SHIPPED" and order.carrier == "Chilexpress"
    dispatch = NotificationDelivery.objects.get(order=order, event="dispatch")
    assert dispatch.status == "PENDING"

    # 11. Email failure is contained: FAILED delivery, domain state persists.
    with mock.patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("SMTP down")):
        attempt_delivery(dispatch.id, trigger="initial")
    dispatch.refresh_from_db()
    assert (dispatch.status, dispatch.attempts, dispatch.next_retry_at is not None) == ("FAILED", 1, True)
    order.refresh_from_db()
    assert order.status == "SHIPPED"

    # 12. Admin retry resends: dispatch email SENT after the failure.
    retry_delivery(dispatch.id)
    dispatch.refresh_from_db()
    assert (dispatch.status, dispatch.sent_at is not None) == ("SENT", True)
    assert len(mail.outbox) == 2
    assert order.order_number in mail.outbox[1].subject


def test_authenticated_journey_cart_ownership_approval_and_dispatch(
        authenticated_client, user, product_factory, comuna_factory, mock_payment_enabled):
    """Authenticated: server cart -> idempotent order (cart preserved) ->
    initiate -> masked cross-owner approve -> owned approve exactly once with
    purchased-quantity cart clearing -> dispatch -> notifications."""
    bought = product_factory(price=5000, current_stock=10)
    comuna = comuna_factory(shipping_cost=3000)
    cart = CartFactory(user=user)
    CartItemFactory(cart=cart, product=bought, quantity=2)

    # 1. Server cart availability with backend-computed totals.
    cart_view = authenticated_client.get("/api/cart/me/")
    assert cart_view.status_code == status.HTTP_200_OK
    body = cart_view.json()
    assert len(body["items"]) == 1 and body["subtotal"] == 10000

    # 2. Idempotent order creation; the cart is PRESERVED until approval.
    created = authenticated_client.post("/api/orders/", _auth_payload(comuna.id),
                                        format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert created.status_code == status.HTTP_201_CREATED
    order_data = created.json()
    assert order_data["status"] == "PENDING"
    assert (order_data["subtotal"], order_data["shipping_cost"], order_data["total"]) == (10000, 3000, 13000)
    cart.refresh_from_db()
    assert cart.items.count() == 1
    replayed = authenticated_client.post("/api/orders/", _auth_payload(comuna.id),
                                         format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert replayed.status_code == status.HTTP_201_CREATED
    # Auth replay contract: full payload equality — replay returns the same row
    # and no field is intentionally different (no capability rotation).
    assert replayed.json() == order_data
    assert Order.objects.count() == 1

    # 2b. Customer adds an unrelated item while payment is pending.
    unrelated = product_factory(price=2000, current_stock=10)
    added = authenticated_client.post("/api/cart/me/",
                                      {"product_id": unrelated.id, "quantity": 1}, format="json")
    assert added.status_code == status.HTTP_201_CREATED
    cart.refresh_from_db()
    assert cart.items.count() == 2

    # 3. Mock initiation (development) + idempotent replay: exact same payload.
    initiated = authenticated_client.post("/api/payments/initiate/", {"order_id": order_data["id"]},
                                          format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert initiated.status_code == status.HTTP_200_OK
    attempt = initiated.json()
    transaction_id = attempt["transaction_id"]
    replayed_init = authenticated_client.post("/api/payments/initiate/", {"order_id": order_data["id"]},
                                              format="json", HTTP_IDEMPOTENCY_KEY=KEY)
    assert replayed_init.status_code == status.HTTP_200_OK
    assert replayed_init.json() == attempt

    # 4. Cross-owner approval is masked: state unchanged, nothing leaked.
    other = APIClient()
    other.force_authenticate(user=UserFactory.create())
    denied = other.post(f"/api/payments/{transaction_id}/mock-approve/")
    assert denied.status_code == status.HTTP_404_NOT_FOUND
    assert _transaction_model().objects.get(id=transaction_id).status == "PENDING"

    # 5. Owned approval exactly once; cart clears ONLY purchased quantities.
    with TestCase.captureOnCommitCallbacks(execute=True):
        approved = authenticated_client.post(f"/api/payments/{transaction_id}/mock-approve/")
    assert approved.status_code == status.HTTP_200_OK
    assert approved.json() == {"transaction_id": transaction_id,
                               "order_id": order_data["id"],
                               "status": "APPROVED", "order_status": "PAID"}
    with TestCase.captureOnCommitCallbacks(execute=True):
        re_approved = authenticated_client.post(f"/api/payments/{transaction_id}/mock-approve/")
    assert re_approved.status_code == status.HTTP_200_OK
    assert re_approved.json() == approved.json()
    order = Order.objects.get(id=order_data["id"])
    assert order.status == "PAID"
    assert _transaction_model().objects.filter(order=order).count() == 1
    cart.refresh_from_db()
    assert cart.items.count() == 1
    assert cart.items.get().product_id == unrelated.id  # unrelated item intact

    # 6. Dispatch + durable notifications (payment confirmation + dispatch).
    with TestCase.captureOnCommitCallbacks(execute=True):
        order = fulfill_dispatch(order=order, carrier="Chilexpress",
                                 estimated_delivery_date=date.today() + timedelta(days=4))
    assert order.status == "SHIPPED"
    assert NotificationDelivery.objects.get(order=order, event="payment_confirmation").status == "SENT"
    assert NotificationDelivery.objects.get(order=order, event="dispatch").status == "SENT"
    assert len(mail.outbox) == 2
    assert mail.outbox[0].to == [user.email]


def test_payment_initiation_fails_closed_outside_development(
        authenticated_client, user, order_factory):
    """Production (DEBUG off) fails closed: no provider, state unchanged."""
    order = order_factory(user=user, status="PENDING", total=30000)

    with override_settings(DEBUG=False, PAYMENT_PROVIDER="mock"):
        response = authenticated_client.post("/api/payments/initiate/",
                                             {"order_id": order.id}, format="json")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    order.refresh_from_db()
    assert order.status == "PENDING"
    assert not _transaction_model().objects.filter(order=order).exists()


def test_mock_approve_fails_closed_outside_development(
        authenticated_client, user, order_factory):
    """Production (DEBUG off) denies mock approval too: same fail-closed
    contract as initiation (503 + detail), owned attempt stays PENDING."""
    order = order_factory(user=user, status="PENDING", total=30000)
    attempt = _transaction_model().objects.create(
        order=order, amount=order.total, status="PENDING",
        gateway_reference="token_prod_denied", payment_method="webpay",
        provider="mock",
    )

    with override_settings(DEBUG=False, PAYMENT_PROVIDER="mock"):
        response = authenticated_client.post(
            f"/api/payments/{attempt.id}/mock-approve/")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Payment service unavailable."}
    attempt.refresh_from_db()
    assert attempt.status == "PENDING"
    order.refresh_from_db()
    assert order.status == "PENDING"
    assert not _transaction_model().objects.filter(order=order, status="APPROVED").exists()
