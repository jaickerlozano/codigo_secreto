"""Retry-engine unit tests for notification deliveries (Unit 1)."""
import pytest
from django.db import transaction
from django.utils import timezone
from unittest.mock import patch

from apps.orders.models import NotificationDelivery
from apps.orders.notifications import attempt_delivery, schedule_delivery, RETRY_DELAY_MINUTES
from apps.orders.tests.factories import OrderFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def order():
    return OrderFactory(guest_email="guest@example.test")


def test_schedule_rejects_unsupported_event(order, caplog):
    assert schedule_delivery(order, "unknown") is None
    assert not NotificationDelivery.objects.filter(order=order, event="unknown").exists()
    assert "Unsupported" in caplog.text


@pytest.mark.django_db(transaction=True)
def test_schedule_creates_and_sends(order):
    with patch("apps.orders.notifications.send_mail", return_value=1) as mock:
        with transaction.atomic():
            delivery = schedule_delivery(order, "payment_confirmation")
    delivery.refresh_from_db()
    assert delivery.status == "SENT" and delivery.attempts == 1
    mock.assert_called_once()


@pytest.mark.parametrize("before_attempts,expected_delay", [
    (0, 15), (1, 60), (2, 240), (3, 720), (4, None),
])
def test_failed_attempt_schedules_delay_or_exhausts(order, before_attempts, expected_delay, caplog):
    now = timezone.now()
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=before_attempts, next_retry_at=now
    )
    with patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("boom")):
        attempt_delivery(delivery.id, now=now)
    delivery.refresh_from_db()
    assert delivery.attempts == before_attempts + 1
    if expected_delay is None:
        assert delivery.next_retry_at is None and delivery.exhausted and "exhausted" in caplog.text.lower()
    else:
        assert delivery.next_retry_at == now + timezone.timedelta(minutes=expected_delay)


def test_sent_guard(order):
    now = timezone.now()
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="SENT", attempts=1, sent_at=now
    )
    with patch("apps.orders.notifications.send_mail") as mock:
        attempt_delivery(delivery.id, now=now)
    mock.assert_not_called()
    delivery.refresh_from_db()
    assert delivery.attempts == 1
