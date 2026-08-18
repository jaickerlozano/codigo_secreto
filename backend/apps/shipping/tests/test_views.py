import datetime as dt

import pytest
from django.utils import timezone
from rest_framework import status

from apps.shipping.models import Comuna, Region
from apps.shipping.services import resolve_shipping_price


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _results(response):
    """Return the list of results from a paginated DRF response."""
    data = response.json()
    return data.get("results", data)


def _all_pages(client, url):
    """Follow DRF pagination and return all results for a list endpoint."""
    results = []
    next_url = url
    while next_url:
        response = client.get(next_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results.extend(data.get("results", []))
        next_url = data.get("next")
    return results


# ---------------------------------------------------------------------------
# Region endpoints
# ---------------------------------------------------------------------------


def test_list_regions_public(api_client):
    """GET /api/shipping/regions/ is public and returns a paginated list."""
    response = api_client.get("/api/shipping/regions/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert data["results"]


def test_list_regions_ordered_by_ordinal_number(api_client, region_factory):
    """Regions are returned ordered by ordinal_number (north to south)."""
    region_factory(name="Región Zeta", ordinal_number=999)
    region_factory(name="Región Alfa", ordinal_number=0)

    regions = _all_pages(api_client, "/api/shipping/regions/")

    ordinals = [item["ordinal_number"] for item in regions]
    assert ordinals == sorted(ordinals)
    assert ordinals[0] <= ordinals[-1]


def test_region_detail_public(api_client, region_factory, comuna_factory):
    """GET /api/shipping/regions/{id}/ is public and includes only active comunas."""
    region = region_factory(name="Región Detail")
    active_comuna = comuna_factory(region=region, name="Comuna Activa", is_active=True)
    comuna_factory(region=region, name="Comuna Inactiva", is_active=False)

    response = api_client.get(f"/api/shipping/regions/{region.id}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == region.id
    assert data["name"] == region.name
    assert len(data["comunas"]) == 1
    assert data["comunas"][0]["id"] == active_comuna.id
    assert data["comunas"][0]["name"] == active_comuna.name


def test_region_create_not_allowed(api_client):
    """POST /api/shipping/regions/ is not allowed (read-only viewset)."""
    response = api_client.post(
        "/api/shipping/regions/",
        {"name": "Nueva Región", "ordinal_number": 99},
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_region_update_not_allowed(api_client, region_factory):
    """PUT /api/shipping/regions/{id}/ is not allowed (read-only viewset)."""
    region = region_factory(name="Región Update")
    response = api_client.put(
        f"/api/shipping/regions/{region.id}/",
        {"name": "Región Modificada", "ordinal_number": region.ordinal_number},
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_region_delete_not_allowed(api_client, region_factory):
    """DELETE /api/shipping/regions/{id}/ is not allowed (read-only viewset)."""
    region = region_factory(name="Región Delete")
    response = api_client.delete(f"/api/shipping/regions/{region.id}/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# Comuna endpoints
# ---------------------------------------------------------------------------


def test_list_comunas_public(api_client, comuna_factory):
    """GET /api/shipping/comunas/ is public and returns active comunas."""
    comuna = comuna_factory(name="Comuna Pública", is_active=True)

    comunas = _all_pages(api_client, "/api/shipping/comunas/")
    ids = {item["id"] for item in comunas}

    assert comuna.id in ids
    for item in comunas:
        assert item["is_active"] is True


def test_list_comunas_excludes_inactive(api_client, comuna_factory):
    """ComunaViewSet list excludes comunas with is_active=False."""
    inactive_comuna = comuna_factory(name="Comuna Inactiva", is_active=False)

    comunas = _all_pages(api_client, "/api/shipping/comunas/")
    ids = {item["id"] for item in comunas}

    assert inactive_comuna.id not in ids


def test_list_comunas_ordered_by_name(api_client, comuna_factory, region_factory):
    """Comunas are returned ordered alphabetically by name."""
    region = region_factory(name="Región Comunas")
    comuna_factory(name="Zzz Comuna", region=region)
    comuna_factory(name="Aaa Comuna", region=region)

    comunas = _all_pages(api_client, "/api/shipping/comunas/")
    names = [item["name"] for item in comunas]

    assert names == sorted(names)


def test_comuna_detail_returns_shipping_cost(api_client, comuna_factory):
    """GET /api/shipping/comunas/{id}/ returns the comuna shipping cost."""
    comuna = comuna_factory(name="Comuna Costo", shipping_cost=4500)

    response = api_client.get(f"/api/shipping/comunas/{comuna.id}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == comuna.id
    assert data["name"] == "Comuna Costo"
    assert data["shipping_cost"] == 4500
    assert data["is_active"] is True


def test_comuna_update_not_allowed(api_client, comuna_factory):
    """PUT /api/shipping/comunas/{id}/ is not allowed (read-only viewset)."""
    comuna = comuna_factory(name="Comuna Update")
    response = api_client.put(
        f"/api/shipping/comunas/{comuna.id}/",
        {"name": "Comuna Modificada", "region": comuna.region.id},
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_comuna_delete_not_allowed(api_client, comuna_factory):
    """DELETE /api/shipping/comunas/{id}/ is not allowed (read-only viewset)."""
    comuna = comuna_factory(name="Comuna Delete")
    response = api_client.delete(f"/api/shipping/comunas/{comuna.id}/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_comuna_create_not_allowed(api_client):
    """POST /api/shipping/comunas/ is not allowed (read-only viewset)."""
    response = api_client.post(
        "/api/shipping/comunas/",
        {"name": "Nueva Comuna", "shipping_cost": 3000},
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_list_comunas_filtered_by_region(api_client, comuna_factory, region_factory):
    """GET /api/shipping/comunas/?region={id} returns only comunas for that region."""
    region_a = region_factory(name="Región A")
    region_b = region_factory(name="Región B")
    comuna_a = comuna_factory(name="Comuna A", region=region_a)
    comuna_b = comuna_factory(name="Comuna B", region=region_b)

    response = api_client.get(f"/api/shipping/comunas/?region={region_a.id}")

    assert response.status_code == status.HTTP_200_OK
    results = _results(response)
    ids = {item["id"] for item in results}
    assert comuna_a.id in ids
    assert comuna_b.id not in ids


# ---------------------------------------------------------------------------
# Dispatch options endpoint
# ---------------------------------------------------------------------------


DISPATCH_OPTIONS_URL = "/api/shipping/dispatch-options/"


def _dispatch_options(client, comuna):
    """GET the dispatch options for a comuna, as the StepShipping client would."""
    return client.get(DISPATCH_OPTIONS_URL, {"comuna": comuna.id})


def test_dispatch_options_santiago_exactly_four_future_tue_thu_excluding_today(
    api_client, comuna_factory
):
    """Santiago dispatch exposes exactly the next four Tue/Thu dates, never today."""
    comuna = comuna_factory()

    response = _dispatch_options(api_client, comuna)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["comuna_id"] == comuna.id
    assert data["mode"] == "santiago"
    assert data["shipping_option"] is None
    today = timezone.localdate().isoformat()
    assert len(data["dates"]) == 4
    assert all(option_date > today for option_date in data["dates"])
    assert all(
        dt.date.fromisoformat(option_date).weekday() in (1, 3)
        for option_date in data["dates"]
    )


def test_dispatch_options_regional_exposes_one_applicable_option(
    api_client, comuna_factory, region_factory, regional_option_factory
):
    """A non-Santiago comuna exposes the single applicable regional option."""
    comuna = comuna_factory(
        name="Vina del Mar", region=region_factory(name="Valparaiso")
    )
    option = regional_option_factory(
        key="regional", carrier="CS Logistics", tariff=5500,
        min_lead_days=2, max_lead_days=5,
    )

    response = _dispatch_options(api_client, comuna)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["comuna_id"] == comuna.id
    assert data["mode"] == "regional"
    assert data["dates"] is None
    selected = data["shipping_option"]
    assert selected["shipping_option_id"] == option.id
    assert selected["key"] == "regional"
    assert selected["carrier"] == "CS Logistics"
    assert selected["tariff"] == 5500
    assert selected["min_lead_days"] == 2
    assert selected["max_lead_days"] == 5


def test_dispatch_options_regional_tariff_matches_price_authority(
    api_client, comuna_factory, region_factory, regional_option_factory
):
    """The advertised regional tariff equals the exclusive backend price authority."""
    comuna = comuna_factory(
        region=region_factory(name="Valparaiso"), shipping_cost=9000
    )
    regional_option_factory(key="regional", tariff=5500)

    response = _dispatch_options(api_client, comuna)

    authority = resolve_shipping_price(comuna_id=comuna.id)
    assert response.status_code == status.HTTP_200_OK
    assert authority.authority == "regional"
    assert response.json()["shipping_option"]["tariff"] == authority.price


def test_dispatch_options_requires_comuna_parameter(api_client):
    response = api_client.get(DISPATCH_OPTIONS_URL)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "comuna_required"


def test_dispatch_options_rejects_non_integer_comuna(api_client):
    response = api_client.get(DISPATCH_OPTIONS_URL, {"comuna": "not-a-number"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == "comuna_invalid"


def test_dispatch_options_unknown_comuna_fails_closed(api_client):
    response = api_client.get(DISPATCH_OPTIONS_URL, {"comuna": 999_999})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "delivery_unavailable"


def test_dispatch_options_inactive_comuna_fails_closed(api_client, comuna_factory):
    comuna = comuna_factory(name="Comuna Inactiva", is_active=False)

    response = _dispatch_options(api_client, comuna)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "delivery_unavailable"


def test_dispatch_options_regional_without_configuration_fails_closed(
    api_client, comuna_factory, region_factory
):
    comuna = comuna_factory(region=region_factory(name="Valparaiso"))

    response = _dispatch_options(api_client, comuna)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["code"] == "delivery_unavailable"


def test_dispatch_options_ambiguous_regional_configuration_fails_closed_without_leaks(
    api_client, comuna_factory, region_factory, regional_option_factory
):
    """Two active regional options fail closed; no configuration detail leaks."""
    comuna = comuna_factory(region=region_factory(name="Valparaiso"))
    regional_option_factory(key="regional", carrier="Carrier One", tariff=3000)
    regional_option_factory(key="regional-alt", carrier="Carrier Two", tariff=4000)

    response = _dispatch_options(api_client, comuna)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["code"] == "delivery_configuration_invalid"
    assert "Carrier One" not in str(body)
    assert "Carrier Two" not in str(body)


def test_dispatch_options_is_read_only(api_client, comuna_factory):
    comuna = comuna_factory()

    response = api_client.post(DISPATCH_OPTIONS_URL, {"comuna": comuna.id})

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
