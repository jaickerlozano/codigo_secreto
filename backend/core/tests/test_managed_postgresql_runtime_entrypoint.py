"""Process-environment contracts for the runtime module entry point."""


def test_configure_runtime_environment_preserves_explicit_dotenv_loading(monkeypatch):
    from core.managed_postgresql_runtime import entrypoint

    environment = {"DJANGO_READ_DOTENV": "1"}
    imports = []
    monkeypatch.setattr(entrypoint, "import_module", imports.append)

    entrypoint.configure_runtime_environment(environment)

    assert environment == {"DJANGO_READ_DOTENV": "1"}
    assert imports == ["core.settings"]


def test_configure_runtime_environment_disables_dotenv_loading_by_default(monkeypatch):
    from core.managed_postgresql_runtime import entrypoint

    environment = {}
    imports = []
    monkeypatch.setattr(entrypoint, "import_module", imports.append)

    entrypoint.configure_runtime_environment(environment)

    assert environment == {"DJANGO_READ_DOTENV": "0"}
    assert imports == []
