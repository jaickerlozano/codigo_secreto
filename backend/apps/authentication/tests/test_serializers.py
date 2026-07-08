import pytest
from django.contrib.auth.password_validation import ValidationError

from apps.authentication.models import User
from apps.authentication.serializers import RegisterSerializer, UserMeSerializer
from apps.authentication.tests.factories import UserFactory
from apps.carts.models import Cart

pytestmark = pytest.mark.django_db


def test_register_success():
    """RegisterSerializer crea un usuario y dispara CustomerProfile + Cart."""
    data = {
        "first_name": "María",
        "last_name": "González",
        "email": "register@example.com",
        "rut": "12.345.678-9",
        "phone": "+56912345678",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    }
    serializer = RegisterSerializer(data=data)

    assert serializer.is_valid() is True
    user = serializer.save()

    assert isinstance(user, User)
    assert user.email == "register@example.com"
    assert user.rut == "123456789"  # sanitizado
    assert user.check_password("SecurePass123!") is True
    assert hasattr(user, "profile")
    assert Cart.objects.filter(user=user).exists()


def test_register_password_mismatch():
    """RegisterSerializer rechaza contraseñas que no coinciden."""
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "mismatch@example.com",
        "password": "SecurePass123!",
        "password_confirm": "DifferentPass123!",
    }
    serializer = RegisterSerializer(data=data)

    assert serializer.is_valid() is False
    assert "password_confirm" in serializer.errors


def test_register_weak_password():
    """RegisterSerializer rechaza contraseñas débiles mediante Django validators."""
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "weak@example.com",
        "password": "123",
        "password_confirm": "123",
    }
    serializer = RegisterSerializer(data=data)

    assert serializer.is_valid() is False
    assert "password" in serializer.errors


def test_register_duplicate_email():
    """RegisterSerializer rechaza emails duplicados."""
    existing = UserFactory.create(email="dup@example.com")
    data = {
        "first_name": "Another",
        "last_name": "User",
        "email": existing.email,
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    }
    serializer = RegisterSerializer(data=data)

    assert serializer.is_valid() is False
    assert "email" in serializer.errors


def test_register_sanitizes_rut():
    """RegisterSerializer sanitiza el RUT eliminando puntos, guiones y mayúsculas."""
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "rut@example.com",
        "rut": "12.345.678-9",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    }
    serializer = RegisterSerializer(data=data)

    assert serializer.is_valid() is True
    user = serializer.save()

    assert user.rut == "123456789"


def test_register_serializer_does_not_expose_password():
    """La representación de salida del serializer no incluye campos de contraseña."""
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "expose@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    }
    serializer = RegisterSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert "password" not in serializer.data
    assert "password_confirm" not in serializer.data


def test_user_me_serializer_fields():
    """UserMeSerializer expone los campos públicos incluyendo is_admin."""
    user = UserFactory.create(
        first_name="María",
        last_name="González",
        email="me@example.com",
        is_staff=False,
    )
    serializer = UserMeSerializer(user)
    data = serializer.data

    assert data["id"] == user.id
    assert data["first_name"] == "María"
    assert data["last_name"] == "González"
    assert data["email"] == "me@example.com"
    assert data["is_admin"] is False


def test_user_me_serializer_for_admin():
    """UserMeSerializer refleja is_staff como is_admin=True para staff."""
    user = UserFactory.create(is_staff=True)
    serializer = UserMeSerializer(user)

    assert serializer.data["is_admin"] is True


def test_user_me_serializer_excludes_password():
    """UserMeSerializer nunca expone la contraseña del usuario."""
    user = UserFactory.create()
    serializer = UserMeSerializer(user)

    assert "password" not in serializer.data
