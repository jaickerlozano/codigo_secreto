import factory
from faker import Faker

from apps.shipping.models import Comuna, Region, RegionalShippingOption

faker = Faker("es_CL")


class RegionFactory(factory.django.DjangoModelFactory):
    """Factory for Region.

    Uses a sequence for ``ordinal_number`` so regions are created in
    north-to-south order by default, matching the production data layout.
    """

    class Meta:
        model = Region
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Región {n}")
    ordinal_number = factory.Sequence(lambda n: n)


class ComunaFactory(factory.django.DjangoModelFactory):
    """Factory for Comuna.

    Defaults to an active Santiago comuna with a random shipping cost inside
    the shared Santiago region (comuna-priced delivery authority). Override
    ``region`` with a non-Santiago region to exercise the regional authority.
    ``django_get_or_create`` is intentionally omitted so tests can explicitly
    trigger ``IntegrityError`` on the ``unique_together`` constraint.
    """

    class Meta:
        model = Comuna

    name = factory.Sequence(lambda n: f"Comuna {n}")
    region = factory.SubFactory(
        RegionFactory, name="Metropolitana de Santiago", ordinal_number=7
    )
    shipping_cost = factory.LazyFunction(lambda: faker.random_int(min=1000, max=10000))
    is_active = True


class RegionalShippingOptionFactory(factory.django.DjangoModelFactory):
    """Factory for the single regional shipping configuration (key unique)."""

    class Meta:
        model = RegionalShippingOption

    key = "regional"
    carrier = factory.Sequence(lambda n: f"Carrier {n}")
    tariff = factory.LazyFunction(lambda: faker.random_int(min=1000, max=10000))
    min_lead_days = 2
    max_lead_days = 5
    is_active = True
