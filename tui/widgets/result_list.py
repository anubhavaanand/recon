from datetime import date, datetime

from rich.markup import escape
from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView

from core.models import PatentRecord


# Source badge colors (Tokyo Night accents)
_SOURCE_COLORS = {
    "uspto": "#7aa2f7",
    "epo": "#bb9af7",
    "wipo": "#7dcfff",
    "google": "#9ece6a",
    "lens": "#e0af68",
    "patsnap": "#f7768e",
}


def _age_str(filed_date: str) -> str:
    """Return human age string like '2y' or '8m'."""
    try:
        d = datetime.strptime(filed_date, "%Y-%m-%d").date()
        delta = date.today() - d
        years = delta.days // 365
        months = (delta.days % 365) // 30
        if years >= 1:
            return f"{years}y"
        return f"{months}m"
    except Exception:
        return "[?]"


def _mini_bar(score: int, width: int = 6) -> str:
    """Return compact score bar with score-graded color."""
    filled = int((score / 100) * width)
    if score >= 60:
        color = "#9ece6a"      # green
    elif score >= 40:
        color = "#e0af68"      # amber
    elif score > 0:
        color = "#7aa2f7"      # blue
    else:
        color = "#3b4261"      # faint
    bar = ("█" * filled).replace("█", f"[{color}]█[/]")
    return bar + "[dim]" + "░" * (width - filled) + "[/]"


def _source_badge(source_meta: str) -> str:
    src = (source_meta or "").strip().lower()
    color = _SOURCE_COLORS.get(src, "#565f89")
    name = (source_meta or "?").upper()[:7]
    return f"[{color}]▎{name}[/]"


class ResultListItem(ListItem):
    def __init__(self, record: PatentRecord, position: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self.position = position

    def compose(self) -> ComposeResult:
        yield Label(self._generate_label_text(), id="score_label", markup=True)

    def _generate_label_text(self) -> str:
        from core.scoring import calculate_signal_score

        from core.models import normalize_date
        score = calculate_signal_score(self.record.cross_references)
        filed_iso = normalize_date(self.record.dates.get("filed", ""))
        year = filed_iso[:4] if filed_iso != "[?]" else "[?]"
        age = _age_str(filed_iso) if filed_iso != "[?]" else ""
        rec_id = escape(self.record.id[:18])
        title = escape(self.record.title)
        if len(self.record.title) > 30:
            title = escape(self.record.title[:29]) + "…"
        badge = _source_badge(getattr(self.record, "source", "") or self._infer_source())

        line1 = (
            f"[dim]{self.position:>02}[/] [bold #7aa2f7]{rec_id:<18}[/] "
            f"{_mini_bar(score)} [dim]{(year + (" · " + age if age else "")):>9}[/]"
        )
        line2 = f"   {badge} [dim]│[/] {title}"
        return f"{line1}\n{line2}"

    def _infer_source(self) -> str:
        pid = (self.record.id or "").upper()
        if pid.startswith("US"):
            return "uspto"
        if pid.startswith("EP"):
            return "epo"
        if pid.startswith("WO"):
            return "wipo"
        if "MOCK" in pid or pid.startswith("LN"):
            return "lens"
        return ""

    def refresh_score(self) -> None:
        try:
            self.query_one("#score_label", Label).update(self._generate_label_text())
        except Exception:
            pass


class ResultList(ListView):
    pass
