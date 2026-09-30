"""Offline media storage for the explicit local profile."""

from django.core.files.storage import Storage


class LocalReferenceStorage(Storage):
    preserve_delivery_url = True

    def url(self, name):
        """Leave persisted remote references unresolved without making requests."""
        return None

    def _denied(self, *args, **kwargs):
        raise PermissionError("Local media storage is offline")

    open = save = delete = exists = _denied
