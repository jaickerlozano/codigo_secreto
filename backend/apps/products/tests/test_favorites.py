import pytest
from django.core.cache import cache
from rest_framework import status

from apps.authentication.tests.factories import UserFactory
from apps.products.models import Favorite
from apps.products.services import merge_favorites


pytestmark = pytest.mark.django_db

FAVORITES_URL = "/api/favorites/"


@pytest.fixture(autouse=True)
def _reset_throttle_cache():
    """Start each test with a clean throttle window (suite convention)."""
    cache.clear()
    yield


def _merge(client, *product_ids):
    return client.post(FAVORITES_URL, {"product_ids": list(product_ids)}, format="json")


def test_anonymous_favorites_fail_closed(api_client, product_factory):
    """Guests have no server favorites: every verb fails closed without data."""
    product = product_factory()
    assert api_client.get(FAVORITES_URL).status_code == status.HTTP_401_UNAUTHORIZED
    assert _merge(api_client, product.id).status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.delete(f"{FAVORITES_URL}{product.id}/").status_code == status.HTTP_401_UNAUTHORIZED
    assert Favorite.objects.count() == 0


def test_merge_deduplicates_guest_ids_against_existing(
        authenticated_client, user, product_factory):
    """Overlapping guest ids merge privately without duplicate rows."""
    favorite_product = product_factory()
    merge_favorites(user=user, product_ids=[favorite_product.id])
    guest_a, guest_b = product_factory(), product_factory()

    response = _merge(authenticated_client, favorite_product.id, guest_a.id, guest_b.id, guest_b.id)

    assert response.status_code == status.HTTP_200_OK
    assert Favorite.objects.filter(user=user).count() == 3
    assert sorted(item["product"] for item in response.json()) == sorted([favorite_product.id, guest_a.id, guest_b.id])


def test_get_favorites_is_scoped_to_the_owner(authenticated_client, user, product_factory):
    """Another customer's resources never leak: each user sees only their own favorites."""
    mine, theirs = product_factory(), product_factory()
    merge_favorites(user=user, product_ids=[mine.id])
    other = UserFactory.create()
    merge_favorites(user=other, product_ids=[theirs.id])

    response = authenticated_client.get(FAVORITES_URL)

    assert response.status_code == status.HTTP_200_OK
    assert [item["product"] for item in response.json()] == [mine.id]
    assert Favorite.objects.count() == 2


def test_delete_removes_only_the_requested_favorite(
        authenticated_client, user, product_factory):
    """Deleting one favorite leaves the rest untouched."""
    keep, remove = product_factory(), product_factory()
    merge_favorites(user=user, product_ids=[keep.id, remove.id])

    response = authenticated_client.delete(f"{FAVORITES_URL}{remove.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert list(Favorite.objects.filter(user=user).values_list("product_id", flat=True)) == [keep.id]


def test_delete_unowned_or_unknown_favorite_is_masked_404(
        authenticated_client, user, product_factory):
    """Another user's favorite (or a missing product) never reveals existence."""
    unowned = product_factory()
    assert authenticated_client.delete(f"{FAVORITES_URL}{unowned.id}/").status_code == status.HTTP_404_NOT_FOUND
    assert authenticated_client.delete(f"{FAVORITES_URL}999999/").status_code == status.HTTP_404_NOT_FOUND
    assert Favorite.objects.count() == 0


def test_merge_ignores_stale_guest_ids_for_deleted_products(
        authenticated_client, user, product_factory):
    """A stale guest id (product deleted) never blocks the merge."""
    live = product_factory()
    response = _merge(authenticated_client, 999999, live.id)

    assert response.status_code == status.HTTP_200_OK
    assert list(Favorite.objects.filter(user=user).values_list("product_id", flat=True)) == [live.id]


def test_merge_rejects_non_list_payload(authenticated_client):
    """Malformed payloads fail with actionable field errors and create nothing."""
    response = authenticated_client.post(FAVORITES_URL, {"product_ids": "1,2,3"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "product_ids" in response.json()
    assert Favorite.objects.count() == 0
