"""Retry-engine, command, concurrency, and admin tests for notification deliveries."""
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Event, Lock
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections, connection, transaction
from django.utils import timezone

from apps.orders.admin import ExhaustedFilter, NotificationDeliveryAdmin
from apps.orders.models import NotificationDelivery
from apps.orders.notifications import attempt_delivery, schedule_delivery, RETRY_DELAY_MINUTES, STALE_PENDING_MINUTES
from apps.orders.tests.factories import OrderFactory, faker


pytestmark = pytest.mark.django_db


@pytest.fixture
def order():
    return OrderFactory(guest_email="guest@example.test")


def test_order_factory_phone_fits_database_column(monkeypatch):
    monkeypatch.setattr(faker, "phone_number", lambda: "1" * 21)

    order = OrderFactory.build()

    assert order.phone == "1" * 20


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


@pytest.fixture
def delivery_admin():
    return NotificationDeliveryAdmin(NotificationDelivery, AdminSite())


@pytest.fixture
def admin_request(rf):
    request = rf.get("/admin/orders/notificationdelivery/")
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.pg_only
@pytest.mark.django_db(transaction=True)
def test_postgresql_two_connections_exactly_one_send(order):
    now = timezone.now()
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=1, next_retry_at=now
    )
    entered_send = Event()
    release_send = Event()
    send_count = 0
    send_lock = Lock()

    def blocking_send(*args, **kwargs):
        nonlocal send_count
        with send_lock:
            send_count += 1
        entered_send.set()
        assert release_send.wait(timeout=5)
        return 1

    def worker():
        close_old_connections()
        try:
            return attempt_delivery(delivery.id, trigger="automatic", now=now)
        finally:
            close_old_connections()

    with patch("apps.orders.notifications.send_mail", side_effect=blocking_send):
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(worker)
            assert entered_send.wait(timeout=5)
            future2 = executor.submit(worker)
            future2.result(timeout=2)
            release_send.set()
            future1.result(timeout=5)

    delivery.refresh_from_db()
    assert send_count == 1
    assert delivery.status == "SENT"
    assert delivery.attempts == 2


@pytest.mark.skipif(connection.vendor == "postgresql", reason="SQLite-specific contention behaviour")
@pytest.mark.django_db(transaction=True)
def test_sqlite_lock_contention_prevents_duplicate_send(order):
    now = timezone.now()
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=1, next_retry_at=now
    )
    entered_send = Event()
    release_send = Event()
    send_count = 0
    send_lock = Lock()

    def blocking_send(*args, **kwargs):
        nonlocal send_count
        with send_lock:
            send_count += 1
        entered_send.set()
        assert release_send.wait(timeout=5)
        return 1

    def worker():
        close_old_connections()
        try:
            return attempt_delivery(delivery.id, trigger="automatic", now=now)
        finally:
            close_old_connections()

    with patch("apps.orders.notifications.send_mail", side_effect=blocking_send):
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(worker)
            assert entered_send.wait(timeout=5)
            future2 = executor.submit(worker)
            assert future2.result(timeout=5) is None
            release_send.set()
            future1.result(timeout=5)

    delivery.refresh_from_db()
    assert send_count == 1
    assert delivery.status == "SENT"
    assert delivery.attempts == 2


@pytest.mark.parametrize("attempts,expected", [(5, True), (4, False)])
def test_admin_exhausted_display(delivery_admin, order, attempts, expected):
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=attempts
    )
    assert delivery_admin.is_exhausted(delivery) is expected


@pytest.mark.parametrize("choice,expected_count", [("1", 1), ("0", 0)])
def test_admin_exhausted_filter(delivery_admin, order, choice, expected_count):
    NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=5
    )
    filter_obj = ExhaustedFilter(None, {"exhausted": choice}, NotificationDelivery, delivery_admin)
    assert filter_obj.queryset(None, NotificationDelivery.objects.all()).count() == expected_count


def test_admin_retry_action_sends_exhausted_delivery(delivery_admin, admin_request, order):
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=5
    )
    with patch("apps.orders.notifications.send_mail", return_value=1):
        delivery_admin.retry_failed(admin_request, NotificationDelivery.objects.filter(pk=delivery.pk))
    delivery.refresh_from_db()
    assert delivery.status == "SENT" and delivery.attempts == 6


def test_admin_failed_manual_retry_remains_exhausted(delivery_admin, admin_request, order, caplog):
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=5
    )
    with patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("boom")):
        delivery_admin.retry_failed(admin_request, NotificationDelivery.objects.filter(pk=delivery.pk))
    delivery.refresh_from_db()
    assert delivery.status == "FAILED" and delivery.attempts == 6
    assert delivery.exhausted and delivery.next_retry_at is None
    assert "exhausted" in caplog.text.lower()


def test_failure_log_contains_delivery_identity(order, caplog):
    now = timezone.now()
    delivery = NotificationDelivery.objects.create(
        order=order, event="payment_confirmation", status="FAILED", attempts=1, next_retry_at=now
    )
    with patch("apps.orders.notifications.send_mail", side_effect=RuntimeError("boom")):
        attempt_delivery(delivery.id, now=now)
    assert order.order_number in caplog.text
    assert str(delivery.id) in caplog.text
    assert "attempt=2" in caplog.text
