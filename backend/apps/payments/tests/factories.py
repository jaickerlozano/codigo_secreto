import factory
from faker import Faker

from apps.orders.tests.factories import OrderFactory
from apps.payments.models import Transaction

faker = Faker("es_CL")


class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for Transaction.

    Defaults to a PENDING transaction linked to a fresh order, with the
    transaction amount matching the order total.
    """

    class Meta:
        model = Transaction

    order = factory.SubFactory(OrderFactory)
    amount = factory.LazyAttribute(lambda o: o.order.total)
    status = "PENDING"
    gateway_reference = factory.LazyAttribute(
        lambda o: f"token_simulado_cl_f_{o.order.id}x99"
    )
    payment_method = "MÉTODO SIMULADO"
