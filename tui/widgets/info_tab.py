from rich.markup import escape
from textual.widgets import Static

from core.models import PatentRecord
from core.scoring import calculate_signal_score


def _render_score_bar(score: int, width: int = 24) -> str:
    """Score-graded unicode progress bar."""
    filled = int((score / 100) * width)
    if score >= 60:
        color = "#9ece6a"
    elif score >= 40:
        color = "#e0af68"
    elif score > 0:
        color = "#7aa2f7"
    else:
        color = "#3b4261"
    bar = f"[bold {color}]" + "█" * filled + "[/]"
    return bar + "[dim]" + "░" * (width - filled) + f"[/] {score}/100"


def _render_signal_dots(refs) -> str:
    """Return signal dot summary: NIH ●●●●● SEC ●●●○○"""
    source_map = {}
    for ref in refs:
        src = ref.source.upper()[:3]
        conf = ref.metadata.get("confidence", 100.0)
        source_map[src] = conf

    if not source_map:
        return "No signals detected."

    parts = []
    for src, conf in source_map.items():
        filled = min(5, int(conf / 20))
        if filled >= 4:
            color = "#9ece6a"
        elif filled >= 2:
            color = "#e0af68"
        else:
            color = "#7aa2f7"
        dots = f"[{color}]" + "●" * filled + "[dim]" + "○" * (5 - filled) + "[/]"
        parts.append(f"[bold]{src}[/]{dots}")
    return "  ".join(parts)


def _render_status_pill(status: str) -> str:
    """Return colored status pill."""
    if not status:
        return "[dim][?][/]"

    import re

    # Strip bullet points, question marks, brackets, and extra spaces
    s = re.sub(r"[●•\?\[\]]", "", status).strip().upper()
    if not s or s in ("UNKNOWN", ""):
        return "[dim][?][/]"

    if s in ("ACTIVE", "GRANTED"):
        return f"[#9ece6a]●[/] [bold #9ece6a]{s}[/]"
    elif s == "EXPIRED":
        return f"[dim]● EXPIRED[/] [dim]→ public domain[/]"
    elif s == "ABANDONED":
        return f"[#f7768e]●[/] [#f7768e]ABANDONED[/] [dim]→ free to use[/]"
    elif s == "PENDING":
        return f"[#e0af68]○[/] [#e0af68]PENDING[/]"
    return f"[dim]○ {s}[/]"


def _rule(title: str = "", width: int = 46) -> str:
    if title:
        pad = max(0, width - len(title) - 5)
        return f"[dim]─[/] [bold $primary]{title}[/] [dim]" + "─" * pad + "[/]"
    return "[dim]" + "─" * width + "[/]"


class InfoTab(Static):
    """Info tab: sectioned patent dossier with graded score and signals."""

    _EMPTY_STATE = (
        "\n"
        "[bold #7aa2f7]██╗  ██╗███████╗ ██████╗ ██████╗ ███╗   ██╗[/]\n"
        "[bold #7aa2f7]██║ ██╔╝██╔════╝██╔════╝██╔═══██╗████╗  ██║[/]\n"
        "[bold #7aa2f7]█████╔╝ █████╗  ██║     ██║   ██║██╔██╗ ██║[/]\n"
        "[bold #7aa2f7]██╔═██╗ ██╔══╝  ██║     ██║   ██║██║╚██╗██║[/]\n"
        "[bold #7aa2f7]██║  ██╗███████╗╚██████╗╚██████╔╝██║ ╚████║[/]\n"
        "[bold #7aa2f7]╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝[/]\n\n"
        "[dim]terminal-native patent intelligence[/]\n\n"
        "[cyan]→[/] Type a query above and press [bold]Enter[/]\n"
        "[cyan]→[/] [bold]↑↓[/] navigate results  ·  [bold]h/l[/] switch tabs\n"
        "[cyan]→[/] Press [bold]?[/] for all shortcuts\n\n"
        "[dim]USPTO · EPO · WIPO · Google Patents · Lens · PatSnap[/]"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_loaded = False

    def on_mount(self) -> None:
        if not self.is_loaded:
            self.update(self._EMPTY_STATE)

    def update_record(self, record: PatentRecord | None) -> None:
        try:
            self.is_loaded = True
            if not record:
                self.update(
                    "[dim]No patent selected.[/]  [cyan]↑↓[/] [dim]to navigate.[/]"
                )
                return

            title = escape(record.title or "[?]")
            assignee = escape(record.assignee or "[?]")
            status = _render_status_pill(record.status)
            abstract = escape(record.abstract or "[?]")
            date_f = escape(str(record.dates.get("filed", "[?]")))
            family = escape(str(record.dates.get("family_count", "[?]")))
            rec_id = escape(record.id)

            score = calculate_signal_score(record.cross_references)
            score_bar = _render_score_bar(score)

            lines: list[str] = []
            lines.append(f"[bold]{title}[/]")
            lines.append(_rule())
            lines.append("")
            lines.append(f"  [bold dim]ID[/]       [cyan]{rec_id}[/]")
            lines.append(f"  [bold dim]STATUS[/]   {status}")
            lines.append(f"  [bold dim]ASSIGNEE[/] {assignee}")
            lines.append(f"  [bold dim]FILED[/]    {date_f}   [bold dim]FAMILY[/]  {family}")
            lines.append("")
            lines.append(_rule("SIGNAL SCORE"))
            lines.append(f"  {score_bar}")
            if record.cross_references:
                lines.append(f"  {_render_signal_dots(record.cross_references)}")
            else:
                lines.append("  [dim]○ no cross-reference signals — score reflects raw record[/]")
            lines.append("")
            lines.append(_rule("ABSTRACT"))
            lines.append(f"{abstract}")

            self.update("\n".join(lines))
        except Exception as e:
            self.update(f"ERR: Info rendering failed: {escape(str(e))}")
