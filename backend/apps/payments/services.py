"""Backend-owned payment initiation and mock approval: fail-closed provider
selection, order state validation, idempotent replay, transaction creation
and the development-only approval transition. Authorization stays at the
request boundary (``authorize_order_access``).
"""
from django.conf import settings
from django.db import IntegrityError, transaction

from apps.orders.models import Order

from .models import Transaction
from .providers import MOCK_PROVIDER_ID, SUPPORTED_PAYMENT_METHODS, MockPaymentProvider

IDEMPOTENCY_KEY_MAX_LENGTH = 64  # mirrors the checkout-key client contract


class InvalidPaymentKeyError(ValueError): """The Idempotency-Key header cannot be used safely."""
class PaymentProviderUnavailableError(RuntimeError): """No provider is enabled; initiation fails closed."""
class PaymentMethodUnsupportedError(ValueError): """The order's payment method is not an approved simulated method."""
class PaymentIdempotencyConflictError(ValueError): """An idempotency key was reused for a different payment."""
class PaymentStateError(ValueError): """The order is not in a payable state (carries the status label)."""
class PaymentAlreadyPaidError(ValueError): """The order already has an APPROVED transaction."""
class PaymentApprovalError(ValueError): """The transaction cannot be approved in its current state."""


def normalize_idempotency_key(raw):
    """Normalize the Idempotency-Key header; None when absent or blank."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if not isinstance(raw, str) or len(raw.strip()) > IDEMPOTENCY_KEY_MAX_LENGTH:
        raise InvalidPaymentKeyError("Invalid idempotency key.")
    return raw.strip()


def _select_provider(order):
    """Return the active provider, or None when payment is disabled."""
    if settings.DEBUG and settings.PAYMENT_PROVIDER == MOCK_PROVIDER_ID:
        return MockPaymentProvider(order)
    return None


def _normalize_method(method):
    """Validate the order's payment method against the approved simulated set."""
    if not isinstance(method, str) or method.strip().lower() not in SUPPORTED_PAYMENT_METHODS:
        raise PaymentMethodUnsupportedError()
    return method.strip().lower()


def _replay_conflict(existing, method):
    """An attempt only replays when it is PENDING and method-consistent."""
    return existing.status != "PENDING" or existing.payment_method != method


def initiate_payment(*, order, idempotency_key):
    """Create a PENDING transaction or replay the owned order's attempt for
    the same key; fails closed when the mock provider is not enabled."""
    provider = _select_provider(order)
    if provider is None:
        raise PaymentProviderUnavailableError()
    method = _normalize_method(order.payment_method)
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order.id)
        if order.status != "PENDING":
            raise PaymentStateError(order.get_status_display())
        if order.transactions.filter(status="APPROVED").exists():
            raise PaymentAlreadyPaidError()
        if idempotency_key:
            existing = Transaction.objects.filter(
                idempotency_key=idempotency_key
            ).select_for_update().first()
            if existing is not None:
                if existing.order_id != order.id or _replay_conflict(existing, method):
                    raise PaymentIdempotencyConflictError()
                return existing, provider.continuation_url(existing.gateway_reference)
        gateway_reference, payment_url = provider.initiate(method=method, idempotency_key=idempotency_key)
        try:
            attempt = Transaction.objects.create(
                order=order, amount=order.total, status="PENDING",
                gateway_reference=gateway_reference, payment_method=method,
                provider=provider.provider_id, idempotency_key=idempotency_key,
            )
        except IntegrityError:
            existing = Transaction.objects.filter(order=order, idempotency_key=idempotency_key).select_for_update().get()
            if _replay_conflict(existing, method):
                raise PaymentIdempotencyConflictError()
            return existing, provider.continuation_url(existing.gateway_reference)
    return attempt, payment_url


def _clear_purchased_cart_quantities(order):
    """Remove only the frozen purchased quantities from the authenticated cart.

    Rows with equal quantity are deleted, larger carts are decremented, and
    unrelated or missing products are never touched. Guest carts are
    client-side and never touched here.
    """
    if order.user_id is None:
        return
    purchased = {}
    for item in order.items.all():
        if item.product_id:
            purchased[item.product_id] = purchased.get(item.product_id, 0) + item.quantity
    if not purchased:
        return
    cart_items = order.user.cart.items.select_for_update().filter(product_id__in=purchased)
    for cart_item in cart_items:
        if cart_item.quantity <= purchased[cart_item.product_id]:
            cart_item.delete()
        else:
            cart_item.quantity -= purchased[cart_item.product_id]
            cart_item.save(update_fields=["quantity"])


def approve_payment(*, order, transaction_id):
    """Approve an owned PENDING mock transaction exactly once.

    Under one atomic lock, the PENDING->APPROVED transaction and PENDING->PAID
    order transitions happen together; a repeat approval returns the same
    approved state without duplicate effects. Fails closed outside
    DEBUG + PAYMENT_PROVIDER=mock.
    """
    provider = _select_provider(order)
    if provider is None:
        raise PaymentProviderUnavailableError()
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order.id)
        attempt = Transaction.objects.select_for_update().get(id=transaction_id, order=order)
        if attempt.status == "APPROVED" and order.status == "PAID":
            return attempt, order
        if attempt.status != "PENDING" or attempt.provider != MOCK_PROVIDER_ID:
            raise PaymentApprovalError()
        if order.status != "PENDING":
            raise PaymentStateError(order.get_status_display())
        attempt.status = "APPROVED"
        attempt.save(update_fields=["status", "updated_at"])
        order.status = "PAID"
        order.save(update_fields=["status", "updated_at"])
        _clear_purchased_cart_quantities(order)
        return attempt, order
