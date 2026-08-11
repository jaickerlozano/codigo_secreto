"""Payment provider abstraction and the development-only mock provider.

Production fails closed: no provider is selectable unless DEBUG is enabled
and ``PAYMENT_PROVIDER=mock`` is set explicitly.
"""
import secrets

SUPPORTED_PAYMENT_METHODS = ("webpay", "flow", "mercadopago", "transfer")
MOCK_PROVIDER_ID = "mock"
MOCK_CONTINUATION_URL = "https://api.tu_pasarela.cl/mock-checkout"


class BasePaymentProvider:
    """Abstract payment provider; subclasses implement initiation only."""

    provider_id = None

    def __init__(self, order):
        self.order = order

    def initiate(self, *, method, idempotency_key):
        """Start a new attempt and return (gateway_reference, continuation_url)."""
        raise NotImplementedError

    def continuation_url(self, gateway_reference):
        """Build the continuation URL for an existing gateway reference."""
        raise NotImplementedError


class MockPaymentProvider(BasePaymentProvider):
    """Simulated development provider; every attempt gets a unique reference."""

    provider_id = MOCK_PROVIDER_ID

    def initiate(self, *, method, idempotency_key):
        gateway_reference = f"token_simulado_cl_f_{self.order.id}x{secrets.token_hex(4)}"
        return gateway_reference, self.continuation_url(gateway_reference)

    def continuation_url(self, gateway_reference):
        return f"{MOCK_CONTINUATION_URL}?token={gateway_reference}"
