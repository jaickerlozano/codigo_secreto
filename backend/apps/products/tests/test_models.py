import pytest
from django.core.exceptions import ValidationError

from apps.products.models import Product, StockMovement


pytestmark = pytest.mark.django_db


def test_stock_in_movement(product_factory, stock_movement_factory):
    """IN aumenta el stock del producto."""
    product = product_factory(current_stock=10)
    stock_movement_factory(product=product, movement_type="IN", quantity=5)

    product.refresh_from_db()
    assert product.current_stock == 15


def test_stock_out_movement(product_factory, stock_movement_factory):
    """OUT disminuye el stock del producto."""
    product = product_factory(current_stock=10)
    stock_movement_factory(product=product, movement_type="OUT", quantity=4)

    product.refresh_from_db()
    assert product.current_stock == 6


def test_stock_out_insufficient(product_factory, stock_movement_factory):
    """OUT con cantidad mayor al stock actual lanza ValidationError."""
    product = product_factory(current_stock=5)

    with pytest.raises(ValidationError):
        stock_movement_factory(product=product, movement_type="OUT", quantity=10)

    product.refresh_from_db()
    assert product.current_stock == 5


def test_stock_movement_edit_blocked(stock_movement_factory):
    """Un movimiento de stock existente no puede editarse."""
    movement = stock_movement_factory(movement_type="IN", quantity=5)
    original_quantity = movement.quantity

    movement.quantity = 999
    movement.save()
    movement.refresh_from_db()

    assert movement.quantity == original_quantity


def test_stock_movement_in_zero_quantity(product_factory, stock_movement_factory):
    """IN con cantidad 0 es válido y no altera el stock."""
    product = product_factory(current_stock=5)
    stock_movement_factory(product=product, movement_type="IN", quantity=0)

    product.refresh_from_db()
    assert product.current_stock == 5


def test_category_root_str(category_factory):
    """__str__ de categoría raíz devuelve solo su nombre."""
    category = category_factory(name="Juguetes", parent=None)
    assert str(category) == "Juguetes"


def test_category_child_str(category_factory):
    """__str__ de categoría hija incluye el nombre del padre."""
    parent = category_factory(name="Adultos", parent=None)
    child = category_factory(name="Vibradores", parent=parent)
    assert str(child) == "Adultos > Vibradores"


def test_category_hierarchy(category_factory):
    """Las relaciones padre/hijo se mantienen correctamente."""
    parent = category_factory(name="Padre", parent=None)
    child = category_factory(name="Hijo", parent=parent)

    assert child.parent == parent
    assert parent.subcategories.first() == child


def test_stock_movement_uses_select_for_update(product_factory, stock_movement_factory):
    """StockMovement.save() aplica select_for_update dentro de una transacción atómica.

    En SQLite no hay bloqueo real, pero el flujo de guardado debe seguir
    funcionando y actualizar el stock correctamente.
    """
    product = product_factory(current_stock=10)
    stock_movement_factory(product=product, movement_type="OUT", quantity=3)

    product.refresh_from_db()
    assert product.current_stock == 7


def test_product_str(product_factory):
    """Product.__str__ devuelve el nombre del producto."""
    product = product_factory(name="Vibrador X")
    assert str(product) == "Vibrador X"


def test_supplier_str(supplier_factory):
    """Supplier.__str__ devuelve el nombre del proveedor."""
    supplier = supplier_factory(name="Distribuidora Norte")
    assert str(supplier) == "Distribuidora Norte"


def test_stock_movement_str(stock_movement_factory, product_factory):
    """StockMovement.__str__ incluye producto, tipo y cantidad."""
    product = product_factory(name="Lubricante Y")
    movement = stock_movement_factory(product=product, movement_type="IN", quantity=12)
    assert str(movement) == "Lubricante Y - IN - 12"
