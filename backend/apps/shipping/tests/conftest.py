import pytest

from apps.shipping.tests.factories import (
    ComunaFactory,
    RegionFactory,
    RegionalShippingOptionFactory,
)


@pytest.fixture
def region_factory():
    return RegionFactory


@pytest.fixture
def comuna_factory():
    return ComunaFactory


@pytest.fixture
def regional_option_factory():
    return RegionalShippingOptionFactory
