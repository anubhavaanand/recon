import os
import pytest
from tui.widgets.image_tab import detect_terminal_protocol, TerminalProtocol

def test_detect_kitty(monkeypatch):
    # New implementation detects Kitty via KITTY_WINDOW_ID env var
    monkeypatch.setenv("KITTY_WINDOW_ID", "1")
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    assert detect_terminal_protocol() == TerminalProtocol.KITTY

def test_detect_iterm2(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    assert detect_terminal_protocol() == TerminalProtocol.ITERM2

def test_detect_fallback(monkeypatch):
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.delenv("KITTY_WINDOW_ID", raising=False)
    monkeypatch.delenv("MLTERM", raising=False)
    assert detect_terminal_protocol() == TerminalProtocol.FALLBACK
