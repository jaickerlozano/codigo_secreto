"""Migration reversibility tests for the shipping app (Unit 2)."""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BASELINE = ("shipping", "0003_alter_comuna_name_alter_comuna_region_and_more")
TARGET = ("shipping", "0004_regional_shipping_option")

# Django default table name: app label + lowercased model name, no separators.
TABLE = "shipping_regionalshippingoption"
NEW_FIELDS = ("key", "carrier", "tariff", "min_lead_days", "max_lead_days", "is_active")


def _table_columns(table_name):
    return {
        column.name
        for column in connection.introspection.get_table_description(
            connection.cursor(), table_name
        )
    }


@pytest.mark.django_db(transaction=True)
def test_shipping_0004_adds_regional_option_table_and_is_reversible():
    # Fresh executor per direction: the loader caches applied migrations.
    executor = MigrationExecutor(connection)
    executor.migrate([BASELINE])
    assert TABLE not in connection.introspection.table_names()
    executor = MigrationExecutor(connection)
    executor.migrate([TARGET])
    assert TABLE in connection.introspection.table_names()
    assert all(field in _table_columns(TABLE) for field in NEW_FIELDS)
    state = executor.loader.project_state([TARGET])
    option_model = state.apps.get_model("shipping", "RegionalShippingOption")
    assert option_model._meta.get_field("key").unique
