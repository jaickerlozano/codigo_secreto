from apps.orders.models import Order


def authorize_order_access(order_number, *, user=None, capability=None):
    """Return the order if the caller is authorized, or None otherwise.

    This is the centralized authorization boundary for order disclosure and
    payment initiation. It enforces a masked failure policy: every unauthorized
    path returns ``None`` so callers cannot distinguish missing orders from
    rejected credentials.

    Authorization precedence:
    1. Staff users can access any order.
    2. Authenticated owners can access their own orders.
    3. Guest orders (``user`` is None) can be accessed with a valid,
       unexpired, non-revoked capability token.

    Args:
        order_number: Public order number (e.g., ``CS-XXXXXXX``).
        user: Optional authenticated user making the request.
        capability: Optional raw guest capability token.

    Returns:
        ``Order`` instance if authorized, otherwise ``None``.
    """
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return None

    if user and user.is_authenticated:
        if user.is_staff:
            return order
        if order.user and order.user == user:
            return order
        # Authenticated non-owner: do not fall through to capability check.
        return None

    if capability and order.user is None and order.verify_guest_access(capability):
        return order

    return None
