from dataclasses import FrozenInstanceError
import datetime as dt

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.shipping.services import (
    ComunaShippingSnapshot,
    RegionalShippingSnapshot,
    evaluate_requested_dispatch_date,
    future_dispatch_dates,
    resolve_comuna_shipping_snapshot,
    resolve_regional_shipping_option,
)


pytestmark = pytest.mark.django_db


def test_comuna_shipping_snapshot_is_frozen():
    snapshot = ComunaShippingSnapshot(
        id=7,
        name="Providencia",
        region_name="Metropolitana",
        shipping_cost=3500,
    )

    assert snapshot.shipping_cost == 3500
    with pytest.raises(FrozenInstanceError):
        snapshot.shipping_cost = 1


def test_resolve_comuna_by_id_uses_one_related_query(
    comuna_factory, region_factory, django_assert_num_queries
):
    region = region_factory(name="Metropolitana")
    comuna = comuna_factory(name="Providencia", region=region, shipping_cost=3500)

    with django_assert_num_queries(1):
        snapshot = resolve_comuna_shipping_snapshot(comuna_id=comuna.id)

    assert snapshot == ComunaShippingSnapshot(
        comuna.id, "Providencia", "Metropolitana", 3500
    )


def test_resolve_comuna_by_name_and_region_and_absent_selector(
    comuna_factory, region_factory, django_assert_num_queries
):
    region = region_factory(name="Valparaiso")
    comuna = comuna_factory(name="Vina del Mar", region=region, shipping_cost=4200)

    with django_assert_num_queries(1):
        snapshot = resolve_comuna_shipping_snapshot(
            comuna_name="Vina del Mar", region_name="Valparaiso"
        )

    assert snapshot.id == comuna.id
    with django_assert_num_queries(0):
        assert resolve_comuna_shipping_snapshot() is None


def test_resolve_comuna_masks_unknown_selector(comuna_factory):
    comuna_factory(name="Known comuna")

    with pytest.raises(LookupError) as error:
        resolve_comuna_shipping_snapshot(
            comuna_name="Secret missing comuna", region_name="Secret region"
        )

    assert "Secret missing comuna" not in str(error.value)
    assert "Secret region" not in str(error.value)


def test_locked_shipping_snapshot_requires_atomic_caller(
    comuna_factory, django_assert_num_queries
):
    comuna = comuna_factory()

    with django_assert_num_queries(0), pytest.raises(RuntimeError, match="atomic"):
        resolve_comuna_shipping_snapshot(comuna_id=comuna.id, for_update=True)


def test_locked_shipping_snapshot_runs_inside_atomic_caller(
    comuna_factory, django_assert_num_queries
):
    comuna = comuna_factory()

    with CaptureQueriesContext(connection) as queries:
        with transaction.atomic():
            snapshot = resolve_comuna_shipping_snapshot(
                comuna_id=comuna.id, for_update=True
            )

    assert snapshot.id == comuna.id
    assert len([query for query in queries if query["sql"].lstrip().upper().startswith("SELECT")]) == 1



def test_resolve_regional_option_returns_active_configuration(regional_option_factory):
    option = regional_option_factory(
        key="regional", carrier="CS Logistics", tariff=5500,
        min_lead_days=2, max_lead_days=5,
    )

    snapshot = resolve_regional_shipping_option()

    assert snapshot == RegionalShippingSnapshot(
        option.id, "regional", "CS Logistics", 5500, 2, 5
    )


def test_resolve_regional_option_returns_none_when_only_inactive(regional_option_factory):
    regional_option_factory(key="regional", carrier="Inactive Carrier", is_active=False)

    assert resolve_regional_shipping_option() is None


def test_resolve_regional_option_masks_multiple_active_configurations(regional_option_factory):
    regional_option_factory(key="regional", carrier="Carrier One", tariff=3000)
    regional_option_factory(key="regional-alt", carrier="Carrier Two", tariff=4000)

    with pytest.raises(LookupError) as error:
        resolve_regional_shipping_option()

    assert "Carrier One" not in str(error.value)
    assert "Carrier Two" not in str(error.value)


def test_locked_regional_option_requires_atomic_caller(regional_option_factory, django_assert_num_queries):
    regional_option_factory()

    with django_assert_num_queries(0), pytest.raises(RuntimeError, match="atomic"):
        resolve_regional_shipping_option(for_update=True)



def test_future_dispatch_dates_follow_weekday_boundaries():
    cases = [
        (dt.date(2026, 8, 10), dt.date(2026, 8, 11)),  # Monday -> Tuesday
        (dt.date(2026, 8, 11), dt.date(2026, 8, 13)),  # Tuesday -> Thursday
        (dt.date(2026, 8, 12), dt.date(2026, 8, 13)),  # Wednesday -> Thursday
        (dt.date(2026, 8, 13), dt.date(2026, 8, 18)),  # Thursday -> next Tue
        (dt.date(2026, 8, 14), dt.date(2026, 8, 18)),  # Friday -> next Tue
        (dt.date(2026, 8, 15), dt.date(2026, 8, 18)),  # Saturday -> next Tue
        (dt.date(2026, 8, 16), dt.date(2026, 8, 18)),  # Sunday -> next Tue
    ]
    for from_date, first_expected in cases:
        assert future_dispatch_dates(from_date=from_date, limit=2)[0] == first_expected


def test_future_dispatch_dates_never_include_from_date_and_respect_limit():
    from_date = dt.date(2026, 8, 11)  # Tuesday

    dates = future_dispatch_dates(from_date=from_date, limit=5)

    assert len(dates) == 5
    assert all(option_date > from_date for option_date in dates)
    assert all(option_date.weekday() in (1, 3) for option_date in dates)


def test_future_dispatch_dates_default_to_santiago_today():
    dates = future_dispatch_dates(limit=3)

    assert all(option_date > timezone.localdate() for option_date in dates)



def test_standard_future_tuesday_never_blocks_payment():
    decision = evaluate_requested_dispatch_date(
        requested_date=dt.date(2026, 8, 18), today=dt.date(2026, 8, 12)
    )

    assert decision.dispatch_kind == "standard"
    assert decision.payment_blocked is False


@pytest.mark.parametrize(
    ("requested_date", "agreed_at"),
    [
        (dt.date(2026, 8, 11), None),  # same-day Tuesday
        (dt.date(2026, 8, 12), None),  # non-dispatch weekday
        (dt.date(2026, 8, 12), timezone.now()),  # special + staff agreement
    ],
)
def test_special_dates_require_agreement_unless_recorded(requested_date, agreed_at):
    decision = evaluate_requested_dispatch_date(
        requested_date=requested_date, special_delivery_agreed_at=agreed_at,
        today=dt.date(2026, 8, 11),
    )

    assert decision.dispatch_kind == "special"
    assert decision.payment_blocked is (agreed_at is None)
    assert "whatsapp" in decision.recovery_guidance.lower()


def test_past_dispatch_date_is_special_and_blocked():
    decision = evaluate_requested_dispatch_date(
        requested_date=dt.date(2026, 8, 11), today=dt.date(2026, 8, 18)
    )

    assert decision.dispatch_kind == "special"
    assert decision.payment_blocked is True


def test_missing_requested_date_blocks_payment_with_guidance():
    decision = evaluate_requested_dispatch_date(today=dt.date(2026, 8, 11))

    assert decision.dispatch_kind == "special"
    assert decision.payment_blocked is True
    assert len(decision.recovery_guidance) > 0
