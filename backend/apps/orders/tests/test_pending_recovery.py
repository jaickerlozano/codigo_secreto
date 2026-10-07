import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.orders.services import issue_guest_access_cookie
from apps.products.models import InventoryReservation
from .test_checkout_context import COOKIE, prepare
from .test_idempotent_checkout import _guest_payload

pytestmark = pytest.mark.django_db
URL = '/api/orders/pending/'


def create_pending(client, product_factory, comuna_factory):
    prepare(client)
    response = client.post('/api/orders/', _guest_payload(product_factory(current_stock=10), comuna_factory()), format='json')
    assert response.status_code == 201
    return Order.objects.get(pk=response.json()['id'])


@pytest.mark.parametrize('proof', ['attempt', 'cookie'])
def test_guest_discovery_restores_cookie_without_domain_writes(api_client, product_factory, comuna_factory, proof, django_assert_num_queries):
    order = create_pending(api_client, product_factory, comuna_factory)
    client = APIClient()
    name = COOKIE if proof == 'attempt' else 'guest_order_access'
    client.cookies[name] = api_client.cookies[name].value
    before_order = Order.objects.values().get(pk=order.pk)
    before_reservation = InventoryReservation.objects.values().get(order_id=order.id)
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json()['id'] == order.id and response.json()['guest_access'] is None
    assert response.json()['payment_expires_at']
    assert ('guest_order_access' in response.cookies) == (proof == 'attempt')
    assert Order.objects.values().get(pk=order.pk) == before_order
    assert InventoryReservation.objects.values().get(order_id=order.id) == before_reservation


@pytest.mark.parametrize('invalid', ['absent', 'tampered', 'revoked', 'rotated', 'expired', 'paid', 'reservation_due'])
def test_unverified_or_obsolete_guest_not_disclosed(api_client, product_factory, comuna_factory, invalid):
    order = create_pending(api_client, product_factory, comuna_factory)
    if invalid == 'absent':
        api_client.cookies.clear()
    if invalid == 'tampered':
        api_client.cookies.clear()
        api_client.cookies[COOKIE] = 'not-signed'
    if invalid == 'revoked':
        order.revoke_guest_access()
    if invalid == 'rotated':
        order.rotate_guest_access()
    if invalid == 'expired':
        order.guest_access_expires_at = timezone.now() - timezone.timedelta(seconds=1)
        order.save()
    if invalid == 'paid':
        order.status = 'PAID'
        order.save()
    if invalid == 'reservation_due':
        InventoryReservation.objects.filter(order_id=order.id).update(expires_at=timezone.now() - timezone.timedelta(seconds=1))
    response = api_client.get(URL, {'email': order.guest_email, 'order_number': order.order_number})
    assert response.status_code == 204 and not response.content
    assert 'guest_order_access' not in response.cookies
    assert InventoryReservation.objects.get(order_id=order.id).status == 'ACTIVE'


def test_account_discovery_enforces_owner_even_staff(api_client, order_factory, user):
    owned = order_factory(user=user)
    order_factory()
    api_client.force_authenticate(user=user)
    response = api_client.get(URL)
    assert response.status_code == 200 and response.json()['id'] == owned.id
    assert response.json()['payment_expires_at'] is None
    assert 'guest_order_access' not in response.cookies
    from apps.authentication.tests.factories import UserFactory
    api_client.force_authenticate(user=UserFactory(is_staff=True))
    assert api_client.get(URL).status_code == 204


def test_guest_cookie_cannot_disclose_to_foreign_account(api_client, product_factory, comuna_factory, user):
    order = create_pending(api_client, product_factory, comuna_factory)
    api_client.force_authenticate(user=user)
    assert api_client.get(URL).status_code == 204
    assert order.user_id is None


def test_recovered_cookie_can_initiate_payment(api_client, product_factory, comuna_factory, settings):
    settings.DEBUG = True
    settings.PAYMENT_PROVIDER = 'mock'
    order = create_pending(api_client, product_factory, comuna_factory)
    client = APIClient()
    client.cookies[COOKIE] = api_client.cookies[COOKIE].value
    assert client.get(URL).status_code == 200
    response = client.post('/api/payments/initiate/', {'order_id': order.id}, format='json')
    assert response.status_code == 200


def test_list_deadlines_are_batched(api_client, order_factory, user, django_assert_num_queries):
    for _ in range(3):
        order_factory(user=user)
    api_client.force_authenticate(user=user)
    # Related order data and deadlines must not grow with each order.
    with django_assert_num_queries(4):
        response = api_client.get('/api/orders/')
    assert response.status_code == 200
    assert all(row['payment_expires_at'] is None for row in response.json()['results'])


def test_expired_attempt_without_access_cookie_is_masked(api_client, product_factory, comuna_factory):
    import time
    from unittest.mock import patch
    create_pending(api_client, product_factory, comuna_factory)
    client = APIClient()
    client.cookies[COOKIE] = api_client.cookies[COOKIE].value
    with patch('django.core.signing.time.time', return_value=time.time() + 3601):
        response = client.get(URL)
    assert response.status_code == 204 and not response.cookies
