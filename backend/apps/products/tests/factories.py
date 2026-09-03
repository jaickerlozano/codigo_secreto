import factory
from faker import Faker

from apps.products.models import Category, Product, StockMovement, Supplier

faker = Faker("es_CL")


class SupplierFactory(factory.django.DjangoModelFactory):
    """Factory for Supplier.

    Generates a supplier with a unique RUT-style identifier embedded in the
    name to keep test data deterministic.
    """

    class Meta:
        model = Supplier
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Proveedor {n}")
    contact = factory.Faker("name")
    email = factory.LazyAttribute(lambda o: f"{faker.uuid4()}@supplier.test")
    phone = factory.Sequence(lambda n: f"+569{n:08d}")
    address = factory.Faker("street_address")


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for Category.

    Defaults to a root category (``parent=None``). Pass a parent instance or
    ``factory.SubFactory`` to build recursive category trees.
    """

    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Categoría {n}")
    description = factory.Faker("sentence")
    parent = None


class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for Product.

    Creates a product linked to a fresh root category and supplier. The
    factory does **not** create a stock movement automatically; that behavior
    belongs to the product creation view.
    """

    class Meta:
        model = Product
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Producto {n}")
    description = factory.Faker("sentence")
    category = factory.SubFactory(CategoryFactory, parent=None)
    supplier = factory.SubFactory(SupplierFactory)
    price = factory.LazyFunction(lambda: faker.random_int(min=5000, max=50000))
    current_stock = 10
    minimum_stock = 0


class StockMovementFactory(factory.django.DjangoModelFactory):
    """Factory for StockMovement.

    Defaults to an ``IN`` movement so it does not accidentally exhaust the
    product's initial stock. Override ``movement_type`` and ``quantity`` to
    exercise ``OUT`` behavior.
    """

    class Meta:
        model = StockMovement

    product = factory.SubFactory(ProductFactory)
    movement_type = "IN"
    quantity = 5
    description = factory.Faker("sentence")
