---
name: agent-tui-development
description: Use when an AI agent needs to write, design, visually verify, or debug terminal UI apps (Textual/Python or similar TUI frameworks). Covers headless driving, rendered-frame capture, visual iteration loops, and framework-specific pitfalls. Trigger on "TUI", "Textual", "terminal UI", "pilot testing", "headless UI debug".
---

# Agent-Driven TUI Development

How an AI agent writes, designs, verifies, and debugs terminal UIs — without a human watching a screen.

## Core Loop

```
1. BUILD    edit widgets/CSS/handlers
2. DRIVE    boot app headless via run_test() pilot
3. CAPTURE  export_screenshot() per UI state → SVG + extracted text
4. READ     parse frames; compare against intended layout
5. FIX      patch CSS/logic from what frames actually show
6. VERIFY   re-run captures + test suite
```

Never claim a UI "works" without reading a captured frame. Never trust code inspection alone — borders eat rows, markup fails silently, handlers crash on real input paths.

## 1. Headless Driving (Textual)

```python
import asyncio
from tui.app import ReconApp   # your App subclass

async def main():
    app = ReconApp()
    async with app.run_test(size=(120, 36)) as pilot:
        await pilot.pause(0.4)          # let mount settle
        await pilot.press("b","a","t")  # keystrokes
        await pilot.press("enter")
        await pilot.pause(6.0)          # wait for async workers/timeouts
        svg = app.export_screenshot()   # returns SVG string of live frame
asyncio.run(main())
```

- `size=` controls the virtual terminal — capture multiple sizes to verify responsive breakpoints.
- `app.screen` tells you which Screen is active.
- Focus widgets directly (`widget.focus()`) instead of guessing tab order.
- `@work(exclusive=True)` workers need real `pause()` time; network timeouts define your settle delay.

## 2. Frame Capture & Agent-Readable Extraction

```python
import html, re

def svg_to_lines(svg: str) -> list[str]:
    rows = {}
    for m in re.finditer(r'<text[^>]*? y="([\d.]+)"[^>]*>(.*?)</text>', svg):
        y, content = m.group(1), m.group(2)
        clean = html.unescape(re.sub(r"<[^>]+>", "", content)).replace("\u00a0", " ")
        if clean.strip():
            rows.setdefault(y, []).append(clean)
    return ["".join(rows[y]).rstrip() for y in sorted(rows, key=float)]
```

Snapshot EVERY state: first-run, empty, loading(spinner mid-frame), results, error, each overlay open/closed. Save both `.svg` (visual ground truth) and `.txt` (grep/read).

Extraction artifacts to ignore: SVG `<title>` duplicates app TITLE; adjacent same-row runs concatenate (spacing exists in real render).

## 3. Real Bugs This Method Catches (seen in RECON)

| Class | Example |
|---|---|
| Env-dependent tests | detection test passed off-Kitty, failed in Kitty (`KITTY_WINDOW_ID` leak) |
| Flaky perf asserts | wall-clock <100ms under CI load → warmup + best-of-N |
| Silent CSS failures | invalid TCSS kills whole stylesheet at mount → every widget unstyled while tests still pass |
| Wrong-boundary mocks | `patch("mod.f")` then calling pre-imported local ref hits real network |
| Callback misuse | `call_after_refresh(self.method())` invokes coroutine immediately → TypeError only when user triggers it |
| Stale persistence | junk cached in legacy DB path survives cache-clear of the new path |

## 4. Textual TCSS Pitfalls (v8.x)

- **One property per `transition:`** — `transition: background 120ms, color 120ms;` is a PARSE ERROR that nukes the entire stylesheet. Use one property; pick the higher-impact one.
- **Easing names use underscores**: `in_out_cubic`, `out_cubic`, `linear` — not `ease-out`.
- **Borders add height** (box model): `height: 1` + `border-bottom` leaves ZERO content rows → text vanishes. Use `height: auto` when adding borders to single-line bars.
- **`.hidden {display:none}` can't transition** — animate opacity programmatically on reveal instead:
  ```python
  widget.remove_class("hidden")
  widget.styles.opacity = 0.0
  widget.styles.animate("opacity", 1.0, duration=0.14)
  ```
- Rich markup (`[bold cyan]▸ Info[/]`) is safe inside `Static.update()`.
- No automatic narrow/wide size classes on Screen — implement breakpoints via `on_resize` adding classes and key CSS off them.

## 5. Design System Discipline (k9s/ncspot/Hermes style)

1. Minimal chrome: no heavy ASCII boxes — CSS `border: round $border` on containers.
2. Status bar bottom shows active shortcuts (Hermes signature).
3. Animated spinner (braille frames ⠋⠙⠹…) during any >100ms op; MUST stop on success, empty, AND error paths.
4. Empty states teach: wordmark + top-3 keys + source list, never blank panes.
5. Subtle motion only: ≤150ms fades/transitions; respect reduced-motion users by keeping durations short.
6. ERR voice: dry, prefixed, actionable — verified frame-by-frame.

## 6. Verification Gate

Before declaring done:
```bash
pytest tests/ -q                      # logic green
python tui_debug.py                   # frames captured for all states
grep -i "traceback\|unhandled" logs   # silent crashes
```
Read the .txt frames yourself. If you cannot see it render, you cannot say it renders.
