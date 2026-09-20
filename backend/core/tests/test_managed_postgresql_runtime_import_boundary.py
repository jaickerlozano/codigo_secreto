"""Import-boundary contracts for managed PostgreSQL runtime commands."""

import subprocess
import sys

from core.managed_postgresql_runtime import cli


def test_validate_cli_contract_remains_available():
    arguments = cli.build_parser().parse_args(["validate", "--result", "result.json"])

    assert arguments.command == "validate"
    assert arguments.ack_disposable is False
    assert arguments.result == "result.json"


def test_runner_import_does_not_load_cli_command_handling():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import core.managed_postgresql_runtime.runner; print('core.managed_postgresql_runtime.cli' in sys.modules)",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "False\n"
