import factory

from apps.authentication.tests.factories import UserFactory
from apps.carts.models import Cart, CartItem
from apps.products.tests.factories import ProductFactory


class CartFactory(factory.django.DjangoModelFactory):
    """Factory for Cart.

    ``UserFactory`` already triggers the post_save signal that creates a Cart,
    so this factory uses ``django_get_or_create`` on ``user`` to reuse the
    signal-created cart instead of raising an IntegrityError.
    """

    class Meta:
        model = Cart
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)


class CartItemFactory(factory.django.DjangoModelFactory):
    """Factory for CartItem.

    Defaults to a quantity of 2. ``django_get_or_create`` is intentionally
    omitted so tests can explicitly trigger ``IntegrityError`` on the
    ``unique_together`` constraint when needed.
    """

    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 2
