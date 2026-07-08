import pytest

from apps.shipping.tests.factories import ComunaFactory, RegionFactory


@pytest.fixture
def region_factory():
    """Return the RegionFactory class."""
    return RegionFactory


@pytest.fixture
def comuna_factory():
    """Return the ComunaFactory class."""
    return ComunaFactory
