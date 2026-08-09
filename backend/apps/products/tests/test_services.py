from dataclasses import FrozenInstanceError
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.db import connection, transaction
from django.db import close_old_connections
from django.test.utils import CaptureQueriesContext

from apps.products.services import (
    ProductPriceSnapshot,
    resolve_product_price_snapshot,
)


pytestmark = pytest.mark.django_db


def test_product_price_snapshot_is_frozen():
    snapshot = ProductPriceSnapshot(id=7, name="Intimate product", unit_price=12500)

    assert snapshot == ProductPriceSnapshot(7, "Intimate product", 12500)
    with pytest.raises(FrozenInstanceError):
        snapshot.unit_price = 1


def test_resolve_product_price_snapshot_returns_id_keyed_map_in_one_query(
    product_factory, django_assert_num_queries
):
    first = product_factory(name="First product", price=12000)
    second = product_factory(name="Second product", price=18000)

    with django_assert_num_queries(1):
        snapshots = resolve_product_price_snapshot([second.id, first.id])

    assert snapshots == {
        first.id: ProductPriceSnapshot(first.id, "First product", 12000),
        second.id: ProductPriceSnapshot(second.id, "Second product", 18000),
    }


def test_resolve_product_price_snapshot_masks_unknown_identifier(product_factory):
    product = product_factory()

    with pytest.raises(LookupError) as error:
        resolve_product_price_snapshot([product.id, 987654321])

    assert "987654321" not in str(error.value)


def test_locked_product_snapshot_requires_atomic_caller(
    product_factory, django_assert_num_queries
):
    product = product_factory()

    with django_assert_num_queries(0), pytest.raises(RuntimeError, match="atomic"):
        resolve_product_price_snapshot([product.id], for_update=True)


def test_locked_product_snapshot_orders_ids_before_query(
    product_factory, django_assert_num_queries
):
    first = product_factory()
    second = product_factory()

    with CaptureQueriesContext(connection) as queries:
        with transaction.atomic():
            snapshots = resolve_product_price_snapshot(
                [second.id, first.id], for_update=True
            )

    assert set(snapshots) == {first.id, second.id}
    select_queries = [query["sql"] for query in queries if query["sql"].lstrip().upper().startswith("SELECT")]
    assert len(select_queries) == 1
    assert 'ORDER BY "products_product"."id" ASC' in select_queries[0]


@pytest.mark.pg_only
@pytest.mark.django_db(transaction=True)
def test_concurrent_locked_product_resolution_serializes_on_same_order(
    product_factory,
):
    first = product_factory()
    second = product_factory()
    first_locked = Event()
    release_first = Event()
    second_finished = Event()

    def hold_first_lock():
        close_old_connections()
        try:
            with transaction.atomic():
                resolve_product_price_snapshot(
                    [second.id, first.id], for_update=True
                )
                first_locked.set()
                assert release_first.wait(timeout=5)
        finally:
            close_old_connections()

    def acquire_second_lock():
        close_old_connections()
        try:
            with transaction.atomic():
                resolve_product_price_snapshot(
                    [first.id, second.id], for_update=True
                )
                second_finished.set()
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(hold_first_lock)
        assert first_locked.wait(timeout=5)
        second_future = executor.submit(acquire_second_lock)
        assert not second_finished.wait(timeout=0.2)
        release_first.set()
        first_future.result(timeout=5)
        second_future.result(timeout=5)

    assert second_finished.is_set()
