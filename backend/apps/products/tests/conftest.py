import pytest

from apps.products.tests.factories import (
    CategoryFactory,
    ProductFactory,
    StockMovementFactory,
    SupplierFactory,
)


@pytest.fixture
def supplier_factory():
    """Return the SupplierFactory class."""
    return SupplierFactory


@pytest.fixture
def category_factory():
    """Return the CategoryFactory class."""
    return CategoryFactory


@pytest.fixture
def product_factory():
    """Return the ProductFactory class."""
    return ProductFactory


@pytest.fixture
def stock_movement_factory():
    """Return the StockMovementFactory class."""
    return StockMovementFactory


@pytest.fixture
def product_with_stock(db, product_factory):
    """Product with a positive initial stock."""
    return product_factory(current_stock=20)


@pytest.fixture
def category_tree(db, category_factory):
    """Three-level category hierarchy: root -> child -> grandchild."""
    root = category_factory(name="Adultos", parent=None)
    child = category_factory(name="Vibradores", parent=root)
    grandchild = category_factory(name="Mini vibradores", parent=child)
    return {
        "root": root,
        "child": child,
        "grandchild": grandchild,
    }
