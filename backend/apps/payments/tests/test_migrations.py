"""Migration reversibility tests for the payments app (Unit 1).

These tests prove the new Transaction idempotency/provider migration can be
applied forward and reversed backward on a real database, and that the
forward state carries the unique (order, idempotency_key) constraint.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BASELINE = ("payments", "0001_initial")
TARGET = ("payments", "0002_transaction_idempotency_provider")


def _table_columns(table_name):
    return {
        column.name
        for column in connection.introspection.get_table_description(
            connection.cursor(), table_name
        )
    }


@pytest.mark.django_db(transaction=True)
def test_payments_0002_adds_idempotency_fields_and_is_reversible():
    # A fresh executor per direction re-reads applied migrations; the loader
    # caches them at construction, so reusing one executor skips the forward.
    executor = MigrationExecutor(connection)

    # Backward: the pre-change schema has no idempotency columns.
    executor.migrate([BASELINE])
    columns = _table_columns("payments_transaction")
    assert "idempotency_key" not in columns
    assert "provider" not in columns

    # Forward: the new migration adds both columns and the constraint.
    executor = MigrationExecutor(connection)
    executor.migrate([TARGET])
    columns = _table_columns("payments_transaction")
    assert "idempotency_key" in columns
    assert "provider" in columns

    state = executor.loader.project_state([TARGET])
    transaction_model = state.apps.get_model("payments", "Transaction")
    constraint_names = {constraint.name for constraint in transaction_model._meta.constraints}
    assert "unique_transaction_order_idempotency_key" in constraint_names
