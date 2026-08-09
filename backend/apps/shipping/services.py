from dataclasses import dataclass

from django.db import connection

from .models import Comuna


class ShippingSnapshotResolutionError(LookupError):
    """Raised when a shipping snapshot cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class ComunaShippingSnapshot:
    id: int
    name: str
    region_name: str
    shipping_cost: int


def _require_atomic_for_update() -> None:
    if not any(
        not getattr(block, "_from_testcase", False)
        for block in connection.atomic_blocks
    ):
        raise RuntimeError("Locked shipping snapshots require an active transaction.atomic block.")


def resolve_comuna_shipping_snapshot(
    *,
    comuna_id=None,
    comuna_name=None,
    region_name=None,
    for_update: bool = False,
) -> ComunaShippingSnapshot | None:
    """Resolve an optional comuna by id or by its name and region."""
    if for_update:
        _require_atomic_for_update()

    if comuna_id is None and comuna_name is None and region_name is None:
        return None

    if comuna_id is not None:
        filters = {"id": comuna_id}
    elif comuna_name is not None and region_name is not None:
        filters = {"name": comuna_name, "region__name": region_name}
    else:
        raise ShippingSnapshotResolutionError(
            "Unable to resolve the requested shipping snapshot."
        )

    queryset = Comuna.objects.select_related("region").filter(**filters)
    if for_update:
        queryset = queryset.select_for_update()

    try:
        comuna = queryset.only(
            "id", "name", "shipping_cost", "region__name"
        ).get()
    except (Comuna.DoesNotExist, Comuna.MultipleObjectsReturned) as error:
        raise ShippingSnapshotResolutionError(
            "Unable to resolve the requested shipping snapshot."
        ) from error

    return ComunaShippingSnapshot(
        id=comuna.id,
        name=comuna.name,
        region_name=comuna.region.name,
        shipping_cost=comuna.shipping_cost,
    )
