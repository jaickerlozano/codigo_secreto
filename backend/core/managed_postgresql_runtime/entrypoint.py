"""Process-environment setup for the runtime module entry point."""

from importlib import import_module


def configure_runtime_environment(environment):
    """Keep an explicit dotenv policy while defaulting to process-only inputs."""
    environment.setdefault("DJANGO_READ_DOTENV", "0")
    if environment["DJANGO_READ_DOTENV"] != "0":
        import_module("core.settings")
