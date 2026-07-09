import io

import pytest
from django.core.management import call_command

from apps.products.models import Product


pytestmark = pytest.mark.django_db


def test_seed_products_creates_44_products():
    """El comando seed_products crea exactamente 44 productos."""
    call_command("seed_products", stdout=io.StringIO())

    assert Product.objects.count() == 44


def test_seed_products_assigns_skus_101_to_144():
    """Cada producto sembrado tiene un SKU único entre 101 y 144."""
    call_command("seed_products", stdout=io.StringIO())

    skus = set(Product.objects.exclude(sku=None).values_list("sku", flat=True))
    expected = {str(sku) for sku in range(101, 145)}
    assert skus == expected
    assert len(skus) == 44


def test_seed_products_is_idempotent():
    """Ejecutar el comando dos veces no duplica productos y actualiza los datos."""
    call_command("seed_products", stdout=io.StringIO())
    first_count = Product.objects.count()
    first_ids = set(Product.objects.values_list("id", flat=True))

    call_command("seed_products", stdout=io.StringIO())
    second_count = Product.objects.count()
    second_ids = set(Product.objects.values_list("id", flat=True))

    assert first_count == 44
    assert second_count == 44
    assert first_ids == second_ids


def test_seed_products_reset_flag_deletes_seeded_products():
    """La opción --reset elimina los productos sembrados por SKU antes de volver a crearlos."""
    call_command("seed_products", stdout=io.StringIO())
    assert Product.objects.count() == 44

    call_command("seed_products", "--reset", stdout=io.StringIO())
    assert Product.objects.count() == 44


def test_seed_products_reset_does_not_touch_non_seeded_products(product_factory):
    """--reset no elimina productos que no fueron creados por el seeder."""
    product_factory(sku=None, name="Producto externo")
    call_command("seed_products", stdout=io.StringIO())

    assert Product.objects.filter(name="Producto externo").exists()

    call_command("seed_products", "--reset", stdout=io.StringIO())
    assert Product.objects.filter(name="Producto externo").exists()
    assert Product.objects.count() == 45


def test_seed_products_summary_output():
    """El comando imprime un resumen con la cantidad de productos."""
    out = io.StringIO()
    call_command("seed_products", stdout=out)
    output = out.getvalue()

    assert "44" in output
    assert "producto" in output.lower()
