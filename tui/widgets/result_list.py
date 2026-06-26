from datetime import date, datetime

from rich.markup import escape
from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView

from core.models import PatentRecord


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
    """Return compact score bar: ████░░"""
    filled = int((score / 100) * width)
    return "█" * filled + "░" * (width - filled)


class ResultListItem(ListItem):
    def __init__(self, record: PatentRecord, position: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record
        self.position = position

    def compose(self) -> ComposeResult:
        yield Label(self._generate_label_text(), id="score_label")

    def _generate_label_text(self) -> str:
        from core.scoring import calculate_signal_score
        score = calculate_signal_score(self.record.cross_references)
        age = _age_str(self.record.dates.get("filed", ""))
        bar = _mini_bar(score)
        rec_id = escape(self.record.id[:20].ljust(20))
        return f"{self.position:>2}  {rec_id}  {bar} {score:>3}%  {age}"

    def refresh_score(self) -> None:
        try:
            self.query_one("#score_label", Label).update(self._generate_label_text())
        except Exception:
            pass

class ResultList(ListView):
    pass
