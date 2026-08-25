"""Migration reversibility tests for the orders app.

These tests prove the new Order checkout/delivery/dispatch migration and the
notification-delivery due index can be applied forward and reversed without
changing existing rows.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.orders.tests.factories import OrderFactory

BASELINE = ("orders", "0004_order_guest_access_digest_and_more")
TARGET = ("orders", "0005_order_checkout_delivery_fields")
BASELINE_0006 = ("orders", "0006_notificationdelivery")
TARGET_0007 = ("orders", "0007_notificationdelivery_due_index")
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

        order = OrderFactory()
        created = NotificationDelivery.objects.create(
            order=order,
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
        MigrationExecutor(connection).migrate([TARGET_0007])
