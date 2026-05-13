import subprocess
import sys


def test_python_module_entrypoint_runs_help():
    result = subprocess.run(
        [sys.executable, "-m", "recon", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Usage" in result.stdout
