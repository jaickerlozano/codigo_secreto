"""Offline URL rendering; this storage never accesses or changes assets."""

import re
from urllib.parse import quote

from django.conf import settings
from django.core.files.storage import Storage


class LocalReferenceStorage(Storage):
    preserve_delivery_url = True

    def url(self, name):
        namespace = getattr(settings, "LOCAL_CLOUDINARY_NAMESPACE", "")
        if not namespace:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_-]+", namespace):
            raise ValueError("Invalid public image namespace")
        if not name or any(part in {"", ".", ".."} for part in name.split("/")) or ":" in name:
            raise ValueError("Expected a relative image reference")
        return f"https://res.cloudinary.com/{namespace}/image/upload/{quote(name, safe='/')}"

    def _denied(self, *args, **kwargs):
        raise PermissionError("Local reference storage permits URL rendering only")

    open = save = delete = exists = _denied
