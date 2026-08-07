from django.core import signing
from django.utils import timezone

from apps.orders.models import Order


GUEST_ACCESS_COOKIE_NAME = "guest_order_access"
GUEST_ACCESS_COOKIE_MAX_AGE = 60 * 60
GUEST_ACCESS_COOKIE_SALT = "orders.guest-access"


def _verify_cookie(order, value):
    try:
        payload = signing.loads(value, salt=GUEST_ACCESS_COOKIE_SALT, max_age=GUEST_ACCESS_COOKIE_MAX_AGE)
    except signing.BadSignature:
        return False
    expires_at = order.guest_access_expires_at
    return bool(isinstance(payload, dict) and expires_at and not order.guest_access_revoked_at
        and payload.get("order_number") == order.order_number
        and payload.get("version") == order.guest_access_version
        and payload.get("expires_at") == int(expires_at.timestamp())
        and timezone.now() <= expires_at)


def issue_guest_access_cookie(order):
    if not order.guest_access_expires_at:
        return None
    return signing.dumps({"order_number": order.order_number,
        "version": order.guest_access_version,
        "expires_at": int(order.guest_access_expires_at.timestamp())}, salt=GUEST_ACCESS_COOKIE_SALT)


def authorize_order_access(order_number=None, *, order_id=None, user=None, capability=None, access_cookie=None):
    """Return the order if the caller is authorized, or None otherwise.

    This is the centralized authorization boundary for order disclosure and
    payment initiation. It enforces a masked failure policy: every unauthorized
    path returns ``None`` so callers cannot distinguish missing orders from
    rejected credentials.
    """
    try:
        order = Order.objects.get(id=order_id) if order_id is not None else Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return None

    if user and user.is_authenticated:
        if user.is_staff:
            return order
        if order.user and order.user == user:
            return order
        return None

    if capability and order.user is None and order.verify_guest_access(capability):
        return order
    if access_cookie and order.user is None and _verify_cookie(order, access_cookie):
        return order
    return None
