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
    min_lead_days: int
    max_lead_days: int


SANTIAGO_REGION_NAME = "Metropolitana de Santiago"
SHIPPING_AUTHORITY_COMUNA = "comuna"


@dataclass(frozen=True, slots=True)
class ShippingPriceSnapshot:
    """Exclusive backend shipping price authority for a selected destination."""

    price: int
    comuna_id: int
    authority: str


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

    queryset = Comuna.objects.select_related("region").filter(
        **filters, is_active=True, shipping_cost__gt=0
    )
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
    """Resolve one active regional dispatch profile, masking ambiguity.

    This is dispatch metadata only; it never participates in pricing.
    """
    if for_update:
        _require_atomic_for_update()

    queryset = RegionalShippingOption.objects.filter(is_active=True)
    if for_update:
        queryset = queryset.select_for_update()

    options = list(queryset.only("id", "key", "carrier", "min_lead_days", "max_lead_days"))
    if not options:
        return None
    if len(options) > 1:
        raise ShippingSnapshotResolutionError(
            "Unable to resolve the requested shipping option."
        )

    option = options[0]
    return RegionalShippingSnapshot(
        option.id, option.key, option.carrier, option.min_lead_days, option.max_lead_days,
    )


def resolve_shipping_price(
    *,
    comuna_id=None,
    comuna_name=None,
    region_name=None,
    for_update: bool = False,
) -> ShippingPriceSnapshot | None:
    """Resolve the authoritative price for an eligible destination comuna."""
    comuna = resolve_comuna_shipping_snapshot(
        comuna_id=comuna_id,
        comuna_name=comuna_name,
        region_name=region_name,
        for_update=for_update,
    )
    if comuna is None:
        return None

    return ShippingPriceSnapshot(comuna.shipping_cost, comuna.id, SHIPPING_AUTHORITY_COMUNA)


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


DEFAULT_CARRIER = "Chilexpress"


class DeliveryValidationError(ValueError):
    """The submitted delivery selection is invalid."""


class StaleDeliveryOptionError(DeliveryValidationError):
    """The submitted regional option no longer matches the active authority."""


@dataclass(frozen=True, slots=True)
class DeliverySnapshot:
    """Fields to snapshot onto an Order for a validated delivery selection."""

    delivery_kind: str
    requested_dispatch_date: date | None
    carrier: str
    shipping_price: int


def resolve_delivery_snapshot(
    *,
    comuna_id,
    delivery_kind=DISPATCH_KIND_STANDARD,
    requested_dispatch_date=None,
    shipping_option_id=None,
    for_update=False,
) -> DeliverySnapshot:
    """Validate the submitted delivery selection against the exclusive shipping
    authority and return the fields to snapshot onto the Order, including the
    shipping price re-derived under the same locked resolution.

    Santiago requires a valid requested dispatch date. For other regions,
    price always comes from the eligible comuna; a regional profile is optional
    metadata and, when supplied, must still be the sole active profile.
    """
    authority = resolve_shipping_price(comuna_id=comuna_id, for_update=for_update)
    if authority is None:
        raise DeliveryValidationError(
            "El envío no está disponible para la comuna indicada."
        )
    comuna = resolve_comuna_shipping_snapshot(comuna_id=comuna_id, for_update=for_update)
    if comuna.region_name == SANTIAGO_REGION_NAME:
        if shipping_option_id is not None:
            raise DeliveryValidationError(
                "La opción de envío regional no aplica para Santiago."
            )
        if requested_dispatch_date is None:
            if delivery_kind == DISPATCH_KIND_SPECIAL:
                raise DeliveryValidationError(
                    "La entrega especial requiere una fecha de despacho solicitada."
                )
            raise DeliveryValidationError(
                "La entrega estándar requiere una fecha de despacho solicitada."
            )
        if delivery_kind == DISPATCH_KIND_STANDARD:
            decision = evaluate_requested_dispatch_date(
                requested_date=requested_dispatch_date
            )
            if decision.dispatch_kind != DISPATCH_KIND_STANDARD:
                raise DeliveryValidationError(
                    "La fecha de despacho estándar debe ser un martes o jueves futuro."
                )
            return DeliverySnapshot(
                DISPATCH_KIND_STANDARD, requested_dispatch_date, DEFAULT_CARRIER,
                authority.price,
            )
        if not requested_dispatch_date > timezone.localdate():
            raise DeliveryValidationError(
                "La fecha de despacho especial debe ser una fecha futura."
            )
        return DeliverySnapshot(
            DISPATCH_KIND_SPECIAL, requested_dispatch_date, DEFAULT_CARRIER,
            authority.price,
        )

    if delivery_kind == DISPATCH_KIND_SPECIAL:
        raise DeliveryValidationError(
            "La entrega especial no aplica para entregas regionales."
        )
    if requested_dispatch_date is not None:
        raise DeliveryValidationError(
            "La fecha de despacho no aplica para entregas regionales."
        )
    try:
        option = resolve_regional_shipping_option(for_update=for_update)
    except ShippingSnapshotResolutionError:
        option = None
    if shipping_option_id is not None and (option is None or shipping_option_id != option.id):
        raise StaleDeliveryOptionError(
            "La opción de envío seleccionada ya no está disponible."
        )
    return DeliverySnapshot(
        DISPATCH_KIND_STANDARD, None,
        option.carrier if option is not None else DEFAULT_CARRIER,
        authority.price,
    )
