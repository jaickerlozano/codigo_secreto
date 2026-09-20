"""Outcome recording without altering pytest-django database lifecycle."""

from .pytest_plugin import pytest_collection_finish, pytest_runtest_makereport, pytest_sessionfinish
