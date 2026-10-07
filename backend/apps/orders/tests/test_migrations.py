"""Migration reversibility tests for the orders app.

These tests cover order lifecycle fields and notification delivery schema/state
changes while preserving existing rows across forward and reverse migrations.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.shipping.tests.factories import ComunaFactory

BASELINE = ("orders", "0004_order_guest_access_digest_and_more")
TARGET = ("orders", "0005_order_checkout_delivery_fields")
BASELINE_0006 = ("orders", "0006_notificationdelivery")
TARGET_0007 = ("orders", "0007_notificationdelivery_due_index")
TARGET_0009 = ("orders", "0009_order_delivered_at")
TARGET_0010 = ("orders", "0010_order_guest_email_access")
TARGET_0011 = ("orders", "0011_alter_notificationdelivery_event")
TARGET_0012 = ("orders", "0012_alter_notificationdelivery_event")
LATEST = ('orders', '0013_order_cancellation_reason')
TARGET_0013 = ('orders', '0013_order_cancellation_reason')
INDEX_NAME = "orders_notif_status_next_retry"

NEW_COLUMNS = (
    "checkout_key",
    "delivery_kind",
    "requested_dispatch_date",
    "special_delivery_agreed_at",
    "estimated_delivery_date",
    "dispatched_at",
)


def _table_columns(table_name):
    return {
        column.name
        for column in connection.introspection.get_table_description(
            connection.cursor(), table_name
        )
    }


def _index_names(table_name):
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table_name)
    return {name for name, details in constraints.items() if details["index"]}


@pytest.mark.django_db(transaction=True)
def test_orders_0005_adds_checkout_and_delivery_fields_and_is_reversible():
    # A fresh executor per direction re-reads applied migrations; the loader
    # caches them at construction, so reusing one executor skips the forward.
    executor = MigrationExecutor(connection)

    # Backward: the pre-change schema has none of the new columns.
    executor.migrate([BASELINE])
    columns = _table_columns("orders_order")
    assert all(column not in columns for column in NEW_COLUMNS)

    # Forward: the new migration adds every checkout/delivery/dispatch column.
    executor = MigrationExecutor(connection)
    executor.migrate([TARGET])
    columns = _table_columns("orders_order")
    assert all(column in columns for column in NEW_COLUMNS)

    state = executor.loader.project_state([TARGET])
    order_model = state.apps.get_model("orders", "Order")
    assert order_model._meta.get_field("checkout_key").unique
    MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.django_db(transaction=True)
def test_orders_0007_adds_due_index_and_is_reversible():
    from apps.orders.models import NotificationDelivery

    try:
        executor = MigrationExecutor(connection)
        executor.migrate([BASELINE_0006])
        assert INDEX_NAME not in _index_names("orders_notificationdelivery")

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0007])
        assert INDEX_NAME in _index_names("orders_notificationdelivery")

        order_model = executor.loader.project_state([TARGET_0007]).apps.get_model("orders", "Order")
        comuna = ComunaFactory()
        order = order_model.objects.create(
            phone="+56912345678",
            comuna_id=comuna.id,
            shipping_address="Example 123",
            subtotal=1000,
            shipping_cost=1000,
            total=2000,
            status="CANCELLED",
        )
        created = NotificationDelivery.objects.create(
            order_id=order.id,
            event="payment_confirmation",
            status="FAILED",
            attempts=1,
            next_retry_at=timezone.now(),
        )

        executor = MigrationExecutor(connection)
        executor.migrate([BASELINE_0006])
        assert INDEX_NAME not in _index_names("orders_notificationdelivery")
        assert NotificationDelivery.objects.filter(pk=created.pk).exists()

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0007])
        assert INDEX_NAME in _index_names("orders_notificationdelivery")
        assert NotificationDelivery.objects.filter(pk=created.pk).exists()
    finally:
        MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.django_db(transaction=True)
def test_orders_0009_adds_delivered_timestamp_and_is_reversible():
    try:
        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0007])
        assert "delivered_at" not in _table_columns("orders_order")

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0009])
        assert "delivered_at" in _table_columns("orders_order")

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0007])
        assert "delivered_at" not in _table_columns("orders_order")
    finally:
        MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.django_db(transaction=True)
def test_orders_0010_adds_email_access_revocation_fields_and_is_reversible():
    try:
        MigrationExecutor(connection).migrate([TARGET_0009])
        columns = _table_columns("orders_order")
        assert "guest_email_access_version" not in columns
        assert "guest_email_access_revoked_at" not in columns

        MigrationExecutor(connection).migrate([TARGET_0010])
        columns = _table_columns("orders_order")
        assert "guest_email_access_version" in columns
        assert "guest_email_access_revoked_at" in columns
    finally:
        MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.django_db(transaction=True)
def test_orders_0011_adds_delivered_notification_event_and_is_reversible():
    try:
        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0010])
        state = executor.loader.project_state([TARGET_0010])
        field = state.apps.get_model("orders", "NotificationDelivery")._meta.get_field("event")
        assert "delivered" not in dict(field.choices)

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0011])
        state = executor.loader.project_state([TARGET_0011])
        field = state.apps.get_model("orders", "NotificationDelivery")._meta.get_field("event")
        assert dict(field.choices)["delivered"] == "Entrega del Pedido"

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0010])
        state = executor.loader.project_state([TARGET_0010])
        field = state.apps.get_model("orders", "NotificationDelivery")._meta.get_field("event")
        assert "delivered" not in dict(field.choices)
    finally:
        MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.django_db(transaction=True)
def test_orders_0012_adds_cancelled_event_without_backfill_and_is_reversible():
    try:
        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0011])
        state = executor.loader.project_state([TARGET_0011])
        delivery_model = state.apps.get_model("orders", "NotificationDelivery")
        assert "cancelled" not in dict(delivery_model._meta.get_field("event").choices)
        order_model = state.apps.get_model("orders", "Order")
        order = order_model.objects.create(
            comuna_id=ComunaFactory().pk, phone="56912345678", shipping_address="Example 123",
            subtotal=1000, shipping_cost=1000, total=2000, status="CANCELLED",
        )
        existing = delivery_model.objects.create(order_id=order.pk, event="payment_confirmation", status="SENT")

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0012])
        delivery_model = executor.loader.project_state([TARGET_0012]).apps.get_model("orders", "NotificationDelivery")
        assert dict(delivery_model._meta.get_field("event").choices)["cancelled"] == "Cancelación del Pedido"
        assert list(delivery_model.objects.filter(order_id=order.pk).values_list("pk", "event")) == [
            (existing.pk, "payment_confirmation")
        ]
        cancelled = delivery_model.objects.create(order_id=order.pk, event="cancelled")

        executor = MigrationExecutor(connection)
        executor.migrate([TARGET_0011])
        delivery_model = executor.loader.project_state([TARGET_0011]).apps.get_model("orders", "NotificationDelivery")
        assert "cancelled" not in dict(delivery_model._meta.get_field("event").choices)
        assert delivery_model.objects.filter(pk=cancelled.pk, event="cancelled").exists()
        assert delivery_model.objects.filter(pk=existing.pk, status="SENT").exists()
    finally:
        MigrationExecutor(connection).migrate([LATEST])
