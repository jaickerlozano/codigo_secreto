"""Migration reversibility tests for the orders app (Unit 1).

These tests prove the new Order checkout/delivery/dispatch migration can be
applied forward and reversed backward on a real database, and that the
forward state carries the unique checkout_key.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BASELINE = ("orders", "0004_order_guest_access_digest_and_more")
TARGET = ("orders", "0005_order_checkout_delivery_fields")

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
