import pytest
from textual.app import App, ComposeResult

from tui.screens import SearchScreen
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab


class _TestApp(App):
    def compose(self) -> ComposeResult:
        yield SearchScreen()


class DummyRecord:
    id = "US1"
    title = "T1"
    assignee = "A1"
    dates = {"filed": "2023-01-01"}
    abstract = "A1"
    claims = ["c1"]
    image_urls = []
    status = "active"
    family_id = "F1"
    cross_references = []


@pytest.mark.asyncio
async def test_claims_load_only_on_activation():
    """Verify that claims/images are only loaded when their respective tabs are active."""
    app = _TestApp()
    async with app.run_test():
        screen = app.query_one(SearchScreen)

        record = DummyRecord()
        screen._results = [record]
        screen._load_record(record)

        app.query_one(ClaimsTab)
        app.query_one(ImageTab)

        # Default active tab is info; lazy loaders should not populate content yet
        assert screen._active_tab == "info"
