from unittest.mock import patch

import pytest
from django.core import mail
from django.db import transaction
from django.utils import timezone

from apps.orders.models import NotificationDelivery, Order
from apps.orders.notifications import attempt_delivery, retry_delivery, schedule_delivery
from apps.orders.services import authorize_order_email_access, create_order
from apps.products.models import InventoryReservation
from .test_checkout_context import prepare
from .test_idempotent_checkout import _guest_payload

pytestmark = pytest.mark.django_db(transaction=True)


def created(client, product_factory, comuna_factory):
    prepare(client)
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    response = client.post('/api/orders/', payload, format='json')
    assert response.status_code == 201
    return Order.objects.get(pk=response.json()['id']), payload


def test_receipt_after_commit_private_and_replay_once(api_client, product_factory, comuna_factory):
    with transaction.atomic():
        order, payload = created(api_client, product_factory, comuna_factory)
        assert not mail.outbox
        receipt = NotificationDelivery.objects.get(order=order, event='pending_payment_receipt')
        assert receipt.status == 'PENDING'
        assert InventoryReservation.objects.get(order_id=order.id).status == 'ACTIVE'
    receipt.refresh_from_db()
    assert (receipt.status, receipt.attempts) == ('SENT', 1)
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [order.guest_email]
    assert '15 minutos' in message.body and 'vence' in message.body
    assert order.shipping_address not in message.body
    assert order.items.get().product_name not in message.body
    assert str(order.total) not in message.body
    ticket = message.body.split('#access=')[1].strip()
    assert authorize_order_email_access(order.order_number, ticket).id == order.id
    assert api_client.post('/api/orders/', payload, format='json').status_code == 201
    assert len(mail.outbox) == 1
    assert NotificationDelivery.objects.filter(order=order, event='pending_payment_receipt').count() == 1
    attempt_delivery(receipt.id, trigger='manual')
    assert len(mail.outbox) == 1


def test_rollback_discards_new_receipt(api_client, product_factory, comuna_factory):
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            created(api_client, product_factory, comuna_factory)
            raise RuntimeError('rollback')
    assert not Order.objects.exists() and not NotificationDelivery.objects.exists()
    assert not mail.outbox


@pytest.mark.parametrize('obsolete', ['paid', 'cancelled', 'deadline', 'revoked'])
@pytest.mark.parametrize('trigger', ['manual', 'automatic', 'initial'])
def test_obsolete_pending_receipt_truthfully_skipped(api_client, product_factory, comuna_factory, obsolete, trigger):
    with patch('apps.orders.notifications.send_mail', side_effect=RuntimeError('smtp unavailable')):
        order, _ = created(api_client, product_factory, comuna_factory)
    receipt = NotificationDelivery.objects.get(order=order, event='pending_payment_receipt')
    assert receipt.status == 'FAILED'
    if obsolete in {'paid', 'cancelled'}:
        order.status = obsolete.upper()
        order.save()
    elif obsolete == 'deadline':
        InventoryReservation.objects.filter(order_id=order.id).update(expires_at=timezone.now() - timezone.timedelta(seconds=1))
    else:
        order.revoke_guest_email_access()
    before = Order.objects.values().get(pk=order.id)
    if trigger == 'initial':
        receipt.status, receipt.attempts = 'PENDING', 0
        receipt.save()
    attempts = receipt.attempts
    with patch('apps.orders.notifications.send_mail') as send:
        attempt_delivery(receipt.id, trigger=trigger, now=receipt.next_retry_at)
        retry_delivery(receipt.id)
        schedule_delivery(order, 'pending_payment_receipt')
    send.assert_not_called()
    receipt.refresh_from_db()
    assert (receipt.status, receipt.sent_at, receipt.next_retry_at, receipt.attempts) == ('SKIPPED', None, None, attempts)
    assert Order.objects.values().get(pk=order.id) == before
    assert InventoryReservation.objects.get(order_id=order.id).status == 'ACTIVE'


def test_retry_live_receipt_and_ticket_error_redaction(api_client, product_factory, comuna_factory):
    with patch('apps.orders.notifications.send_mail', side_effect=RuntimeError('failed #access=opaque-ticket')):
        order, _ = created(api_client, product_factory, comuna_factory)
    receipt = NotificationDelivery.objects.get(order=order, event='pending_payment_receipt')
    assert receipt.status == 'FAILED' and receipt.last_error == 'Email delivery failed.'
    retry_delivery(receipt.id)
    receipt.refresh_from_db()
    assert receipt.status == 'SENT' and receipt.attempts == 2
    assert len(mail.outbox) == 1


def test_account_receipt_has_plain_link_and_missing_recipient_retry(api_client, user, cart_factory, cart_item_factory, product_factory, comuna_factory):
    from .test_idempotent_checkout import _auth_payload
    api_client.force_authenticate(user=user)
    cart_item_factory(cart=cart_factory(user=user), product=product_factory(current_stock=10), quantity=1)
    prepare(api_client)
    user.email = ''
    user.save()
    response = api_client.post('/api/orders/', _auth_payload(comuna_factory()), format='json')
    assert response.status_code == 201
    order = Order.objects.get()
    receipt = NotificationDelivery.objects.get(order=order, event='pending_payment_receipt')
    assert receipt.status == 'FAILED' and receipt.next_retry_at and not mail.outbox
    user.email = 'account@example.test'
    user.save()
    retry_delivery(receipt.id)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    assert f'/order/{order.order_number}' in mail.outbox[0].body
    assert '#access=' not in mail.outbox[0].body
