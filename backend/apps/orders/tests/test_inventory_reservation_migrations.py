"""Migration-contract coverage for inventory reservation rollout."""
from datetime import timedelta
from importlib import import_module
from itertools import count

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from apps.shipping.tests.factories import ComunaFactory


PRODUCTS_BASELINE = ("products", "0008_favorite")
PRODUCTS_TARGET = ("products", "0009_inventory_reservations")
ORDERS_BASELINE = ("orders", "0007_notificationdelivery_due_index")
ORDERS_TARGET = ("orders", "0008_backfill_inventory_reservations")
RESERVATION_TABLE = "products_inventoryreservation"
RESERVATION_LINE_TABLE = "products_inventoryreservationline"
_SEQUENCE = count()


def _migrate(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


def _restore_latest():
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


def _label(prefix):
    return f"{prefix}-{next(_SEQUENCE)}"


def _create_product(apps, stock):
    Category = apps.get_model("products", "Category")
    Product = apps.get_model("products", "Product")
    Supplier = apps.get_model("products", "Supplier")
    supplier = Supplier.objects.create(
        name=_label("supplier"),
        contact="Migration Test",
        email=f"{_label('supplier')}@example.test",
        phone="+56000000000",
        address="Migration Street 1",
    )
    category = Category.objects.create(name=_label("category"))
    return Product.objects.create(
        name=_label("product"),
        category_id=category.pk,
        supplier_id=supplier.pk,
        current_stock=stock,
        price=1000,
    )


def _create_pending_order(apps, created_at, lines):
    Order = apps.get_model("orders", "Order")
    OrderItem = apps.get_model("orders", "OrderItem")
    order = Order.objects.create(
        phone="+56000000001",
        comuna_id=ComunaFactory().pk,
        shipping_address="Migration Street 2",
        subtotal=1000,
        shipping_cost=0,
        total=1000,
        status="PENDING",
    )
    Order.objects.filter(pk=order.pk).update(created_at=created_at)
    for product, quantity in lines:
        OrderItem.objects.create(
            order_id=order.pk,
            product_id=product.pk if product else None,
            product_name=product.name if product else "Missing product",
            price=1000,
            quantity=quantity,
        )
    return order.pk


def _delete_orders(apps, order_ids):
    apps.get_model("orders", "Order").objects.filter(pk__in=order_ids).delete()


def _cleanup_legacy_rows(legacy_apps, target_apps, order_ids):
    if target_apps is not None:
        target_apps.get_model("products", "InventoryReservation").objects.filter(order_id__in=order_ids).delete()
    if legacy_apps is not None:
        _delete_orders(legacy_apps, order_ids)


@pytest.mark.django_db(transaction=True)
def test_reservation_schema_is_product_owned_indexed_and_reversible():
    try:
        migration = import_module("apps.orders.migrations.0008_backfill_inventory_reservations")
        assert PRODUCTS_TARGET in migration.Migration.dependencies

        apps = _migrate([ORDERS_TARGET])
        Reservation = apps.get_model("products", "InventoryReservation")
        ReservationLine = apps.get_model("products", "InventoryReservationLine")

        assert Reservation._meta.app_label == "products"
        assert ("status", "expires_at") in {
            tuple(index.fields) for index in Reservation._meta.indexes
        }
        assert {
            "products_reservation_terminal_metadata",
            "products_reservation_line_positive_quantity",
            "products_reservation_line_product_unique",
        } <= {
            constraint.name
            for model in (Reservation, ReservationLine)
            for constraint in model._meta.constraints
        }

        _migrate([PRODUCTS_BASELINE, ORDERS_BASELINE])
        tables = connection.introspection.table_names()
        assert RESERVATION_TABLE not in tables
        assert RESERVATION_LINE_TABLE not in tables
    finally:
        _restore_latest()


@pytest.mark.django_db(transaction=True)
def test_backfill_creates_active_and_expired_legacy_allocations_without_out_movements():
    order_ids = []
    legacy_apps = None
    target_apps = None
    try:
        legacy_apps = _migrate([PRODUCTS_BASELINE, ORDERS_BASELINE])
        lower_product = _create_product(legacy_apps, stock=10)
        higher_product = _create_product(legacy_apps, stock=10)
        now = timezone.now()
        active_order_id = _create_pending_order(
            legacy_apps,
            now - timedelta(minutes=5),
            [(higher_product, 1), (lower_product, 2)],
        )
        due_order_id = _create_pending_order(
            legacy_apps,
            now - timedelta(minutes=30),
            [(lower_product, 1)],
        )
        order_ids = [active_order_id, due_order_id]

        target_apps = _migrate([ORDERS_TARGET])
        Order = target_apps.get_model("orders", "Order")
        Product = target_apps.get_model("products", "Product")
        Reservation = target_apps.get_model("products", "InventoryReservation")
        ReservationLine = target_apps.get_model("products", "InventoryReservationLine")
        StockMovement = target_apps.get_model("products", "StockMovement")

        active = Reservation.objects.get(order_id=active_order_id)
        due = Reservation.objects.get(order_id=due_order_id)
        assert active.status == "ACTIVE"
        assert active.expires_at == now + timedelta(minutes=10)
        assert active.transitioned_at is None
        assert active.release_reason is None
        assert due.status == "RELEASED"
        assert due.release_reason == "EXPIRED"
        assert due.transitioned_at is not None
        assert Order.objects.get(pk=due_order_id).status == "CANCELLED"
        assert list(
            ReservationLine.objects.filter(reservation_id=active.pk)
            .order_by("pk")
            .values_list("product_id", flat=True)
        ) == [lower_product.pk, higher_product.pk]
        assert list(
            ReservationLine.objects.filter(reservation_id=active.pk)
            .order_by("product_id")
            .values_list("quantity", flat=True)
        ) == [2, 1]
        assert list(
            Product.objects.filter(pk__in=[lower_product.pk, higher_product.pk])
            .order_by("pk")
            .values_list("current_stock", flat=True)
        ) == [10, 10]
        assert list(
            ReservationLine.objects.filter(reservation_id=due.pk).values_list("product_id", "quantity")
        ) == [(lower_product.pk, 1)]
        assert StockMovement.objects.filter(
            product_id__in=[lower_product.pk, higher_product.pk]
        ).count() == 0
    finally:
        _cleanup_legacy_rows(legacy_apps, target_apps, order_ids)
        _restore_latest()


@pytest.mark.django_db(transaction=True)
def test_backfill_aborts_all_rows_when_a_pending_item_has_no_product():
    order_ids = []
    legacy_apps = None
    target_apps = None
    try:
        legacy_apps = _migrate([PRODUCTS_BASELINE, ORDERS_BASELINE])
        product = _create_product(legacy_apps, stock=10)
        now = timezone.now()
        order_ids = [
            _create_pending_order(legacy_apps, now - timedelta(minutes=5), [(product, 1)]),
            _create_pending_order(legacy_apps, now - timedelta(minutes=4), [(None, 1)]),
        ]

        with pytest.raises(RuntimeError, match="missing product"):
            _migrate([ORDERS_TARGET])

        target_apps = MigrationExecutor(connection).loader.project_state([PRODUCTS_TARGET]).apps
        Reservation = target_apps.get_model("products", "InventoryReservation")
        assert Reservation.objects.count() == 0
        assert list(
            legacy_apps.get_model("orders", "Order").objects.filter(pk__in=order_ids)
            .order_by("pk")
            .values_list("status", flat=True)
        ) == ["PENDING", "PENDING"]
    finally:
        _cleanup_legacy_rows(legacy_apps, target_apps, order_ids)
        _restore_latest()


@pytest.mark.django_db(transaction=True)
def test_backfill_aborts_all_rows_when_ordered_active_allocations_exceed_stock():
    order_ids = []
    legacy_apps = None
    target_apps = None
    try:
        legacy_apps = _migrate([PRODUCTS_BASELINE, ORDERS_BASELINE])
        product = _create_product(legacy_apps, stock=3)
        now = timezone.now()
        order_ids = [
            _create_pending_order(legacy_apps, now - timedelta(minutes=5), [(product, 2)]),
            _create_pending_order(legacy_apps, now - timedelta(minutes=4), [(product, 2)]),
        ]

        with pytest.raises(RuntimeError, match="exceeds physical stock"):
            _migrate([ORDERS_TARGET])

        target_apps = MigrationExecutor(connection).loader.project_state([PRODUCTS_TARGET]).apps
        Reservation = target_apps.get_model("products", "InventoryReservation")
        assert Reservation.objects.count() == 0
        assert legacy_apps.get_model("products", "Product").objects.get(pk=product.pk).current_stock == 3
        assert list(
            legacy_apps.get_model("orders", "Order").objects.filter(pk__in=order_ids)
            .order_by("pk")
            .values_list("status", flat=True)
        ) == ["PENDING", "PENDING"]
    finally:
        _cleanup_legacy_rows(legacy_apps, target_apps, order_ids)
        _restore_latest()
