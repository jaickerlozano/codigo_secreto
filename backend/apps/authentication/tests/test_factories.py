import pytest
from rest_framework.test import APIClient

from apps.authentication.models import CustomerProfile, User
from apps.authentication.tests.factories import (
    CustomerProfileFactory,
    UserFactory,
    generate_rut,
    validate_rut,
)
from apps.carts.models import Cart

pytestmark = pytest.mark.django_db


def test_user_factory_creates_valid_user():
    """UserFactory must produce a real, authenticated-ready user."""
    user = UserFactory.create()

    assert user.pk is not None
    assert user.email.endswith("@example.com")
    assert user.is_active is True
    assert user.check_password("TestPass123!") is True
    assert user.rut is not None
    assert validate_rut(user.rut) is True


def test_user_factory_emails_are_unique():
    """Sequential factory calls must never collide on the unique email."""
    user_a = UserFactory.create()
    user_b = UserFactory.create()

    assert user_a.email != user_b.email


def test_customer_profile_factory_creates_valid_profile():
    """CustomerProfileFactory must yield a profile linked to a user with a valid RUT."""
    profile = CustomerProfileFactory.create()

    assert profile.pk is not None
    assert isinstance(profile.user, User)
    assert validate_rut(profile.user.rut) is True
    assert CustomerProfile.objects.filter(user=profile.user).exists()
    assert Cart.objects.filter(user=profile.user).exists()


def test_generated_rut_is_valid():
    """The RUT generator must always produce a Chilean RUT with a correct verifier."""
    rut = generate_rut(1234)

    assert validate_rut(rut) is True


def test_global_api_client_fixture(api_client):
    """The shared api_client fixture must be an unauthenticated DRF client."""
    assert isinstance(api_client, APIClient)


def test_global_authenticated_client_fixture(authenticated_client, user):
    """The authenticated_client fixture must be tied to the generated user."""
    assert isinstance(authenticated_client, APIClient)
    assert authenticated_client.handler._force_user == user


def test_global_staff_client_fixture(staff_client, staff_user):
    """The staff_client fixture must be tied to a staff user."""
    assert isinstance(staff_client, APIClient)
    assert staff_client.handler._force_user == staff_user
    assert staff_user.is_staff is True
