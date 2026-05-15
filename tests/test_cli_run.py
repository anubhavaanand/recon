from typer.testing import CliRunner
from types import SimpleNamespace
import pytest

from cli import main as cli_main


async def fake_search_all(query):
    # Return a small list of simple record-like objects (async to match real API)
    return [
        SimpleNamespace(id="US1", title="Quantum widget", dates={"filed": "2020-01-01"}, assignee="Acme"),
        SimpleNamespace(id="US2", title="Flux capacitor", dates={"filed": "2021-06-01"}, assignee="Wayne"),
    ]


class DummyDB:
    def __init__(self):
        self.saved = []

    def save_search_results(self, query, results):
        self.saved.append((query, results))

    def save_to_collection(self, record):
        # pretend to save
        pass

    def get_collection(self):
        return [r for (_, rs) in self.saved for r in rs]


def test_run_command_monkeypatched(monkeypatch):
    runner = CliRunner()

    # Patch search_all and CacheDatabase to deterministic fakes
    monkeypatch.setattr(cli_main, "search_all", fake_search_all)
    monkeypatch.setattr(cli_main, "CacheDatabase", lambda: DummyDB())

    result = runner.invoke(cli_main.app, ["run", "quantum"], catch_exceptions=True)

    # Ensure the command completed and printed expected content
    assert result.exit_code == 0
    assert "Running recon for: quantum" in result.output
    assert "Run Results (2 patents)" in result.output