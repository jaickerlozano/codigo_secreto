"""Parse only approved local database keys, without shell expansion."""

import shlex

from django.core.exceptions import ImproperlyConfigured


def local_database(path):
    keys = {"POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"}
    values = {}
    try:
        for line in path.read_text().splitlines():
            key, separator, raw = line.partition("=")
            if separator and key.strip() in keys:
                tokens = shlex.split(raw, comments=True)
                if len(tokens) != 1 or not tokens[0] or key.strip() in values:
                    raise ValueError
                values[key.strip()] = tokens[0]
        if values.keys() != keys:
            raise ValueError
    except (OSError, ValueError):
        raise ImproperlyConfigured("Invalid local PostgreSQL configuration") from None
    return {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "127.0.0.1", "PORT": "5432",
        "NAME": values["POSTGRES_DB"], "USER": values["POSTGRES_USER"],
        "PASSWORD": values["POSTGRES_PASSWORD"],
        "OPTIONS": {"options": "-c default_transaction_read_only=on", "connect_timeout": 5},
    }
