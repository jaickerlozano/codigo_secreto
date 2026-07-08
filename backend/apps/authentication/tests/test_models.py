import pytest

from apps.authentication.models import User
from apps.carts.models import Cart

pytestmark = pytest.mark.django_db


def test_user_creation_with_email():
    """USERNAME_FIELD = email funciona y el username interno coincide con el email."""
    user = User.objects.create_user(
        email="test@example.com",
        username="test@example.com",
        password="TestPass123!",
    )

    assert user.email == "test@example.com"
    assert user.username == "test@example.com"
    assert User.USERNAME_FIELD == "email"


def test_signal_creates_customer_profile(user_factory):
    """post_save crea CustomerProfile cuando se crea un usuario."""
    user = user_factory()

    assert hasattr(user, "profile")
    assert user.profile is not None
    assert user.profile.user == user


def test_signal_creates_cart(user_factory):
    """post_save crea Cart cuando se crea un usuario."""
    user = user_factory()

    assert Cart.objects.filter(user=user).exists()
    assert user.cart is not None


def test_signal_idempotent(user_factory):
    """Guardar un usuario existente no crea CustomerProfile ni Cart duplicados."""
    user = user_factory()

    initial_profile_pk = user.profile.pk
    initial_cart_pk = user.cart.pk

    user.first_name = "Updated"
    user.save()

    assert user.profile.pk == initial_profile_pk
    assert user.cart.pk == initial_cart_pk


def test_user_str_with_full_name(user_factory):
    """__str__ muestra nombre completo y email cuando ambos existen."""
    user = user_factory(first_name="María", last_name="González", email="fullname@example.com")

    assert str(user) == "María González (fullname@example.com)"


def test_user_str_without_full_name(user_factory):
    """__str__ fallback al email cuando no hay nombre ni apellido."""
    user = User.objects.create_user(
        email="noname@example.com",
        username="noname@example.com",
        password="TestPass123!",
    )

    assert str(user) == "noname@example.com"


def test_customer_profile_str(user_factory):
    """CustomerProfile.__str__ identifica al usuario dueño."""
    user = user_factory(email="profile@example.com")

    assert str(user.profile) == "Customer Profile for profile@example.com"
