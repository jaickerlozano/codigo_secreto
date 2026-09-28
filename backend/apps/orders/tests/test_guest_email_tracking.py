from datetime import date
from unittest.mock import patch

import pytest
from django.core import signing
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import NotificationDelivery
from apps.orders.notifications import _body, attempt_delivery
from apps.orders.services import (
    GUEST_EMAIL_ACCESS_MAX_AGE,
    GUEST_EMAIL_ACCESS_PURPOSE,
    GUEST_EMAIL_ACCESS_SALT,
    issue_guest_email_access_ticket,
    verify_guest_email_access_ticket,
)
from apps.orders.tests.factories import OrderFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def guest_order():
    order = OrderFactory(user=None, guest_email="guest@example.test", estimated_delivery_date=date.today())
    order.issue_guest_access()
    return order


def _ticket_from_body(body):
    return body.split("#access=", 1)[1]


@override_settings(ORDER_TRACKING_PUBLIC_ORIGIN="http://localhost:5173")
def test_payment_confirmation_includes_email_ticket_only_for_guest_orders(guest_order):
    ticket = _ticket_from_body(_body("payment_confirmation", guest_order))

    payload = signing.loads(ticket, salt=GUEST_EMAIL_ACCESS_SALT, max_age=GUEST_EMAIL_ACCESS_MAX_AGE)

    assert payload == {
        "order_id": guest_order.id,
        "purpose": GUEST_EMAIL_ACCESS_PURPOSE,
        "version": guest_order.guest_email_access_version,
    }
    assert f"http://localhost:5173/order/{guest_order.order_number}#access={ticket}" in _body("payment_confirmation", guest_order)
    assert "#access=" not in _body("dispatch", guest_order)
    assert "#access=" not in _body("payment_confirmation", OrderFactory())


def test_email_ticket_exchanges_only_through_the_existing_header_and_returns_no_body(guest_order):
    ticket = issue_guest_email_access_ticket(guest_order)
    client = APIClient()

    exchanged = client.post(
        f"/api/orders/by-order-number/{guest_order.order_number}/access/",
        {}, format="json", HTTP_X_ORDER_CAPABILITY=ticket,
    )

    assert exchanged.status_code == status.HTTP_204_NO_CONTENT
    assert exchanged.content == b""
    assert "guest_order_access" in exchanged.cookies
    client.cookies["guest_order_access"] = exchanged.cookies["guest_order_access"].value
    assert client.get(f"/api/orders/by-order-number/{guest_order.order_number}/").status_code == status.HTTP_200_OK
    assert client.post(f"/api/orders/by-order-number/{guest_order.order_number}/access/?access={ticket}").status_code == status.HTTP_404_NOT_FOUND


def test_email_ticket_is_masked_when_tampered_expired_revoked_or_foreign(guest_order):
    ticket = issue_guest_email_access_ticket(guest_order)
    other_order = OrderFactory(user=None, guest_email="other@example.test")
    other_ticket = issue_guest_email_access_ticket(other_order)
    client = APIClient()
    endpoint = f"/api/orders/by-order-number/{guest_order.order_number}/access/"

    assert client.post(endpoint, {}, format="json", HTTP_X_ORDER_CAPABILITY=f"{ticket}x").status_code == status.HTTP_404_NOT_FOUND
    assert client.post(endpoint, {}, format="json", HTTP_X_ORDER_CAPABILITY=other_ticket).status_code == status.HTTP_404_NOT_FOUND
    with patch("django.core.signing.time.time", return_value=signing.time.time() + GUEST_EMAIL_ACCESS_MAX_AGE + 1):
        assert client.post(endpoint, {}, format="json", HTTP_X_ORDER_CAPABILITY=ticket).status_code == status.HTTP_404_NOT_FOUND
    guest_order.revoke_guest_email_access()
    assert client.post(endpoint, {}, format="json", HTTP_X_ORDER_CAPABILITY=ticket).status_code == status.HTTP_404_NOT_FOUND


def test_email_ticket_version_bump_invalidates_every_prior_ticket(guest_order):
    ticket = issue_guest_email_access_ticket(guest_order)

    guest_order.bump_guest_email_access_version()

    assert not verify_guest_email_access_ticket(guest_order, ticket)
    assert verify_guest_email_access_ticket(guest_order, issue_guest_email_access_ticket(guest_order))


def test_notification_retry_keeps_email_ticket_version_stable_and_redacts_delivery_errors(guest_order):
    delivery = NotificationDelivery.objects.create(order=guest_order, event="payment_confirmation")
    opaque_version = guest_order.guest_access_version
    email_version = guest_order.guest_email_access_version
    sent_bodies = []

    def fail_with_email_body(*args):
        raise RuntimeError(args[1])

    with patch("apps.orders.notifications.send_mail", side_effect=fail_with_email_body):
        attempt_delivery(delivery.id, trigger="initial")
    delivery.refresh_from_db()

    assert delivery.status == "FAILED"
    assert delivery.last_error == "Email delivery failed."
    assert "#access=" not in delivery.last_error
    with patch("apps.orders.notifications.send_mail", side_effect=lambda *args: sent_bodies.append(args[1]) or 1):
        attempt_delivery(delivery.id, trigger="manual")
    delivery.refresh_from_db()
    guest_order.refresh_from_db()

    assert delivery.status == "SENT"
    assert delivery.attempts == 2
    assert guest_order.guest_access_version == opaque_version
    assert guest_order.guest_email_access_version == email_version
    assert verify_guest_email_access_ticket(guest_order, _ticket_from_body(sent_bodies[0]))
