import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.products.serializers import (
    CategorySerializer,
    ProductSerializer,
    StockMovementSerializer,
)


pytestmark = pytest.mark.django_db


def test_product_serializer_makes_stock_read_only_on_update(product_factory):
    """ProductSerializer marca current_stock como read-only al actualizar."""
    product = product_factory(current_stock=10)
    data = {"name": product.name, "current_stock": 999, "price": product.price}

    serializer = ProductSerializer(instance=product, data=data, partial=True)
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    product.refresh_from_db()
    assert product.current_stock == 10


def test_product_serializer_validation(product_factory, category_factory, supplier_factory):
    """ProductSerializer valida un payload completo para crear un producto."""
    category = category_factory(parent=None)
    supplier = supplier_factory()
    data = {
        "name": "Vibrador X",
        "description": "Descripción de prueba",
        "category": category.id,
        "supplier": supplier.id,
        "price": 15000,
        "current_stock": 10,
        "minimum_stock": 2,
    }

    serializer = ProductSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    product = serializer.save()
    assert product.name == "Vibrador X"
    assert product.price == 15000


def test_category_serializer_nested(category_factory):
    """CategorySerializer anida subcategorías recursivamente."""
    root = category_factory(name="Adultos", parent=None)
    child = category_factory(name="Vibradores", parent=root)
    grandchild = category_factory(name="Mini vibradores", parent=child)

    serializer = CategorySerializer(root)
    data = serializer.data

    assert data["name"] == "Adultos"
    assert len(data["subcategories"]) == 1
    assert data["subcategories"][0]["name"] == "Vibradores"
    assert len(data["subcategories"][0]["subcategories"]) == 1
    assert data["subcategories"][0]["subcategories"][0]["name"] == "Mini vibradores"


def test_category_serializer_empty_children(category_factory):
    """CategorySerializer devuelve [] cuando la categoría no tiene hijas."""
    leaf = category_factory(name="Hoja", parent=None)
    serializer = CategorySerializer(leaf)
    assert serializer.data["subcategories"] == []


def test_stock_movement_serializer_readonly(stock_movement_factory):
    """El campo timestamp de StockMovementSerializer es de solo lectura."""
    movement = stock_movement_factory()
    serializer = StockMovementSerializer(movement)
    assert "timestamp" in serializer.data


def test_stock_movement_serializer_error_translation(product_factory):
    """StockMovementSerializer traduce ValidationError del modelo a DRF."""
    product = product_factory(current_stock=2)
    data = {"product": product.id, "movement_type": "OUT", "quantity": 10}

    serializer = StockMovementSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    with pytest.raises(DRFValidationError) as exc_info:
        serializer.save()

    assert "quantity" in exc_info.value.detail
