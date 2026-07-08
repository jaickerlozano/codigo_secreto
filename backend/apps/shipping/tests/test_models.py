import pytest
from django.db import IntegrityError

from apps.shipping.models import Comuna, Region


pytestmark = pytest.mark.django_db


def test_region_str(region_factory):
    """Region.__str__ returns the region name."""
    region = region_factory(name="Región Test Str")
    assert str(region) == "Región Test Str"


def test_region_ordering(region_factory):
    """Regions are ordered by ordinal_number from north to south."""
    region_second = region_factory(name="Región Zeta", ordinal_number=99)
    region_first = region_factory(name="Región Alfa", ordinal_number=1)

    regions = list(Region.objects.filter(name__startswith="Región").order_by("ordinal_number"))

    assert regions[0] == region_first
    assert regions[1] == region_second


def test_comuna_str(comuna_factory, region_factory):
    """Comuna.__str__ includes the comuna name and its region."""
    region = region_factory(name="Región Metropolitana")
    comuna = comuna_factory(name="Santiago Centro", region=region)
    assert str(comuna) == "Santiago Centro (Región Metropolitana)"


def test_comuna_unique_per_region(comuna_factory, region_factory):
    """The same comuna name cannot be duplicated within the same region."""
    region = region_factory(name="Región Única")
    comuna_factory(name="Comuna Única", region=region)

    with pytest.raises(IntegrityError):
        Comuna.objects.create(name="Comuna Única", region=region, shipping_cost=1000)


def test_comuna_ordering_by_name(comuna_factory, region_factory):
    """Comunas are ordered alphabetically by name within a region."""
    region = region_factory(name="Región Orden")
    comuna_z = comuna_factory(name="Zapallar Test", region=region)
    comuna_a = comuna_factory(name="Alhué Test", region=region)

    comunas = list(Comuna.objects.filter(region=region))

    assert comunas[0] == comuna_a
    assert comunas[1] == comuna_z
