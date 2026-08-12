import pytest
from django.core.cache import cache
from rest_framework import status

from apps.contact.models import ContactMessage


pytestmark = pytest.mark.django_db

CONTACT_URL = "/api/contact/"


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    """Start each test with a clean throttle window (suite convention)."""
    cache.clear()
    yield


def _payload(**overrides):
    data = {"name": "Cliente Prueba", "email": "cliente@example.com", "subject": "Consulta", "body": "Quisiera más información."}
    data.update(overrides)
    return data


def test_valid_message_is_persisted(api_client):
    response = api_client.post(CONTACT_URL, _payload(), format="json")

    assert response.status_code == status.HTTP_201_CREATED
    message = ContactMessage.objects.get(id=response.json()["id"])
    assert (message.name, message.email, message.subject, message.body) == ("Cliente Prueba", "cliente@example.com", "Consulta", "Quisiera más información.")
    assert message.status == ContactMessage.STATUS_NEW
    assert response.json()["status"] == ContactMessage.STATUS_NEW


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("email", "correo-invalido"), ("subject", ""), ("body", ""),
])
def test_invalid_message_returns_actionable_field_errors(api_client, field, value):
    """Field-level validation errors guide the customer and persist nothing."""
    response = api_client.post(CONTACT_URL, _payload(**{field: value}), format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.json() and response.json()[field]
    assert ContactMessage.objects.count() == 0


def test_contact_post_is_throttled(api_client, settings):
    """A public endpoint must be rate-limited to protect against spam."""
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["contact_message"] = "2/min"

    for _ in range(2):
        assert api_client.post(CONTACT_URL, _payload(), format="json").status_code == status.HTTP_201_CREATED
    assert api_client.post(CONTACT_URL, _payload(), format="json").status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert ContactMessage.objects.count() == 2


def test_contact_rejects_other_verbs(api_client):
    """Only POST is allowed on the public contact endpoint."""
    assert api_client.get(CONTACT_URL).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
