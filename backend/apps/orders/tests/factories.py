import factory
from faker import Faker

from apps.authentication.tests.factories import UserFactory
from apps.orders.models import Order, OrderItem
from apps.products.tests.factories import ProductFactory
from apps.shipping.tests.factories import ComunaFactory

faker = Faker("es_CL")


class OrderFactory(factory.django.DjangoModelFactory):
    """Factory for Order.

    Defaults to an authenticated user order linked to a fresh comuna.
    Override ``user`` with ``None`` to create guest orders, and set the
    appropriate guest fields in that case.
    """

    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    guest_email = factory.LazyAttribute(lambda o: None if o.user else f"{faker.uuid4()}@guest.test")
    guest_name = factory.LazyAttribute(lambda o: None if o.user else faker.name())
    phone = factory.LazyFunction(lambda: faker.phone_number()[:20])
    comuna = factory.SubFactory(ComunaFactory)
    shipping_address = factory.Faker("street_address")
    apartment_office = factory.Faker("building_number")
    subtotal = factory.LazyFunction(lambda: faker.random_int(min=5000, max=50000))
    shipping_cost = factory.LazyFunction(lambda: faker.random_int(min=1000, max=10000))
    total = factory.LazyAttribute(lambda o: o.subtotal + o.shipping_cost)
    status = "PENDING"


class OrderItemFactory(factory.django.DjangoModelFactory):
    """Factory for OrderItem.

    Freezes the product's current name and price at creation time to mimic the
    production serializer behavior.
    """

    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    product_name = factory.LazyAttribute(lambda o: o.product.name)
    price = factory.LazyAttribute(lambda o: o.product.price)
    quantity = 2
