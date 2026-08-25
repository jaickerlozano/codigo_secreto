"""Retry-engine and command tests for notification deliveries."""
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from apps.orders.models import NotificationDelivery
from apps.orders.notifications import attempt_delivery, schedule_delivery, RETRY_DELAY_MINUTES, STALE_PENDING_MINUTES
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


def _run_command(**kwargs):
    out = StringIO()
    call_command("process_notifications", stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.parametrize("batch_size", [0, -1])
@pytest.mark.django_db(transaction=True)
def test_command_rejects_non_positive_batch_size(batch_size):
    with pytest.raises(CommandError):
        call_command("process_notifications", batch_size=batch_size)


@pytest.mark.django_db(transaction=True)
def test_command_empty_run_prints_zero_totals():
    output = _run_command()
    for key in ("selected", "attempted", "sent", "failed", "exhausted", "skipped"):
        assert f"{key}=0" in output


@pytest.mark.django_db(transaction=True)
def test_command_selects_due_and_stale_and_skips_others(order):
    now = timezone.now()
    due = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=1, next_retry_at=now
    )
    future = NotificationDelivery.objects.create(
        order=order, event="dispatch", status="FAILED", attempts=1,
        next_retry_at=now + timezone.timedelta(hours=1),
    )
    stale = NotificationDelivery.objects.create(order=OrderFactory(), event="payment_confirmation", status="PENDING", attempts=0)
    NotificationDelivery.objects.filter(pk=stale.pk).update(
        updated_at=now - timezone.timedelta(minutes=STALE_PENDING_MINUTES + 1)
    )
    NotificationDelivery.objects.create(order=OrderFactory(), event="payment_confirmation", status="SENT", attempts=1, sent_at=now)
    NotificationDelivery.objects.create(order=OrderFactory(), event="payment_confirmation", status="FAILED", attempts=5)
    fresh = NotificationDelivery.objects.create(order=OrderFactory(), event="payment_confirmation", status="PENDING", attempts=0)
    with patch("apps.orders.notifications.send_mail", return_value=1):
        output = _run_command()
    due.refresh_from_db(); stale.refresh_from_db(); fresh.refresh_from_db(); future.refresh_from_db()
    assert due.status == "SENT" and stale.status == "SENT"
    assert fresh.status == "PENDING" and future.status == "FAILED"
    assert "selected=2" in output and "sent=2" in output


@pytest.mark.django_db(transaction=True)
def test_command_batch_size_limits_selection(order):
    now = timezone.now()
    for _ in range(3):
        NotificationDelivery.objects.create(
            order=OrderFactory(), event="payment_confirmation", status="FAILED", attempts=1, next_retry_at=now
        )
    with patch("apps.orders.notifications.send_mail", return_value=1):
        output = _run_command(batch_size=2)
    assert "selected=2" in output and "sent=2" in output
    assert NotificationDelivery.objects.filter(status="SENT").count() == 2


@pytest.mark.django_db(transaction=True)
def test_command_failed_send_counts_failed_and_exhausted(order):
    now = timezone.now()
    retry = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=1, next_retry_at=now
    )
    last = NotificationDelivery.objects.create(
        order=OrderFactory(), event="dispatch", status="FAILED", attempts=4, next_retry_at=now
    )
    with patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("boom")):
        output = _run_command()
    retry.refresh_from_db(); last.refresh_from_db()
    assert retry.status == "FAILED" and retry.attempts == 2 and retry.next_retry_at is not None
    assert last.status == "FAILED" and last.attempts == 5 and last.next_retry_at is None and last.exhausted
    assert "selected=2" in output and "attempted=2" in output
    assert "failed=1" in output and "exhausted=1" in output
