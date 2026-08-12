from dataclasses import dataclass

from django.db import connection

from .models import Favorite, Product


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


def merge_favorites(*, user, product_ids):
    """Merge guest ids into private favorites, deduplicating and ignoring deleted products."""
    known = set(Product.objects.filter(id__in=set(product_ids)).values_list('id', flat=True))
    existing = set(Favorite.objects.filter(user=user, product_id__in=known).values_list('product_id', flat=True))
    Favorite.objects.bulk_create(
        [Favorite(user=user, product_id=product_id) for product_id in known - existing])
