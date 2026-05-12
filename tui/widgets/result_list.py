from textual.widgets import ListView, ListItem, Label
from textual.app import ComposeResult
from core.models import PatentRecord

class ResultListItem(ListItem):
    def __init__(self, record: PatentRecord, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record = record

    def compose(self) -> ComposeResult:
        date = self.record.dates.get("filed", "[?]")
        yield Label(f"[{date}] {self.record.id}: {self.record.title}")

class ResultList(ListView):
    pass
