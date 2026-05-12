import os
import pytest
from tui.widgets.image_tab import detect_terminal_protocol, TerminalProtocol

def test_detect_kitty(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-kitty")
    assert detect_terminal_protocol() == TerminalProtocol.KITTY

def test_detect_iterm2(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    assert detect_terminal_protocol() == TerminalProtocol.ITERM2

def test_detect_fallback(monkeypatch):
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    # Could add sixel detection test, but let's test fallback as default for unknown
    assert detect_terminal_protocol() == TerminalProtocol.FALLBACK
