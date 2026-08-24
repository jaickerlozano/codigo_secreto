import re


CHILEAN_MOBILE_PHONE_MESSAGE = (
    "Ingresa un teléfono móvil chileno válido (ej. 9 1234 5678)."
)


def normalize_chilean_mobile_phone(value):
    """Return the canonical Chilean mobile number, or raise ValueError."""
    if not isinstance(value, str):
        raise ValueError(CHILEAN_MOBILE_PHONE_MESSAGE)

    compact = re.sub(r"\s+", "", value)
    if compact.startswith("+56"):
        compact = compact[3:]

    if not re.fullmatch(r"9\d{8}", compact):
        raise ValueError(CHILEAN_MOBILE_PHONE_MESSAGE)

    return f"+56 {compact[0]} {compact[1:5]} {compact[5:]}"
