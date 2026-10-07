"""Checkout attempt is a signed browser proof, never a public lookup key."""
import time
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.products.models import InventoryReservation
from .test_idempotent_checkout import _guest_payload

pytestmark = pytest.mark.django_db
CONTEXT = '/api/orders/checkout-context/'
COOKIE = 'checkout_attempt'


def prepare(client):
    response = client.post(CONTEXT)
    assert response.status_code == 204
    assert not response.content
    return response


@pytest.fixture
def prepared_context(request):
    """Existing checkout suites now perform the browser preparation step."""
    for name in ('authenticated_client', 'api_client'):
        if name in request.fixturenames:
            prepare(request.getfixturevalue(name))
            break


def test_context_is_stable_signed_http_only(api_client):
    first = prepare(api_client)
    cookie = first.cookies[COOKIE]
    assert cookie['httponly'] and cookie['samesite'] == 'Strict'
    assert cookie['path'] == '/' and int(cookie['max-age']) == 3600
    second = prepare(api_client)
    assert COOKIE not in second.cookies
    assert api_client.cookies[COOKIE].value == cookie.value


def test_context_requires_csrf():
    client = APIClient(enforce_csrf_checks=True)
    assert client.post(CONTEXT).status_code == 403
    from django.middleware.csrf import _get_new_csrf_string
    token = _get_new_csrf_string()
    client.cookies['csrftoken'] = token
    assert client.post(CONTEXT, HTTP_X_CSRFTOKEN=token).status_code == 204


def test_dropped_response_retry_restores_access_without_rotation(api_client, product_factory, comuna_factory):
    prepare(api_client)
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    first = api_client.post('/api/orders/', payload, format='json')
    assert first.status_code == 201
    assert first.json()['guest_access']['token']
    # Simulate another connection/reload retaining only the preparation cookie.
    retry_client = APIClient()
    retry_client.cookies[COOKIE] = api_client.cookies[COOKIE].value
    retry = retry_client.post('/api/orders/', payload, format='json')
    assert retry.status_code == 201
    assert retry.json()['id'] == first.json()['id']
    assert retry.json()['guest_access'] is None
    assert 'guest_order_access' in retry.cookies
    order = Order.objects.get()
    assert order.guest_access_version == 1
    assert order.verify_guest_access(first.json()['guest_access']['token'])
    assert InventoryReservation.objects.count() == 1


@pytest.mark.parametrize('field,value', [
    ('guest_name', 'Changed'), ('guest_email', 'different@example.com'),
    ('phone', '+56987654321'), ('shipping_address', 'Other street'),
    ('apartment_office', '8'), ('payment_method', 'flow'),
    ('guest_items', None), ('comuna', None), ('delivery_kind', 'special'),
    ('requested_dispatch_date', '2000-01-01'),
])
def test_full_intent_conflicts(api_client, product_factory, comuna_factory, field, value):
    prepare(api_client)
    product = product_factory(current_stock=10)
    payload = _guest_payload(product, comuna_factory())
    assert api_client.post('/api/orders/', payload, format='json').status_code == 201
    if field == 'guest_items':
        value = [{'product_id': product.id, 'quantity': 3}]
    if field == 'comuna':
        value = comuna_factory().id
    response = api_client.post('/api/orders/', {**payload, field: value}, format='json')
    assert response.status_code == 409
    assert response.json()['code'] == 'checkout_key_conflict'
    assert Order.objects.count() == InventoryReservation.objects.count() == 1


def test_header_guest_replay_requires_private_proof(api_client, product_factory, comuna_factory):
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    first = api_client.post('/api/orders/', payload, format='json', HTTP_IDEMPOTENCY_KEY='public-key')
    assert first.status_code == 201
    stranger = APIClient()
    response = stranger.post('/api/orders/', payload, format='json', HTTP_IDEMPOTENCY_KEY='public-key')
    assert response.status_code == 409
    assert 'guest_order_access' not in response.cookies
    assert Order.objects.get().guest_access_version == 1
    retry = api_client.post('/api/orders/', payload, format='json', HTTP_IDEMPOTENCY_KEY='public-key')
    assert retry.status_code == 201 and retry.json()['guest_access'] is None


@pytest.mark.parametrize('invalid', ['missing', 'tampered', 'expired', 'foreign'])
def test_invalid_attempt_cannot_create(api_client, user, product_factory, comuna_factory, invalid):
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    if invalid != 'missing':
        prepare(api_client)
    if invalid == 'tampered':
        api_client.cookies[COOKIE] = api_client.cookies[COOKIE].value + 'x'
    if invalid == 'foreign':
        api_client.force_authenticate(user=user)
    clock = patch('django.core.signing.time.time', return_value=time.time() + 3601) if invalid == 'expired' else patch('time.monotonic', wraps=time.monotonic)
    with clock:
        response = api_client.post('/api/orders/', payload, format='json')
    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_authenticated_attempt_not_reusable_by_other_owner(api_client, user, product_factory, comuna_factory, cart_factory, cart_item_factory):
    from apps.authentication.tests.factories import UserFactory
    from .test_idempotent_checkout import _auth_payload
    api_client.force_authenticate(user=user)
    cart = cart_factory(user=user)
    cart_item_factory(cart=cart, product=product_factory(current_stock=10), quantity=1)
    prepare(api_client)
    payload = _auth_payload(comuna_factory())
    assert api_client.post('/api/orders/', payload, format='json').status_code == 201
    other = UserFactory(is_staff=True)
    api_client.force_authenticate(user=other)
    assert api_client.post('/api/orders/', payload, format='json').status_code == 400
    assert Order.objects.count() == 1


def test_preparation_renews_terminal_attempt_but_not_pending(api_client, product_factory, comuna_factory):
    prepare(api_client)
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    assert api_client.post('/api/orders/', payload, format='json').status_code == 201
    first_cookie = api_client.cookies[COOKIE].value
    assert COOKIE not in prepare(api_client).cookies
    order = Order.objects.get()
    from apps.orders.services import cancel_pending_order
    cancel_pending_order(order_id=order.id)
    assert Order.objects.get().cancellation_reason == 'BUYER'
    assert COOKIE in prepare(api_client).cookies
    assert api_client.cookies[COOKIE].value != first_cookie
    assert api_client.post('/api/orders/', payload, format='json').status_code == 201
    assert Order.objects.count() == InventoryReservation.objects.count() == 2


def test_guest_header_replay_accepts_email_ticket(api_client, product_factory, comuna_factory):
    from apps.orders.services import issue_guest_email_access_ticket
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    assert api_client.post('/api/orders/', payload, format='json', HTTP_IDEMPOTENCY_KEY='ticket-retry').status_code == 201
    order = Order.objects.get()
    client = APIClient()
    response = client.post('/api/orders/', payload, format='json', HTTP_IDEMPOTENCY_KEY='ticket-retry',
        HTTP_X_ORDER_CAPABILITY=issue_guest_email_access_ticket(order))
    assert response.status_code == 201 and response.json()['guest_access'] is None
    assert 'guest_order_access' in response.cookies
    assert Order.objects.get().guest_access_version == 1


def test_authenticated_cookie_retry_freezes_contact_and_cart(api_client, user, product_factory, comuna_factory, cart_factory, cart_item_factory):
    from .test_idempotent_checkout import _auth_payload
    api_client.force_authenticate(user=user)
    item = cart_item_factory(cart=cart_factory(user=user), product=product_factory(current_stock=10), quantity=1)
    prepare(api_client)
    payload = _auth_payload(comuna_factory())
    first = api_client.post('/api/orders/', payload, format='json')
    assert first.status_code == 201
    client = APIClient()
    client.force_authenticate(user=user)
    client.cookies[COOKIE] = api_client.cookies[COOKIE].value
    retry = client.post('/api/orders/', payload, format='json')
    assert retry.status_code == 201 and retry.json()['id'] == first.json()['id']
    user.phone = '+56987654321'
    user.save()
    assert client.post('/api/orders/', payload, format='json').status_code == 409
    user.phone = Order.objects.get().phone
    user.save()
    item.quantity = 2
    item.save()
    assert client.post('/api/orders/', payload, format='json').status_code == 409
    assert Order.objects.count() == InventoryReservation.objects.count() == 1


def test_guest_race_fallback_requires_proof_and_full_contact(api_client, product_factory, comuna_factory):
    from django.db import transaction
    from apps.orders.services import _race_replay, _contact_intent, calculate_guest_quote, CheckoutKeyConflictError
    from apps.shipping.services import DeliverySnapshot
    prepare(api_client)
    payload = _guest_payload(product_factory(current_stock=10), comuna_factory())
    assert api_client.post('/api/orders/', payload, format='json').status_code == 201
    order = Order.objects.get()
    quote = calculate_guest_quote(payload['guest_items'], payload['comuna'])
    delivery = DeliverySnapshot(order.delivery_kind, order.requested_dispatch_date, order.carrier, order.shipping_cost)
    contact = _contact_intent(order.guest_name, order.phone, order.shipping_address, order.apartment_office, order.payment_method)
    with transaction.atomic():
        with pytest.raises(CheckoutKeyConflictError):
            _race_replay(order.checkout_key, quote, order.guest_email, delivery, contact, {})
        with pytest.raises(CheckoutKeyConflictError):
            _race_replay(order.checkout_key, quote, order.guest_email, delivery, ('different', *contact[1:]), {'attempt_key': order.checkout_key})
        replay = _race_replay(order.checkout_key, quote, order.guest_email, delivery, contact, {'attempt_key': order.checkout_key})
    assert replay.pk == order.pk and replay.guest_access_version == 1
    assert not hasattr(replay, '_guest_access_token')
