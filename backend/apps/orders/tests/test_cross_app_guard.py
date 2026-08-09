from pathlib import Path


def test_orders_modules_do_not_import_product_or_shipping_models_directly():
    orders_dir = Path(__file__).parents[1]
    sources = [path.read_text() for path in orders_dir.glob("*.py")]

    assert all("from apps.products.models" not in source for source in sources)
    assert all("from apps.shipping.models" not in source for source in sources)
