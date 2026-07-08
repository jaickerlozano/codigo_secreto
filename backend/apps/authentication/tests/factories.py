import random

import factory
from faker import Faker

from apps.authentication.models import CustomerProfile, User

# Faker instance reused for deterministic-but-realistic fake data.
faker = Faker()


def calculate_rut_verifier_digit(rut_body: int) -> str:
    """Return the Chilean RUT verifier digit (DV) for a numeric body."""
    digits = str(rut_body)
    factors = [2, 3, 4, 5, 6, 7]
    total = sum(
        int(digit) * factors[index % 6]
        for index, digit in enumerate(reversed(digits))
    )
    remainder = 11 - (total % 11)

    if remainder == 11:
        return "0"
    if remainder == 10:
        return "K"
    return str(remainder)


def generate_rut(sequence: int | None = None) -> str:
    """Generate a valid Chilean RUT as a sanitized digit string.

    The numeric body starts at 5_000_000 plus the optional sequence number to
    keep RUTs unique across tests. The verifier digit is always calculated using
    the official modulus-11 algorithm.
    """
    if sequence is None:
        base = random.randint(5_000_000, 25_000_000)
    else:
        base = 5_000_000 + sequence

    return f"{base}{calculate_rut_verifier_digit(base)}"


def validate_rut(rut: str) -> bool:
    """Validate a sanitized Chilean RUT string (digits + optional trailing K)."""
    if not rut or len(rut) < 2:
        return False

    body, verifier = rut[:-1], rut[-1].upper()
    if not body.isdigit():
        return False

    return calculate_rut_verifier_digit(int(body)) == verifier


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for the custom User model.

    The User post_save signal uses CustomerProfile.objects.get_or_create and
    Cart.objects.get_or_create, so calling this factory repeatedly is safe and
    idempotent. CustomerProfile and Cart are created automatically by the
    signal; no special factory logic is required.
    """

    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.SelfAttribute("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    rut = factory.Sequence(lambda n: generate_rut(n))
    phone = factory.Faker("phone_number")
    is_active = True
    is_staff = False

    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")


class CustomerProfileFactory(factory.django.DjangoModelFactory):
    """Factory for CustomerProfile.

    Relies on UserFactory, which already assigns a valid Chilean RUT and
    triggers the post_save signal. The signal's get_or_create guard guarantees
    no duplicate CustomerProfile or Cart rows are created.
    """

    class Meta:
        model = CustomerProfile
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    birth_date = factory.Faker("date_of_birth", minimum_age=18, maximum_age=90)
    region = factory.Faker("state")
    province = factory.Faker("city")
    address = factory.Faker("street_address")
