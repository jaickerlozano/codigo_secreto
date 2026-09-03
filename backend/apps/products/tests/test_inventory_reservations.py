from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, transaction
from django.utils import timezone

from apps.products.models import InventoryReservation, StockMovement
from apps.products.services import (
    InsufficientAvailableStock,
    ReservationLineInput,
    commit,
    inspect,
    release,
    reserve,
)


pytestmark = pytest.mark.django_db


def _line(product, quantity):
    return ReservationLineInput(product_id=product.id, quantity=quantity)


def _reserve(order_id, product, quantity, expires_at):
    return reserve(
        order_id=order_id,
        lines=(_line(product, quantity),),
        expires_at=expires_at,
    )


def test_reserve_keeps_physical_stock_and_exposes_a_scalar_order_id(product_factory):
    product = product_factory(current_stock=10)
    now = timezone.now()
    expires_at = now + timedelta(minutes=15)

    with transaction.atomic():
        snapshot = _reserve(101, product, 6, expires_at)
        inspected = inspect(order_id=101, at=now)

    product.refresh_from_db()
    reservation = InventoryReservation.objects.get(order_id=101)
    assert snapshot.status == inspected.status == reservation.status == "ACTIVE"
    assert snapshot.expires_at == expires_at
    assert inspected.lines == (ReservationLineInput(product.id, 6),)
    assert reservation.order_id == 101
    assert "order" not in {field.name for field in reservation._meta.fields}
    assert product.current_stock == 10


def test_active_holds_limit_reservations_and_generic_out_movements(product_factory):
    product = product_factory(current_stock=10)
    expires_at = timezone.now() + timedelta(minutes=15)

    with transaction.atomic():
        _reserve(102, product, 6, expires_at)
    with transaction.atomic(), pytest.raises(InsufficientAvailableStock):
        _reserve(103, product, 5, expires_at)
    with pytest.raises(ValidationError):
        StockMovement.objects.create(product=product, movement_type="OUT", quantity=5)

    product.refresh_from_db()
    assert product.current_stock == 10
    assert StockMovement.objects.filter(product=product).count() == 0


def test_release_is_idempotent_and_never_creates_an_out_movement(product_factory):
    product = product_factory(current_stock=10)
    now = timezone.now()

    with transaction.atomic():
        _reserve(104, product, 6, now + timedelta(minutes=15))
        released = release(order_id=104, reason="CANCELLED", at=now)
        retried = release(order_id=104, reason="CANCELLED", at=now + timedelta(seconds=1))

    assert released == retried
    assert released.status == "RELEASED"
    assert released.release_reason == "CANCELLED"
    assert StockMovement.objects.filter(product=product).count() == 0


def test_commit_is_idempotent_and_creates_one_immutable_out_movement(product_factory):
    product = product_factory(current_stock=10)
    now = timezone.now()

    with transaction.atomic():
        _reserve(105, product, 6, now + timedelta(minutes=15))
        committed = commit(order_id=105, at=now)
        retried = commit(order_id=105, at=now + timedelta(seconds=1))

    product.refresh_from_db()
    assert committed == retried
    assert committed.status == "COMMITTED"
    assert product.current_stock == 4
    assert StockMovement.objects.filter(product=product, movement_type="OUT", quantity=6).count() == 1


def test_inspect_and_commit_fail_closed_for_expired_holds(product_factory):
    product = product_factory(current_stock=10)
    expires_at = timezone.now() + timedelta(minutes=15)

    with transaction.atomic():
        _reserve(106, product, 3, expires_at)
        inspected = inspect(order_id=106, at=expires_at)
        _reserve(107, product, 3, expires_at)
        committed = commit(order_id=107, at=expires_at)

    product.refresh_from_db()
    assert (inspected.status, inspected.release_reason) == ("RELEASED", "EXPIRED")
    assert (committed.status, committed.release_reason) == ("RELEASED", "EXPIRED")
    assert product.current_stock == 10
    assert StockMovement.objects.filter(product=product).count() == 0


def test_lifecycle_operations_require_an_outer_atomic_block(product_factory):
    product = product_factory()
    expires_at = timezone.now() + timedelta(minutes=15)

    with pytest.raises(RuntimeError, match="atomic"):
        _reserve(108, product, 1, expires_at)
    for operation in (
        lambda: inspect(order_id=108),
        lambda: release(order_id=108, reason="CANCELLED"),
        lambda: commit(order_id=108),
    ):
        with pytest.raises(RuntimeError, match="atomic"):
            operation()


@pytest.mark.pg_only
@pytest.mark.django_db(transaction=True)
def test_sorted_product_locks_allow_one_reservation_without_oversell(product_factory):
    first, second = product_factory(current_stock=2), product_factory(current_stock=2)
    expires_at = timezone.now() + timedelta(minutes=15)
    start = Barrier(2)

    def reserve_in_worker(order_id, lines):
        close_old_connections()
        try:
            start.wait(timeout=5)
            with transaction.atomic():
                return reserve(order_id=order_id, lines=lines, expires_at=expires_at).status
        except InsufficientAvailableStock:
            return "INSUFFICIENT"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_result = executor.submit(reserve_in_worker, 109, (_line(second, 2), _line(first, 2)))
        second_result = executor.submit(reserve_in_worker, 110, (_line(first, 2), _line(second, 2)))
        results = [first_result.result(timeout=5), second_result.result(timeout=5)]

    assert sorted(results) == ["ACTIVE", "INSUFFICIENT"]
    assert InventoryReservation.objects.filter(status="ACTIVE").count() == 1


@pytest.mark.pg_only
@pytest.mark.django_db(transaction=True)
def test_commit_and_release_produce_exactly_one_terminal_outcome(product_factory):
    product = product_factory(current_stock=10)
    expires_at = timezone.now() + timedelta(minutes=15)
    with transaction.atomic():
        _reserve(111, product, 6, expires_at)
    start = Barrier(2)

    def transition(operation):
        close_old_connections()
        try:
            start.wait(timeout=5)
            with transaction.atomic():
                return operation().status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        committed = executor.submit(transition, lambda: commit(order_id=111))
        released = executor.submit(transition, lambda: release(order_id=111, reason="CANCELLED"))
        results = [committed.result(timeout=5), released.result(timeout=5)]

    reservation = InventoryReservation.objects.get(order_id=111)
    assert results == [reservation.status, reservation.status]
    assert reservation.status in {"COMMITTED", "RELEASED"}
    assert StockMovement.objects.filter(product=product).count() == (reservation.status == "COMMITTED")
