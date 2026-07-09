import pytest
from django.db import IntegrityError

from apps.products.models import Product


pytestmark = pytest.mark.django_db


def test_product_has_sku_field():
    """El modelo Product debe tener un campo sku opcional y único."""
    field = Product._meta.get_field("sku")
    assert field.get_internal_type() == "CharField"
    assert field.max_length == 50
    assert field.unique is True
    assert field.null is True
    assert field.blank is True


def test_product_has_ui_fields():
    """El modelo Product debe tener los campos de UI requeridos."""
    icon_field = Product._meta.get_field("icon")
    assert icon_field.get_internal_type() == "CharField"
    assert icon_field.max_length == 100
    assert icon_field.default == "box"

    gradient_field = Product._meta.get_field("gradient")
    assert gradient_field.get_internal_type() == "CharField"
    assert gradient_field.max_length == 200
    assert gradient_field.default == "from-gray-500 to-gray-700"

    experience_field = Product._meta.get_field("experience_level")
    assert experience_field.get_internal_type() == "PositiveSmallIntegerField"
    assert experience_field.default == 3

    features_field = Product._meta.get_field("features")
    assert features_field.get_internal_type() == "JSONField"
    assert features_field.default == list

    badge_field = Product._meta.get_field("badge")
    assert badge_field.get_internal_type() == "CharField"
    assert badge_field.max_length == 50
    assert badge_field.null is True
    assert badge_field.blank is True


def test_product_sku_unique(product_factory):
    """No se pueden crear dos productos con el mismo SKU."""
    product_factory(sku="CS-101")

    with pytest.raises(IntegrityError):
        product_factory(sku="CS-101")


def test_product_sku_optional(product_factory):
    """Un producto puede guardarse sin SKU (None)."""
    product = product_factory(sku=None)
    assert product.sku is None


def test_product_ui_defaults(product_factory):
    """Los campos de UI usan los valores por defecto esperados."""
    product = product_factory()
    assert product.icon == "box"
    assert product.gradient == "from-gray-500 to-gray-700"
    assert product.experience_level == 3
    assert product.features == []
    assert product.badge is None


def test_product_ui_values_persist(product_factory):
    """Los valores explícitos de UI se guardan correctamente."""
    product = product_factory(
        sku="CS-TEST",
        icon="flame",
        gradient="from-pink-500 to-rose-700",
        experience_level=5,
        features=["Silencioso", "Recargable"],
        badge="Más vendido",
    )
    product.refresh_from_db()
    assert product.sku == "CS-TEST"
    assert product.icon == "flame"
    assert product.gradient == "from-pink-500 to-rose-700"
    assert product.experience_level == 5
    assert product.features == ["Silencioso", "Recargable"]
    assert product.badge == "Más vendido"
