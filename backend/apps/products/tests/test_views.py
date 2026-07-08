import pytest
from rest_framework import status

from apps.products.models import Product, StockMovement


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _results(response):
    """Return the list of results from a paginated DRF response."""
    data = response.json()
    return data.get("results", data)


def _ids(response):
    """Return a set of ids returned by a list response."""
    return {item["id"] for item in _results(response)}


# ---------------------------------------------------------------------------
# Product CRUD & permissions
# ---------------------------------------------------------------------------

def test_product_list_public(api_client, product_factory):
    """GET /api/products/ es público (AllowAny)."""
    product_factory()
    response = api_client.get("/api/products/")
    assert response.status_code == status.HTTP_200_OK


def test_product_create_requires_staff(authenticated_client, category_factory, supplier_factory):
    """POST /api/products/ requiere usuario staff."""
    category = category_factory(parent=None)
    supplier = supplier_factory()
    payload = {
        "name": "Vibrador X",
        "category": category.id,
        "supplier": supplier.id,
        "price": 15000,
        "current_stock": 10,
    }

    response = authenticated_client.post("/api/products/", payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_product_update_requires_staff(staff_client, authenticated_client, product_factory):
    """PUT/PATCH /api/products/{id}/ requiere usuario staff."""
    product = product_factory()
    payload = {"name": "Nombre modificado"}

    response = authenticated_client.patch(f"/api/products/{product.id}/", payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_product_delete_requires_staff(authenticated_client, product_factory):
    """DELETE /api/products/{id}/ requiere usuario staff."""
    product = product_factory()
    response = authenticated_client.delete(f"/api/products/{product.id}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_product_create_with_stock_generates_movement(staff_client, category_factory, supplier_factory):
    """Crear producto con stock > 0 genera un movimiento IN."""
    category = category_factory(parent=None)
    supplier = supplier_factory()
    payload = {
        "name": "Vibrador X",
        "category": category.id,
        "supplier": supplier.id,
        "price": 15000,
        "current_stock": 10,
    }

    response = staff_client.post("/api/products/", payload)
    assert response.status_code == status.HTTP_201_CREATED

    product_id = response.json()["id"]
    movement = StockMovement.objects.filter(product_id=product_id).first()
    assert movement is not None
    assert movement.movement_type == "IN"
    assert movement.quantity == 10


def test_product_create_zero_stock_no_movement(staff_client, category_factory, supplier_factory):
    """Crear producto con stock = 0 no genera movimiento de stock."""
    category = category_factory(parent=None)
    supplier = supplier_factory()
    payload = {
        "name": "Lubricante Y",
        "category": category.id,
        "supplier": supplier.id,
        "price": 8000,
        "current_stock": 0,
    }

    response = staff_client.post("/api/products/", payload)
    assert response.status_code == status.HTTP_201_CREATED

    product_id = response.json()["id"]
    assert StockMovement.objects.filter(product_id=product_id).count() == 0


def test_product_create_negative_stock_rejected(staff_client, category_factory, supplier_factory):
    """Crear producto con stock negativo devuelve 400."""
    category = category_factory(parent=None)
    supplier = supplier_factory()
    payload = {
        "name": "Producto inválido",
        "category": category.id,
        "supplier": supplier.id,
        "price": 10000,
        "current_stock": -1,
    }

    response = staff_client.post("/api/products/", payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_product_create_image_optional(staff_client, category_factory, supplier_factory):
    """El campo image es opcional al crear un producto."""
    category = category_factory(parent=None)
    supplier = supplier_factory()
    payload = {
        "name": "Producto sin imagen",
        "category": category.id,
        "supplier": supplier.id,
        "price": 12000,
        "current_stock": 5,
    }

    response = staff_client.post("/api/products/", payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("image") is None


def test_update_stock_readonly(staff_client, product_factory):
    """PATCH a current_stock es ignorado por el serializer."""
    product = product_factory(current_stock=10)
    payload = {"current_stock": 999}

    response = staff_client.patch(f"/api/products/{product.id}/", payload)
    assert response.status_code == status.HTTP_200_OK

    product.refresh_from_db()
    assert product.current_stock == 10


# ---------------------------------------------------------------------------
# Product filters & search
# ---------------------------------------------------------------------------

def test_filter_by_category(staff_client, category_tree, product_factory):
    """?category=root incluye productos de la categoría y sus descendientes."""
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


def test_filter_by_nonexistent_category_returns_all(staff_client, product_factory):
    """?category=99999 devuelve todos los productos sin error."""
    product1 = product_factory()
    product2 = product_factory()

    response = staff_client.get("/api/products/?category=99999")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product1.id in ids
    assert product2.id in ids


def test_filter_by_supplier(staff_client, supplier_factory, product_factory):
    """?supplier={id} filtra productos por proveedor."""
    supplier_a = supplier_factory()
    supplier_b = supplier_factory()
    product_a1 = product_factory(supplier=supplier_a)
    product_a2 = product_factory(supplier=supplier_a)
    product_b = product_factory(supplier=supplier_b)

    response = staff_client.get(f"/api/products/?supplier={supplier_a.id}")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product_a1.id in ids
    assert product_a2.id in ids
    assert product_b.id not in ids


def test_filter_by_price_range(staff_client, product_factory):
    """?min_price y ?max_price filtran productos por rango de precio."""
    product_low = product_factory(price=5000)
    product_mid = product_factory(price=15000)
    product_high = product_factory(price=50000)

    response = staff_client.get("/api/products/?min_price=10000&max_price=20000")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert product_mid.id in ids
    assert product_low.id not in ids
    assert product_high.id not in ids


def test_filter_by_invalid_price_range_ignored(staff_client, product_factory):
    """?min_price/max_price inválidos son ignorados y se devuelven todos."""
    product = product_factory()

    response = staff_client.get("/api/products/?min_price=abc&max_price=xyz")
    assert response.status_code == status.HTTP_200_OK
    assert product.id in _ids(response)


def test_search_by_name(staff_client, product_factory):
    """?search=vibrador encuentra productos por nombre."""
    product_factory(name="Vibrador A")
    product_factory(name="Lubricante B")

    response = staff_client.get("/api/products/?search=vibrador")
    assert response.status_code == status.HTTP_200_OK

    names = {item["name"] for item in _results(response)}
    assert "Vibrador A" in names
    assert "Lubricante B" not in names


def test_search_by_description(staff_client, product_factory):
    """?search=parejas encuentra productos por descripción."""
    product_factory(name="Producto A", description="Ideal para parejas")
    product_factory(name="Producto B", description="Uso individual")

    response = staff_client.get("/api/products/?search=parejas")
    assert response.status_code == status.HTTP_200_OK

    names = {item["name"] for item in _results(response)}
    assert "Producto A" in names
    assert "Producto B" not in names


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def test_category_menu_filter(api_client, category_factory):
    """?menu=true devuelve solo categorías raíz (parent=null)."""
    root1 = category_factory(name="Raíz 1", parent=None)
    root2 = category_factory(name="Raíz 2", parent=None)
    child = category_factory(name="Hija", parent=root1)

    response = api_client.get("/api/categories/?menu=true")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert root1.id in ids
    assert root2.id in ids
    assert child.id not in ids


def test_category_list_without_menu_returns_all(api_client, category_factory):
    """GET /api/categories/ sin ?menu devuelve todas las categorías."""
    root = category_factory(name="Raíz", parent=None)
    child = category_factory(name="Hija", parent=root)

    response = api_client.get("/api/categories/")
    assert response.status_code == status.HTTP_200_OK

    ids = _ids(response)
    assert root.id in ids
    assert child.id in ids


# ---------------------------------------------------------------------------
# Stock movements
# ---------------------------------------------------------------------------

def test_stock_movement_create(staff_client, product_factory):
    """POST /api/stock-movements/ crea un movimiento y actualiza stock."""
    product = product_factory(current_stock=10)
    payload = {"product": product.id, "movement_type": "IN", "quantity": 5}

    response = staff_client.post("/api/stock-movements/", payload)
    assert response.status_code == status.HTTP_201_CREATED

    product.refresh_from_db()
    assert product.current_stock == 15


def test_stock_movement_create_insufficient_stock(staff_client, product_factory):
    """POST /api/stock-movements/ con OUT excesivo devuelve 400."""
    product = product_factory(current_stock=2)
    payload = {"product": product.id, "movement_type": "OUT", "quantity": 10}

    response = staff_client.post("/api/stock-movements/", payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "quantity" in response.json()


def test_stock_movement_list_ordered_by_newest(staff_client, stock_movement_factory):
    """GET /api/stock-movements/ ordena por -timestamp."""
    movement1 = stock_movement_factory()
    movement2 = stock_movement_factory()
    movement3 = stock_movement_factory()

    response = staff_client.get("/api/stock-movements/")
    assert response.status_code == status.HTTP_200_OK

    ids = [item["id"] for item in _results(response)]
    assert ids == [movement3.id, movement2.id, movement1.id]


def test_stock_movement_405_update(staff_client, stock_movement_factory):
    """PUT/PATCH /api/stock-movements/{id}/ devuelve 405."""
    movement = stock_movement_factory()
    response = staff_client.put(f"/api/stock-movements/{movement.id}/", {"quantity": 1})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = staff_client.patch(f"/api/stock-movements/{movement.id}/", {"quantity": 1})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_stock_movement_405_delete(staff_client, stock_movement_factory):
    """DELETE /api/stock-movements/{id}/ devuelve 405."""
    movement = stock_movement_factory()
    response = staff_client.delete(f"/api/stock-movements/{movement.id}/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

def test_supplier_search_by_name(api_client, supplier_factory):
    """?search=Norte filtra proveedores por nombre."""
    supplier_factory(name="Distribuidora Norte")
    supplier_factory(name="Importadora Sur")

    response = api_client.get("/api/suppliers/?search=Norte")
    assert response.status_code == status.HTTP_200_OK

    names = {item["name"] for item in _results(response)}
    assert "Distribuidora Norte" in names
    assert "Importadora Sur" not in names
