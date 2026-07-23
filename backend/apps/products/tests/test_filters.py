import pytest
from rest_framework import status

from apps.products.models import Category, Product


pytestmark = pytest.mark.django_db


def _results(response):
    """Return the list of results from a paginated DRF response."""
    data = response.json()
    return data.get("results", data)


def _ids(response):
    """Return a set of ids returned by a list response."""
    return {item["id"] for item in _results(response)}


# ---------------------------------------------------------------------------
# Category filter tests
# ---------------------------------------------------------------------------

def test_filter_by_valid_category_includes_descendants(staff_client, category_tree, product_factory):
    """?category=root returns products from category AND all descendants."""
    root = category_tree["root"]
    child = category_tree["child"]
    grandchild = category_tree["grandchild"]

    product_root = product_factory(category=root)
    product_child = product_factory(category=child)
    product_grandchild = product_factory(category=grandchild)
    product_other = product_factory()

    response = staff_client.get(f"/api/products/?category={root.id}")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product_root.id in ids
    assert product_child.id in ids
    assert product_grandchild.id in ids
    assert product_other.id not in ids


def test_filter_by_invalid_category_returns_404(staff_client, product_factory):
    """?category=99999 returns 404 for non-existent category."""
    product_factory()
    product_factory()

    response = staff_client.get("/api/products/?category=99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_filter_by_deep_category_tree(staff_client, category_factory, product_factory):
    """Deep tree (6+ levels) includes all descendants."""
    level1 = category_factory(name="L1", parent=None)
    level2 = category_factory(name="L2", parent=level1)
    level3 = category_factory(name="L3", parent=level2)
    level4 = category_factory(name="L4", parent=level3)
    level5 = category_factory(name="L5", parent=level4)
    level6 = category_factory(name="L6", parent=level5)

    p1 = product_factory(category=level1)
    p2 = product_factory(category=level2)
    p3 = product_factory(category=level3)
    p4 = product_factory(category=level4)
    p5 = product_factory(category=level5)
    p6 = product_factory(category=level6)
    p_other = product_factory()

    response = staff_client.get(f"/api/products/?category={level1.id}")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert p1.id in ids
    assert p2.id in ids
    assert p3.id in ids
    assert p4.id in ids
    assert p5.id in ids
    assert p6.id in ids
    assert p_other.id not in ids


# ---------------------------------------------------------------------------
# Price filter tests
# ---------------------------------------------------------------------------

def test_filter_by_min_price(staff_client, product_factory):
    """?min_price filters products with price >= value."""
    product_factory(price=5000)
    product_mid = product_factory(price=15000)
    product_factory(price=50000)

    response = staff_client.get("/api/products/?min_price=10000")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product_mid.id in ids
    assert len(ids) == 2  # mid and high


def test_filter_by_max_price(staff_client, product_factory):
    """?max_price filters products with price <= value."""
    product_factory(price=5000)
    product_mid = product_factory(price=15000)
    product_factory(price=50000)

    response = staff_client.get("/api/products/?max_price=20000")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product_mid.id in ids
    assert len(ids) == 2  # low and mid


def test_filter_by_price_range(staff_client, product_factory):
    """?min_price=X&max_price=Y filters products in range [X, Y]."""
    product_low = product_factory(price=5000)
    product_mid = product_factory(price=15000)
    product_high = product_factory(price=50000)

    response = staff_client.get("/api/products/?min_price=10000&max_price=20000")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product_mid.id in ids
    assert product_low.id not in ids
    assert product_high.id not in ids


def test_filter_by_invalid_price_ignored(staff_client, product_factory):
    """Invalid min_price/max_price values are ignored."""
    product = product_factory()

    response = staff_client.get("/api/products/?min_price=abc&max_price=xyz")
    assert response.status_code == status.HTTP_200_OK
    assert product.id in _ids(response)


# ---------------------------------------------------------------------------
# Experience level filter tests
# ---------------------------------------------------------------------------

def test_filter_by_experience_level_exact(staff_client, product_factory):
    """?experience_level=N filters by exact level."""
    product_factory(experience_level=1)
    product_factory(experience_level=2)
    p3 = product_factory(experience_level=3)
    product_factory(experience_level=4)
    product_factory(experience_level=5)

    response = staff_client.get("/api/products/?experience_level=3")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert p3.id in ids
    assert len(ids) == 1


def test_filter_by_experience_level_gte(staff_client, product_factory):
    """?experience_level__gte=N filters by level >= N."""
    product_factory(experience_level=1)
    product_factory(experience_level=2)
    p3 = product_factory(experience_level=3)
    p4 = product_factory(experience_level=4)
    p5 = product_factory(experience_level=5)

    response = staff_client.get("/api/products/?experience_level__gte=3")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert p3.id in ids
    assert p4.id in ids
    assert p5.id in ids
    assert len(ids) == 3


def test_filter_by_experience_level_lte(staff_client, product_factory):
    """?experience_level__lte=N filters by level <= N."""
    p1 = product_factory(experience_level=1)
    p2 = product_factory(experience_level=2)
    p3 = product_factory(experience_level=3)
    product_factory(experience_level=4)
    product_factory(experience_level=5)

    response = staff_client.get("/api/products/?experience_level__lte=2")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert p1.id in ids
    assert p2.id in ids
    assert p3.id not in ids
    assert len(ids) == 2


# ---------------------------------------------------------------------------
# Combined filter tests
# ---------------------------------------------------------------------------

def test_combined_category_price_experience_search(
    staff_client, category_factory, product_factory, supplier_factory
):
    """Combined filters (category + price + experience_level + search) work with AND logic."""
    root = category_factory(name="Root", parent=None)
    child = category_factory(name="Child", parent=root)
    supplier = supplier_factory()

    p1 = product_factory(
        name="Vibrador Pro",
        category=root,
        price=20000,
        experience_level=4,
        supplier=supplier,
    )
    p2 = product_factory(
        name="Lubricante Básico",
        category=child,
        price=10000,
        experience_level=1,
        supplier=supplier,
    )
    p3 = product_factory(
        name="Otro Producto",
        category=root,
        price=30000,
        experience_level=4,
        supplier=supplier,
    )
    product_factory(
        name="Producto Externo",
        price=20000,
        experience_level=4,
    )

    # Filter: category=root AND min_price=15000 AND experience_level=4 AND search=vibrador
    response = staff_client.get(
        f"/api/products/?category={root.id}&min_price=15000&experience_level=4&search=vibrador"
    )
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert p1.id in ids
    assert p2.id not in ids  # price too low
    assert p3.id not in ids  # doesn't match search
    assert len(ids) == 1


def test_combined_category_and_supplier(staff_client, category_factory, supplier_factory, product_factory):
    """Category and supplier filters combined."""
    cat1 = category_factory(name="Cat1", parent=None)
    cat2 = category_factory(name="Cat2", parent=None)
    sup1 = supplier_factory()
    sup2 = supplier_factory()

    p1 = product_factory(category=cat1, supplier=sup1)
    p2 = product_factory(category=cat1, supplier=sup2)
    p3 = product_factory(category=cat2, supplier=sup1)

    response = staff_client.get(f"/api/products/?category={cat1.id}&supplier={sup1.id}")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert p1.id in ids
    assert p2.id not in ids
    assert p3.id not in ids
    assert len(ids) == 1