"""Random, signed, actor-bound browser proof for one checkout attempt."""
import secrets

from django.conf import settings
from django.core import signing

COOKIE_NAME = 'checkout_attempt'
MAX_AGE = 3600
SALT = 'orders.checkout-attempt.v1'


def _actor(user):
    return f'user:{user.pk}' if user and user.is_authenticated else 'guest'


def load_attempt(value, user):
    if not value:
        return None
    try:
        payload = signing.loads(value, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature:
        return None
    if not isinstance(payload, dict) or set(payload) != {'key', 'actor'}:
        return None
    key = payload['key']
    if payload['actor'] != _actor(user) or not isinstance(key, str) or len(key) != 43:
        return None
    return key


def new_attempt(user):
    return signing.dumps({'key': secrets.token_urlsafe(32), 'actor': _actor(user)}, salt=SALT)


def set_attempt_cookie(response, value):
    response.set_cookie(COOKIE_NAME, value, max_age=MAX_AGE, httponly=True,
        secure=getattr(settings, 'GUEST_ORDER_ACCESS_COOKIE_SECURE',
                       getattr(settings, 'SIMPLE_JWT', {}).get('JWT_COOKIE_SECURE', False)),
        samesite='Strict', path='/')
