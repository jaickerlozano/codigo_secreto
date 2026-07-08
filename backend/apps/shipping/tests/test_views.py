import pytest
from rest_framework import status

from apps.shipping.models import Comuna, Region


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
