import ast
import inspect

import pytest
from django.utils import timezone

from apps.orders import services as order_services
from apps.orders.models import Order
from apps.orders.services import authorize_order_access
from apps.payments import services as payment_services

pytestmark = pytest.mark.django_db


_INVENTORY_PERSISTENCE_MODELS = frozenset(
    {"InventoryReservation", "InventoryReservationLine", "StockMovement"}
)
_PERSISTENCE_WRITE_METHODS = frozenset(
    {"create", "bulk_create", "bulk_update", "get_or_create", "update", "update_or_create"}
)


def _inventory_persistence_operations(module):
    tree = ast.parse(inspect.getsource(module))
    imports = []
    writes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "apps.products.models":
            imports.extend(alias.name for alias in node.names if alias.name in _INVENTORY_PERSISTENCE_MODELS)
            continue
        if isinstance(node, ast.Import) and any(
            alias.name == "apps.products.models" for alias in node.names
        ):
            imports.append("apps.products.models")
            continue
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue

        manager = node.func.value
        if not (
            node.func.attr in _PERSISTENCE_WRITE_METHODS
            and isinstance(manager, ast.Attribute)
            and manager.attr == "objects"
            and isinstance(manager.value, ast.Name)
            and manager.value.id in _INVENTORY_PERSISTENCE_MODELS
        ):
            continue
        writes.append(f"{manager.value.id}.objects.{node.func.attr}")

    return {"imports": sorted(imports), "writes": sorted(writes)}


@pytest.mark.parametrize(
    ("module_name", "module"),
    [
        ("apps.orders.services", order_services),
        ("apps.payments.services", payment_services),
    ],
)
def test_order_and_payment_services_do_not_write_inventory_persistence_directly(
    module_name, module
):
    assert _inventory_persistence_operations(module) == {
        "imports": [],
        "writes": [],
    }, module_name


def test_authorize_owner_returns_order(order_factory, user):
    order = order_factory(user=user)
    result = authorize_order_access(order.order_number, user=user)
    assert isinstance(result, Order)
    assert result.id == order.id


def test_authorize_staff_returns_any_order(order_factory, staff_user):
    order = order_factory()
    assert authorize_order_access(order.order_number, user=staff_user).id == order.id


def test_authorize_valid_capability_returns_order(order_factory):
    order = order_factory(user=None)
    raw = order.issue_guest_access()
    assert authorize_order_access(order.order_number, capability=raw).id == order.id


def test_authorize_missing_order_returns_none():
    assert authorize_order_access("CS-NONEXISTENT", user=None) is None


def test_authorize_no_user_no_capability_returns_none(order_factory):
    order = order_factory(user=None)
    assert authorize_order_access(order.order_number, user=None) is None


def test_authorize_authenticated_non_owner_returns_none(order_factory, user):
    order = order_factory()
    assert authorize_order_access(order.order_number, user=user) is None


def test_authorize_wrong_capability_returns_none(order_factory):
    order = order_factory(user=None)
    order.issue_guest_access()
    assert authorize_order_access(order.order_number, capability="wrong-token") is None


def test_authorize_expired_capability_returns_none(order_factory):
    order = order_factory(user=None)
    raw = order.issue_guest_access()
    order.guest_access_issued_at = timezone.now() - timezone.timedelta(days=91)
    order.guest_access_expires_at = order.guest_access_issued_at + timezone.timedelta(days=90)
    order.save()
    assert authorize_order_access(order.order_number, capability=raw) is None


def test_authorize_revoked_capability_returns_none(order_factory):
    order = order_factory(user=None)
    raw = order.issue_guest_access()
    order.revoke_guest_access()
    assert authorize_order_access(order.order_number, capability=raw) is None


def test_authorize_capability_on_owned_order_ignored(order_factory, user):
    order = order_factory(user=user)
    raw = order.issue_guest_access()
    assert authorize_order_access(order.order_number, capability=raw, user=None) is None
