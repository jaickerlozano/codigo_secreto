from dataclasses import dataclass
from datetime import datetime

from django.db import connection
from django.db.models import Sum
from django.utils import timezone

from .models import Favorite, InventoryReservation, InventoryReservationLine, Product, StockMovement


class ProductSnapshotResolutionError(LookupError):
    """Raised when a product snapshot cannot be resolved safely."""


class InventoryReservationError(RuntimeError):
    """Raised when an inventory reservation cannot transition safely."""


class InsufficientAvailableStock(InventoryReservationError):
    """Raised when active holds leave insufficient physical stock."""


@dataclass(frozen=True, slots=True)
class ProductPriceSnapshot:
    id: int
    name: str
    unit_price: int


@dataclass(frozen=True, slots=True)
class ReservationLineInput:
    product_id: int
    quantity: int


@dataclass(frozen=True, slots=True)
class ReservationSnapshot:
    order_id: int
    status: str
    expires_at: datetime
    transitioned_at: datetime | None
    release_reason: str | None
    lines: tuple[ReservationLineInput, ...]


def _require_atomic_for_update() -> None:
    if not any(
        not getattr(block, "_from_testcase", False)
        for block in connection.atomic_blocks
    ):
        raise RuntimeError("Locked product snapshots require an active transaction.atomic block.")


def _snapshot(reservation: InventoryReservation) -> ReservationSnapshot:
    return ReservationSnapshot(
        order_id=reservation.order_id,
        status=reservation.status,
        expires_at=reservation.expires_at,
        transitioned_at=reservation.transitioned_at,
        release_reason=reservation.release_reason,
        lines=tuple(ReservationLineInput(line.product_id, line.quantity) for line in reservation.lines.order_by("product_id")),
    )


def _locked_reservation(order_id: int) -> InventoryReservation:
    try:
        return InventoryReservation.objects.select_for_update().get(order_id=order_id)
    except InventoryReservation.DoesNotExist as error:
        raise InventoryReservationError("Inventory reservation does not exist.") from error


def _requested(lines) -> tuple[ReservationLineInput, ...]:
    quantities = {}
    for line in lines:
        product_id, quantity = int(line.product_id), int(line.quantity)
        if product_id <= 0 or quantity <= 0:
            raise InventoryReservationError("Reservation quantities must be positive.")
        quantities[product_id] = quantities.get(product_id, 0) + quantity
    if not quantities:
        raise InventoryReservationError("A reservation requires at least one product.")
    return tuple(ReservationLineInput(product_id, quantities[product_id]) for product_id in sorted(quantities))


def _lock_products(product_ids):
    products = {product.id: product for product in Product.objects.select_for_update().filter(id__in=product_ids).order_by("id")}
    if len(products) != len(product_ids):
        raise InventoryReservationError("Inventory product does not exist.")
    return products


def _active_holds(product_ids, at):
    return dict(
        InventoryReservationLine.objects.filter(
            product_id__in=product_ids, reservation__status="ACTIVE", reservation__expires_at__gt=at
        ).values("product_id").annotate(total=Sum("quantity")).values_list("product_id", "total")
    )


def _expire_if_due(reservation: InventoryReservation, at) -> None:
    if reservation.status == "ACTIVE" and reservation.expires_at <= at:
        reservation.status, reservation.transitioned_at, reservation.release_reason = "RELEASED", at, "EXPIRED"
        reservation.save(update_fields=["status", "transitioned_at", "release_reason"])


def reserve(*, order_id: int, lines, expires_at) -> ReservationSnapshot:
    _require_atomic_for_update()
    order_id = int(order_id)
    existing = InventoryReservation.objects.select_for_update().filter(order_id=order_id).first()
    if existing:
        return _snapshot(existing)
    requested = _requested(lines)
    product_ids = tuple(line.product_id for line in requested)
    products, held = _lock_products(product_ids), _active_holds(product_ids, timezone.now())
    if any(line.quantity > products[line.product_id].current_stock - held.get(line.product_id, 0) for line in requested):
        raise InsufficientAvailableStock("Insufficient available stock for this reservation.")
    reservation = InventoryReservation.objects.create(order_id=order_id, status="ACTIVE", expires_at=expires_at)
    InventoryReservationLine.objects.bulk_create(
        [InventoryReservationLine(reservation=reservation, product_id=line.product_id, quantity=line.quantity) for line in requested]
    )
    return _snapshot(reservation)


def inspect(*, order_id: int, at=None) -> ReservationSnapshot:
    _require_atomic_for_update()
    reservation = _locked_reservation(order_id)
    _expire_if_due(reservation, at or timezone.now())
    return _snapshot(reservation)


def release(*, order_id: int, reason: str, at=None) -> ReservationSnapshot:
    _require_atomic_for_update()
    if reason not in {"EXPIRED", "CANCELLED"}:
        raise InventoryReservationError("Invalid reservation release reason.")
    reservation = _locked_reservation(order_id)
    if reservation.status == "ACTIVE":
        reservation.status, reservation.transitioned_at, reservation.release_reason = "RELEASED", at or timezone.now(), reason
        reservation.save(update_fields=["status", "transitioned_at", "release_reason"])
    return _snapshot(reservation)


def commit(*, order_id: int, at=None) -> ReservationSnapshot:
    _require_atomic_for_update()
    reservation, at = _locked_reservation(order_id), at or timezone.now()
    _expire_if_due(reservation, at)
    if reservation.status != "ACTIVE":
        return _snapshot(reservation)
    lines = list(reservation.lines.order_by("product_id"))
    products = _lock_products(tuple(line.product_id for line in lines))
    reservation.status, reservation.transitioned_at = "COMMITTED", at
    reservation.save(update_fields=["status", "transitioned_at"])
    for line in lines:
        movement = StockMovement.objects.create(
            product=products[line.product_id], movement_type="OUT", quantity=line.quantity, description=f"Inventory reservation {order_id}"
        )
        line.stock_movement = movement
        line.save(update_fields=["stock_movement"])
    return _snapshot(reservation)


def resolve_product_price_snapshot(
    product_ids, *, for_update: bool = False
) -> dict[int, ProductPriceSnapshot]:
    """Resolve product prices in one bounded, optionally locked query."""
    if for_update:
        _require_atomic_for_update()

    ids = tuple(sorted({int(product_id) for product_id in product_ids}))
    if not ids:
        return {}

    queryset = Product.objects.filter(id__in=ids).order_by("id")
    if for_update:
        queryset = queryset.select_for_update()

    products = queryset.only("id", "name", "price")
    snapshots = {
        product.id: ProductPriceSnapshot(
            id=product.id,
            name=product.name,
            unit_price=product.price,
        )
        for product in products
    }

    if len(snapshots) != len(ids):
        raise ProductSnapshotResolutionError(
            "Unable to resolve the requested product price snapshots."
        )

    return snapshots


def merge_favorites(*, user, product_ids):
    """Merge guest ids into private favorites, deduplicating and ignoring deleted products."""
    known = set(Product.objects.filter(id__in=set(product_ids)).values_list('id', flat=True))
    existing = set(Favorite.objects.filter(user=user, product_id__in=known).values_list('product_id', flat=True))
    Favorite.objects.bulk_create(
        [Favorite(user=user, product_id=product_id) for product_id in known - existing])
