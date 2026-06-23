from rich.markup import escape
from textual.widgets import Static
from core.models import PatentRecord
from core.scoring import calculate_signal_score


def _render_score_bar(score: int, width: int = 20) -> str:
    """Return a unicode block progress bar: ████████░░░░ 82/100"""
    filled = int((score / 100) * width)
    empty = width - filled
    return f"{'█' * filled}{'░' * empty} {score}/100"


def _render_signal_dots(refs) -> str:
    """Return signal dot summary: NIH●●●●● SEC●●●●○ DOE○"""
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
        dots = "●" * filled + "○" * (5 - filled)
        parts.append(f"{src}{dots}")
    return "  ".join(parts)


def _render_status_pill(status: str) -> str:
    """Return colored status pill."""
    if not status:
        return "[?]"
    import re
    # Strip bullet points, question marks, brackets, and extra spaces
    s = re.sub(r'[●•\?\[\]]', '', status).strip().upper()
    if not s or s in ("UNKNOWN", ""):
        return "[?]"
    if s in ("ACTIVE", "GRANTED"):
        return f"● {s}"
    elif s in ("EXPIRED",):
        return f"● EXPIRED→PUBLIC DOMAIN"
    elif s in ("ABANDONED",):
        return f"● ABANDONED→FREE TO USE"
    elif s in ("PENDING",):
        return f"○ PENDING"
    return f"○ {s}"


class InfoTab(Static):
    """Info tab: title, metadata, score bar, signals, action hints."""

    def update_record(self, record: PatentRecord | None) -> None:
        try:
            if not record:
                self.update("No patent selected.\nUse ↑↓ to navigate results.")
                return

            title    = escape(record.title)
            rec_id   = escape(record.id)
            assignee = escape(record.assignee)
            status   = _render_status_pill(record.status)
            abstract = escape(record.abstract)
            date_f   = escape(record.dates.get("filed", "[?]"))
            date_exp = escape(record.dates.get("expires", "[?]"))
            family   = escape(record.dates.get("family_count", "[?]"))

            score    = calculate_signal_score(record.cross_references)
            score_bar = _render_score_bar(score)

            signals_section = ""
            if record.cross_references:
                dots = _render_signal_dots(record.cross_references)
                signals_section = f"\n{dots}\n"
                signals_section += "\n─── Intelligence Signals ───────────────────────\n"
                for ref in record.cross_references:
                    conf = ref.metadata.get("confidence", 100.0)
                    signals_section += f"  {escape(ref.source)}: {escape(ref.url)}  ({conf:.1f}%)\n"
            else:
                signals_section = "\n○○○○○  No cross-reference signals found.\n"

            content = (
                f"{title}\n"
                f"{'─' * 48}\n"
                f"Assignee: {assignee}  │  Status: {status}\n"
                f"Filed: {date_f}   Expires: {date_exp}   Family: {family}\n"
                f"\n"
                f"Score: {score_bar}\n"
                f"{signals_section}\n"
                f"─── Abstract ───────────────────────────────────\n"
                f"{abstract}\n"
                f"\n"
                f"(d)ownload  (s)ave  (r)ead full  (o)pen"
            )
            self.update(content)
        except Exception as e:
            self.update(f"ERR: Info rendering failed: {escape(str(e))}")
