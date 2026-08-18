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


# Santiago comunas price exactly from Comuna.shipping_cost; every other region
# prices exactly from the sole active RegionalShippingOption.tariff.
SANTIAGO_REGION_NAME = "Metropolitana de Santiago"
SHIPPING_AUTHORITY_COMUNA = "comuna"
SHIPPING_AUTHORITY_REGIONAL = "regional"


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


def resolve_shipping_price(
    *,
    comuna_id=None,
    comuna_name=None,
    region_name=None,
    for_update: bool = False,
) -> ShippingPriceSnapshot | None:
    """Resolve the exclusive shipping price authority for a destination.

    Santiago prices exactly from ``Comuna.shipping_cost``; any other region
    prices exactly from the sole active regional tariff. Missing applicable
    configuration returns None (delivery unavailable), ambiguity raises
    ``ShippingSnapshotResolutionError``, and the two authorities never combine.
    """
    comuna = resolve_comuna_shipping_snapshot(
        comuna_id=comuna_id,
        comuna_name=comuna_name,
        region_name=region_name,
        for_update=for_update,
    )
    if comuna is None:
        return None

    if comuna.region_name == SANTIAGO_REGION_NAME:
        return ShippingPriceSnapshot(comuna.shipping_cost, comuna.id, SHIPPING_AUTHORITY_COMUNA)

    regional = resolve_regional_shipping_option(for_update=for_update)
    if regional is None:
        return None
    return ShippingPriceSnapshot(regional.tariff, comuna.id, SHIPPING_AUTHORITY_REGIONAL)


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

    Santiago (``comuna`` authority): a standard date must be a future Tuesday
    or Thursday; a special date must be strictly future; a regional option id
    is never applicable. Regional (``regional`` authority): the submitted
    option id must match the sole active option (stale otherwise) and its
    carrier is snapshotted; requested dates never apply. An absent required
    selection (Santiago date or regional option id) is rejected.
    """
    authority = resolve_shipping_price(comuna_id=comuna_id, for_update=for_update)
    if authority is None:
        raise DeliveryValidationError(
            "El envío no está disponible para la comuna indicada."
        )
    if authority.authority == SHIPPING_AUTHORITY_COMUNA:
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
    if shipping_option_id is None:
        raise DeliveryValidationError(
            "Selecciona la opción de envío regional."
        )
    option = resolve_regional_shipping_option(for_update=for_update)
    if option is None or shipping_option_id != option.id:
        raise StaleDeliveryOptionError(
            "La opción de envío seleccionada ya no está disponible."
        )
    return DeliverySnapshot(
        DISPATCH_KIND_STANDARD, None, option.carrier, authority.price
    )
