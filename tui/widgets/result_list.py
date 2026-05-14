from textual.widgets import ListView, ListItem, Label
from textual.app import ComposeResult
from rich.markup import escape
from core.models import PatentRecord

class ResultListItem(ListItem):
    def __init__(self, record: PatentRecord, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record

    def compose(self) -> ComposeResult:
        date = escape(self.record.dates.get("filed", "[?]"))
        title = escape(self.record.title)
        rec_id = escape(self.record.id)
        yield Label(f"[{date}] {rec_id}: {title}")

class ResultList(ListView):
    pass
