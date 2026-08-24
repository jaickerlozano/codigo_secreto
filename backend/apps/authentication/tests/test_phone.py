import pytest

from apps.authentication.phone import normalize_chilean_mobile_phone


@pytest.mark.parametrize(
    ("raw_phone", "normalized_phone"),
    [
        ("912345678", "+56 9 1234 5678"),
        ("+56912345678", "+56 9 1234 5678"),
        ("+56 9 1234 5678", "+56 9 1234 5678"),
    ],
)
def test_normalize_chilean_mobile_phone(raw_phone, normalized_phone):
    assert normalize_chilean_mobile_phone(raw_phone) == normalized_phone


@pytest.mark.parametrize("raw_phone", ["", "812345678", "+56 2 1234 5678", "phone"])
def test_normalize_chilean_mobile_phone_rejects_invalid_values(raw_phone):
    with pytest.raises(ValueError):
        normalize_chilean_mobile_phone(raw_phone)
