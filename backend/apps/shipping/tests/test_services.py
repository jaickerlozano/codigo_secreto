from dataclasses import FrozenInstanceError

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from apps.shipping.services import (
    ComunaShippingSnapshot,
    resolve_comuna_shipping_snapshot,
)


pytestmark = pytest.mark.django_db


def test_comuna_shipping_snapshot_is_frozen():
    snapshot = ComunaShippingSnapshot(
        id=7,
        name="Providencia",
        region_name="Metropolitana",
        shipping_cost=3500,
    )

    assert snapshot.shipping_cost == 3500
    with pytest.raises(FrozenInstanceError):
        snapshot.shipping_cost = 1


def test_resolve_comuna_by_id_uses_one_related_query(
    comuna_factory, region_factory, django_assert_num_queries
):
    region = region_factory(name="Metropolitana")
    comuna = comuna_factory(name="Providencia", region=region, shipping_cost=3500)

    with django_assert_num_queries(1):
        snapshot = resolve_comuna_shipping_snapshot(comuna_id=comuna.id)

    assert snapshot == ComunaShippingSnapshot(
        comuna.id, "Providencia", "Metropolitana", 3500
    )


def test_resolve_comuna_by_name_and_region_and_absent_selector(
    comuna_factory, region_factory, django_assert_num_queries
):
    region = region_factory(name="Valparaiso")
    comuna = comuna_factory(name="Vina del Mar", region=region, shipping_cost=4200)

    with django_assert_num_queries(1):
        snapshot = resolve_comuna_shipping_snapshot(
            comuna_name="Vina del Mar", region_name="Valparaiso"
        )

    assert snapshot.id == comuna.id
    with django_assert_num_queries(0):
        assert resolve_comuna_shipping_snapshot() is None


def test_resolve_comuna_masks_unknown_selector(comuna_factory):
    comuna_factory(name="Known comuna")

    with pytest.raises(LookupError) as error:
        resolve_comuna_shipping_snapshot(
            comuna_name="Secret missing comuna", region_name="Secret region"
        )

    assert "Secret missing comuna" not in str(error.value)
    assert "Secret region" not in str(error.value)


def test_locked_shipping_snapshot_requires_atomic_caller(
    comuna_factory, django_assert_num_queries
):
    comuna = comuna_factory()

    with django_assert_num_queries(0), pytest.raises(RuntimeError, match="atomic"):
        resolve_comuna_shipping_snapshot(comuna_id=comuna.id, for_update=True)


def test_locked_shipping_snapshot_runs_inside_atomic_caller(
    comuna_factory, django_assert_num_queries
):
    comuna = comuna_factory()

    with CaptureQueriesContext(connection) as queries:
        with transaction.atomic():
            snapshot = resolve_comuna_shipping_snapshot(
                comuna_id=comuna.id, for_update=True
            )

    assert snapshot.id == comuna.id
    assert len([query for query in queries if query["sql"].lstrip().upper().startswith("SELECT")]) == 1
