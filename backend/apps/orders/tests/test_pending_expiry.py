from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command, CommandError
from django.utils import timezone

from apps.orders.models import Order, NotificationDelivery
from apps.products.models import InventoryReservation, StockMovement
from apps.products.services import available_stock_for_product
from .test_pending_recovery import create_pending

pytestmark = pytest.mark.django_db


def due(order):
    InventoryReservation.objects.filter(order_id=order.id).update(expires_at=timezone.now() - timezone.timedelta(seconds=1))


def test_command_quiet_idempotent_and_no_physical_stock(api_client, product_factory, comuna_factory):
    order = create_pending(api_client, product_factory, comuna_factory)
    product = order.items.get().product
    before_stock = product.current_stock
    before_movements = StockMovement.objects.count()
    due(order)
    assert available_stock_for_product(product) == before_stock
    with patch('apps.orders.notifications.send_mail') as send:
        for _ in range(2):
            call_command('expire_pending_orders', stdout=StringIO())
    order.refresh_from_db()
    reservation = InventoryReservation.objects.get(order_id=order.id)
    product.refresh_from_db()
    assert (order.status, order.cancellation_reason) == ('CANCELLED', 'EXPIRED')
    assert (reservation.status, reservation.release_reason) == ('RELEASED', 'EXPIRED')
    assert product.current_stock == before_stock and StockMovement.objects.count() == before_movements
    assert not NotificationDelivery.objects.filter(event='cancelled').exists()
    send.assert_not_called()


def test_command_safe_batches_and_legacy_paid_skips(api_client, product_factory, comuna_factory, order_factory):
    orders = []
    for _ in range(4):
        api_client.cookies.clear()
        order = create_pending(api_client, product_factory, comuna_factory)
        due(order)
        orders.append(order)
    orders[0].status = 'PAID'
    orders[0].save()
    legacy = order_factory()
    call_command('expire_pending_orders', batch_size=1, stdout=StringIO())
    for order in orders:
        order.refresh_from_db()
    legacy.refresh_from_db()
    assert orders[0].status == 'PAID' and legacy.status == 'PENDING'
    assert all(order.cancellation_reason == 'EXPIRED' for order in orders[1:])
    assert InventoryReservation.objects.get(order_id=orders[0].id).status == 'ACTIVE'


@pytest.mark.parametrize('mutation', ['future', 'committed', 'cancelled_release', 'empty_lines'])
def test_expiry_skips_inconsistent_or_not_due(api_client, product_factory, comuna_factory, mutation):
    order = create_pending(api_client, product_factory, comuna_factory)
    reservation = InventoryReservation.objects.get(order_id=order.id)
    if mutation != 'future':
        due(order)
    if mutation == 'committed':
        reservation.status = 'COMMITTED'
        reservation.transitioned_at = timezone.now()
        reservation.save(update_fields=['status', 'transitioned_at'])
    if mutation == 'cancelled_release':
        reservation.status, reservation.release_reason = 'RELEASED', 'CANCELLED'
        reservation.transitioned_at = timezone.now()
        reservation.save(update_fields=['status', 'release_reason', 'transitioned_at'])
    if mutation == 'empty_lines':
        # Mismatch, not deletion: legacy inconsistent quantity must be left untouched.
        reservation.lines.update(quantity=99)
    call_command('expire_pending_orders', stdout=StringIO())
    order.refresh_from_db()
    assert order.status == 'PENDING' and order.cancellation_reason == ''


@pytest.mark.parametrize('operation', ['replay', 'initiate', 'approve'])
def test_stale_mutation_guard_commits_quiet_expiry(api_client, product_factory, comuna_factory, settings, operation):
    from .test_idempotent_checkout import _guest_payload
    settings.DEBUG = True
    settings.PAYMENT_PROVIDER = 'mock'
    order = create_pending(api_client, product_factory, comuna_factory)
    attempt = api_client.post('/api/payments/initiate/', {'order_id': order.id}, format='json')
    assert attempt.status_code == 200
    due(order)
    if operation == 'replay':
        payload = _guest_payload(order.items.get().product, order.comuna)
        response = api_client.post('/api/orders/', payload, format='json')
    elif operation == 'initiate':
        response = api_client.post('/api/payments/initiate/', {'order_id': order.id}, format='json')
    else:
        from apps.payments.models import Transaction
        transaction = Transaction.objects.get(order_id=order.id)
        response = api_client.post(f'/api/payments/{transaction.id}/mock-approve/', {}, format='json')
    assert response.status_code == (409 if operation == 'replay' else 400)
    order.refresh_from_db()
    assert (order.status, order.cancellation_reason) == ('CANCELLED', 'EXPIRED')
    assert InventoryReservation.objects.get(order_id=order.id).release_reason == 'EXPIRED'
    assert not NotificationDelivery.objects.filter(order=order, event='cancelled').exists()
    assert Order.objects.count() == 1


def test_unauthorized_payment_does_not_expire(api_client, product_factory, comuna_factory):
    from rest_framework.test import APIClient
    order = create_pending(api_client, product_factory, comuna_factory)
    due(order)
    response = APIClient().post('/api/payments/initiate/', {'order_id': order.id}, format='json')
    assert response.status_code == 404
    order.refresh_from_db()
    assert order.status == 'PENDING'
    assert InventoryReservation.objects.get(order_id=order.id).status == 'ACTIVE'


@pytest.mark.parametrize('options', [{'batch_size': 0}, {'interval': 0}])
def test_invalid_command_options(options):
    with pytest.raises(CommandError):
        call_command('expire_pending_orders', **options)


def test_watch_is_opt_in_foreground_and_interruptible():
    with patch('apps.orders.management.commands.expire_pending_orders.expire_pending_batch', return_value=0) as batch:
        with patch('apps.orders.management.commands.expire_pending_orders.time.sleep', side_effect=KeyboardInterrupt) as sleep:
            output = StringIO()
            call_command('expire_pending_orders', watch=True, interval=2, batch_size=3, stdout=output)
    batch.assert_called_once_with(batch_size=3)
    sleep.assert_called_once_with(2)
    assert 'stopped' in output.getvalue()


def test_paid_race_between_selection_and_lock_is_skipped(api_client, product_factory, comuna_factory):
    from apps.orders.services import due_reservation_order_ids
    order = create_pending(api_client, product_factory, comuna_factory)
    due(order)
    def selected(**kwargs):
        ids = due_reservation_order_ids(**kwargs)
        if ids:
            Order.objects.filter(pk=order.pk).update(status='PAID')
        return ids
    with patch('apps.orders.services.due_reservation_order_ids', side_effect=selected):
        call_command('expire_pending_orders', stdout=StringIO())
    order.refresh_from_db()
    assert (order.status, order.cancellation_reason) == ('PAID', '')
    assert InventoryReservation.objects.get(order_id=order.id).status == 'ACTIVE'
