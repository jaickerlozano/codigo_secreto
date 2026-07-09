import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.products.admin import ProductAdmin
from apps.products.models import Product


pytestmark = pytest.mark.django_db


def test_product_admin_list_display_includes_new_fields():
    """ProductAdmin list_display incluye SKU, badge y experience_level."""
    assert "sku" in ProductAdmin.list_display
    assert "badge" in ProductAdmin.list_display
    assert "experience_level" in ProductAdmin.list_display


def test_product_admin_search_fields_includes_sku():
    """ProductAdmin permite buscar por SKU."""
    assert "sku" in ProductAdmin.search_fields


def test_product_admin_fieldsets_include_ui_config():
    """ProductAdmin agrupa los campos UI en un fieldset."""
    fieldsets = dict(ProductAdmin.fieldsets or [])
    assert "UI Config" in fieldsets

    ui_fields = fieldsets["UI Config"]["fields"]
    assert "icon" in ui_fields
    assert "gradient" in ui_fields
    assert "experience_level" in ui_fields
    assert "features" in ui_fields
    assert "badge" in ui_fields


def test_product_admin_edit_all_new_fields(product_factory):
    """El formulario de admin guarda correctamente todos los campos nuevos."""
    product = product_factory(sku="CS-ADMIN")
    payload = {
        "name": product.name,
        "category": product.category_id,
        "supplier": product.supplier_id,
        "price": product.price,
        "current_stock": product.current_stock,
        "minimum_stock": product.minimum_stock,
        "sku": "CS-ADMIN-UPDATED",
        "icon": "sparkles",
        "gradient": "from-violet-500 to-fuchsia-700",
        "experience_level": 4,
        "features": '["Waterproof", "USB"]',
        "badge": "Nuevo",
    }

    request = RequestFactory().get("/admin/products/product/")
    model_admin = ProductAdmin(Product, AdminSite())
    FormClass = model_admin.get_form(request, obj=product)
    form = FormClass(data=payload, instance=product)

    assert form.is_valid(), form.errors
    form.save()

    product.refresh_from_db()
    assert product.sku == "CS-ADMIN-UPDATED"
    assert product.icon == "sparkles"
    assert product.gradient == "from-violet-500 to-fuchsia-700"
    assert product.experience_level == 4
    assert product.features == ["Waterproof", "USB"]
    assert product.badge == "Nuevo"
