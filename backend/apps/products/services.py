from dataclasses import dataclass

from django.db import connection

from .models import Product


class ProductSnapshotResolutionError(LookupError):
    """Raised when a product snapshot cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class ProductPriceSnapshot:
    id: int
    name: str
    unit_price: int


def _require_atomic_for_update() -> None:
    if not any(
        not getattr(block, "_from_testcase", False)
        for block in connection.atomic_blocks
    ):
        raise RuntimeError("Locked product snapshots require an active transaction.atomic block.")


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
