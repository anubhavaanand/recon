import subprocess
import sys


def test_cli_entrypoint_runs_help():
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Usage" in result.stdout
    assert "search" in result.stdout
    assert "export" in result.stdout
