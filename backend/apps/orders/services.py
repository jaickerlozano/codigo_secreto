import hmac
import json
from dataclasses import dataclass

from django.core import signing
from django.utils import timezone

from apps.orders.models import Order
from apps.products.services import ProductSnapshotResolutionError, resolve_product_price_snapshot
from apps.shipping.services import ShippingSnapshotResolutionError, resolve_comuna_shipping_snapshot


GUEST_ACCESS_COOKIE_NAME = "guest_order_access"
GUEST_ACCESS_COOKIE_MAX_AGE = 60 * 60
GUEST_ACCESS_COOKIE_SALT = "orders.guest-access"
GUEST_QUOTE_REVISION_SALT = "orders.guest-quote"
GUEST_QUOTE_REVISION_MAX_AGE = 15 * 60
GUEST_QUOTE_VERSION = "gq1"
GUEST_QUOTE_MAX_ITEMS = 50


class GuestQuoteValidationError(ValueError):
    """Raised when guest quote input cannot be priced authoritatively."""


class GuestQuoteRevisionStale(ValueError):
    """Raised when a guest confirms anything other than the current quote."""

    def __init__(self, quote):
        super().__init__("The confirmed quote is no longer current.")
        self.quote = quote


@dataclass(frozen=True, slots=True)
class GuestQuoteLine:
    product_id: int; product_name: str; quantity: int; unit_price: int; line_total: int


@dataclass(frozen=True, slots=True)
class GuestQuote:
    items: tuple[GuestQuoteLine, ...]; subtotal: int; shipping_cost: int | None
    total: int | None; comuna_id: int | None; revision: str

    def as_dict(self):
        data = {"items": [{key: getattr(line, key) for key in
            ("product_id", "product_name", "quantity", "unit_price", "line_total")} for line in self.items],
            "subtotal": self.subtotal, "revision": self.revision}
        if self.shipping_cost is not None: data.update(shipping_cost=self.shipping_cost, total=self.total)
        return data


def _canonical_quote_data(lines, *, comuna_id, subtotal, shipping_cost, total):
    return {"version": GUEST_QUOTE_VERSION,
        "items": [[line.product_id, line.quantity, line.unit_price, line.line_total] for line in lines],
        "comuna": comuna_id, "subtotal": subtotal, "shipping_cost": shipping_cost, "total": total}


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sign_guest_quote_revision(payload):
    """Sign canonical authoritative quote data without storing it."""
    return f"{GUEST_QUOTE_VERSION}.{signing.dumps(payload, salt=GUEST_QUOTE_REVISION_SALT, compress=True)}"


def load_guest_quote_revision(revision, *, max_age=GUEST_QUOTE_REVISION_MAX_AGE):
    if not isinstance(revision, str) or not revision.startswith(f"{GUEST_QUOTE_VERSION}."):
        raise signing.BadSignature("Unsupported quote revision.")
    payload = signing.loads(revision.split(".", 1)[1], salt=GUEST_QUOTE_REVISION_SALT, max_age=max_age)
    if not isinstance(payload, dict) or payload.get("version") != GUEST_QUOTE_VERSION:
        raise signing.BadSignature("Unsupported quote revision.")
    return payload


def _normalize_guest_items(guest_items):
    if not isinstance(guest_items, (list, tuple)) or not guest_items or len(guest_items) > GUEST_QUOTE_MAX_ITEMS:
        raise GuestQuoteValidationError("Invalid quote items.")
    normalized = []
    seen = set()
    for item in guest_items:
        if not isinstance(item, dict) or set(item) != {"product_id", "quantity"}:
            raise GuestQuoteValidationError("Invalid quote items.")
        product_id, quantity = item["product_id"], item["quantity"]
        if any((isinstance(value, bool) or not isinstance(value, int) or value <= 0) for value in (product_id, quantity)) or product_id in seen:
            raise GuestQuoteValidationError("Invalid quote items.")
        seen.add(product_id)
        normalized.append((product_id, quantity))
    return sorted(normalized)


def calculate_guest_quote(guest_items, comuna_selector=None, *, lock=False):
    """Calculate a side-effect-free quote from product and shipping snapshots."""
    items = _normalize_guest_items(guest_items)
    product_ids = [product_id for product_id, _ in items]
    try:
        products = resolve_product_price_snapshot(product_ids, for_update=lock)
        selector = {"comuna_id": comuna_selector} if isinstance(comuna_selector, int) and not isinstance(comuna_selector, bool) else comuna_selector
        if selector is None:
            shipping = None
        elif isinstance(selector, dict):
            shipping = resolve_comuna_shipping_snapshot(for_update=lock, **selector)
        else:
            raise GuestQuoteValidationError("Invalid quote destination.")
    except (ProductSnapshotResolutionError, ShippingSnapshotResolutionError, TypeError, ValueError) as error:
        raise GuestQuoteValidationError("Invalid quote input.") from error
    if shipping is None and comuna_selector is not None:
        raise GuestQuoteValidationError("Invalid quote destination.")

    lines = tuple(GuestQuoteLine(product_id, products[product_id].name, quantity,
        products[product_id].unit_price, products[product_id].unit_price * quantity) for product_id, quantity in items)
    subtotal = sum(line.line_total for line in lines)
    shipping_cost = shipping.shipping_cost if shipping else None
    total = subtotal + shipping_cost if shipping_cost is not None else None
    comuna_id = shipping.id if shipping else None
    revision = sign_guest_quote_revision(_canonical_quote_data(lines, comuna_id=comuna_id,
        subtotal=subtotal, shipping_cost=shipping_cost, total=total))
    return GuestQuote(lines, subtotal, shipping_cost, total, comuna_id, revision)


def quote_revision_matches(revision, quote):
    """Compare signed revision data using canonical JSON and constant-time equality."""
    try:
        payload = load_guest_quote_revision(revision)
    except signing.BadSignature:
        return False
    expected = _canonical_quote_data(quote.items, comuna_id=quote.comuna_id, subtotal=quote.subtotal,
        shipping_cost=quote.shipping_cost, total=quote.total)
    return hmac.compare_digest(_canonical_json(payload), _canonical_json(expected))


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
