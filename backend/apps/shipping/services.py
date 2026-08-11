from dataclasses import dataclass
from datetime import date, timedelta

from django.db import connection
from django.utils import timezone

from .models import Comuna, RegionalShippingOption


class ShippingSnapshotResolutionError(LookupError):
    """Raised when a shipping snapshot cannot be resolved safely."""


@dataclass(frozen=True, slots=True)
class ComunaShippingSnapshot:
    id: int
    name: str
    region_name: str
    shipping_cost: int


# Python weekday() values: Monday=0 ... Sunday=6.
DISPATCH_WEEKDAYS = (1, 3)  # Tuesday, Thursday: Santiago dispatch days
DISPATCH_KIND_STANDARD = "standard"
DISPATCH_KIND_SPECIAL = "special"


@dataclass(frozen=True, slots=True)
class RegionalShippingSnapshot:
    id: int
    key: str
    carrier: str
    tariff: int
    min_lead_days: int
    max_lead_days: int


@dataclass(frozen=True, slots=True)
class DeliveryScheduleDecision:
    """Domain decision for a requested dispatch date at the payment boundary."""

    requested_date: date | None
    dispatch_kind: str
    payment_blocked: bool
    recovery_guidance: str


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
        comuna = queryset.only("id", "name", "shipping_cost", "region__name").get()
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


def resolve_regional_shipping_option(
    *, for_update: bool = False
) -> RegionalShippingSnapshot | None:
    """Resolve the single active regional option; None when inactive, masks duplicates."""
    if for_update:
        _require_atomic_for_update()

    queryset = RegionalShippingOption.objects.filter(is_active=True)
    if for_update:
        queryset = queryset.select_for_update()

    options = list(queryset.only("id", "key", "carrier", "tariff", "min_lead_days", "max_lead_days"))
    if not options:
        return None
    if len(options) > 1:
        raise ShippingSnapshotResolutionError(
            "Unable to resolve the requested shipping option."
        )

    option = options[0]
    return RegionalShippingSnapshot(
        option.id, option.key, option.carrier, option.tariff,
        option.min_lead_days, option.max_lead_days,
    )


def future_dispatch_dates(*, from_date: date | None = None, limit: int = 4) -> tuple[date, ...]:
    """Next ``limit`` Santiago Tue/Thu dispatch dates, strictly after ``from_date``
    (same-day excluded; ``from_date`` defaults to Santiago today)."""
    if from_date is None:
        from_date = timezone.localdate()
    if limit <= 0:
        return ()

    dispatch_dates = []
    candidate = from_date + timedelta(days=1)
    while len(dispatch_dates) < limit:
        if candidate.weekday() in DISPATCH_WEEKDAYS:
            dispatch_dates.append(candidate)
        candidate += timedelta(days=1)
    return tuple(dispatch_dates)


def evaluate_requested_dispatch_date(
    *,
    requested_date: date | None = None,
    special_delivery_agreed_at=None,
    today: date | None = None,
) -> DeliveryScheduleDecision:
    """Classify a requested dispatch date; standard never blocks payment, special
    stays blocked until staff records ``special_delivery_agreed_at``."""
    if today is None:
        today = timezone.localdate()

    is_standard = (
        requested_date is not None
        and requested_date > today
        and requested_date.weekday() in DISPATCH_WEEKDAYS
    )
    if is_standard:
        return DeliveryScheduleDecision(
            requested_date=requested_date,
            dispatch_kind=DISPATCH_KIND_STANDARD,
            payment_blocked=False,
            recovery_guidance="Dispatch is available for the requested date.",
        )

    if requested_date is None:
        guidance = ("Select a future Tuesday or Thursday dispatch date, or agree a "
                    "special date via WhatsApp.")
    else:
        guidance = "Special dispatch dates require a pre-payment agreement via WhatsApp."
    return DeliveryScheduleDecision(
        requested_date=requested_date,
        dispatch_kind=DISPATCH_KIND_SPECIAL,
        payment_blocked=special_delivery_agreed_at is None,
        recovery_guidance=guidance,
    )
