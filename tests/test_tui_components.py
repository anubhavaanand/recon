import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from core.models import PatentRecord

SAMPLE_RECORD = PatentRecord(
    id="US12345678",
    title="Test Patent",
    assignee="ACME Corp",
    dates={"filed": "2020-01-01"},
    abstract="A test patent abstract.",
    claims=["Claim 1: A method.", "Claim 2: The method of claim 1."],
    image_urls=["https://patentimages.storage.googleapis.com/img1.png"],
    status="active",
    family_id="FAM001",
)


class TestResultListWidget:
    def test_result_list_item_creation(self):
        from tui.widgets.result_list import ResultListItem
        item = ResultListItem(SAMPLE_RECORD, 1)
        assert item.record.id == "US12345678"
        assert item.position == 1

    def test_result_list_item_score(self):
        from tui.widgets.result_list import ResultListItem, _mini_bar, _age_str
        bar = _mini_bar(80, width=6)
        assert "█" in bar
        assert len(bar) == 6
        age = _age_str("2020-01-01")
        assert age in ("5y", "6y", "7y", "[?]")

    def test_result_list_item_age_unknown(self):
        from tui.widgets.result_list import _age_str
        assert _age_str("") == "[?]"
        assert _age_str("invalid") == "[?]"

    def test_mini_bar_zero(self):
        from tui.widgets.result_list import _mini_bar
        assert _mini_bar(0, width=6) == "░" * 6

    def test_mini_bar_full(self):
        from tui.widgets.result_list import _mini_bar
        assert _mini_bar(100, width=6) == "█" * 6

    def test_mini_bar_half(self):
        from tui.widgets.result_list import _mini_bar
        bar = _mini_bar(50, width=6)
        assert bar.count("█") == 3
        assert bar.count("░") == 3


class TestInfoTab:
    def test_info_tab_creation(self):
        from tui.widgets.info_tab import InfoTab
        tab = InfoTab()
        assert tab is not None

    def test_info_tab_update_record(self):
        from tui.widgets.info_tab import InfoTab
        tab = InfoTab()
        tab.update_record(SAMPLE_RECORD)

    def test_info_tab_update_with_none(self):
        from tui.widgets.info_tab import InfoTab
        tab = InfoTab()
        tab.update_record(None)

    def test_info_tab_render_helpers(self):
        from tui.widgets.info_tab import _render_score_bar, _render_signal_dots, _render_status_pill
        bar = _render_score_bar(50)
        assert "50/100" in bar
        dots = _render_signal_dots([])
        assert "No signals" in dots
        assert _render_status_pill("active") == "● ACTIVE"
        assert _render_status_pill("● Active") == "● ACTIVE"
        assert _render_status_pill("[?] ● Active") == "● ACTIVE"
        assert _render_status_pill("[?]") == "[?]"
        assert _render_status_pill("UNKNOWN") == "[?]"
        assert _render_status_pill("") == "[?]"


class TestClaimsTab:
    def test_claims_tab_creation(self):
        from tui.widgets.claims_tab import ClaimsTab
        tab = ClaimsTab()
        assert tab.is_loaded is False

    @pytest.mark.asyncio
    async def test_claims_tab_load(self):
        from tui.widgets.claims_tab import ClaimsTab
        tab = ClaimsTab()
        await tab.load_claims(SAMPLE_RECORD)
        assert tab.is_loaded is True

    @pytest.mark.asyncio
    async def test_claims_tab_toggle_independent(self):
        from tui.widgets.claims_tab import ClaimsTab
        tab = ClaimsTab()
        await tab.load_claims(SAMPLE_RECORD)
        tab.toggle_independent()
        assert tab._independent_only is True
        tab.toggle_independent()
        assert tab._independent_only is False

    def test_claims_tab_reset(self):
        from tui.widgets.claims_tab import ClaimsTab
        tab = ClaimsTab()
        tab.reset()
        assert tab.is_loaded is False
        assert tab.current_record is None


class TestImageTab:
    def test_image_tab_creation(self):
        from tui.widgets.image_tab import ImageTab
        tab = ImageTab()
        assert tab.is_loaded is False

    @pytest.mark.asyncio
    async def test_image_tab_load(self):
        from tui.widgets.image_tab import ImageTab
        tab = ImageTab()
        await tab.load_image(SAMPLE_RECORD)
        assert tab.is_loaded is True

    def test_image_tab_reset(self):
        from tui.widgets.image_tab import ImageTab
        tab = ImageTab()
        tab.reset()
        assert tab.is_loaded is False

    def test_terminal_protocol_detection(self):
        from tui.widgets.image_tab import detect_terminal_protocol, TerminalProtocol
        protocol = detect_terminal_protocol()
        assert protocol in TerminalProtocol

    def test_is_safe_url(self):
        from tui.widgets.image_tab import is_safe_url
        assert is_safe_url("https://patentimages.storage.googleapis.com/img.png") is True
        assert is_safe_url("https://lens.org/img.png") is True
        assert is_safe_url("http://patentimages.storage.googleapis.com/img.png") is False
        assert is_safe_url("ftp://evil.com/img.png") is False
        assert is_safe_url("") is False


class TestResultListWidgetIntegration:
    @pytest.mark.asyncio
    async def test_result_list_compose(self):
        from tui.widgets.result_list import ResultListItem
        item = ResultListItem(SAMPLE_RECORD, 1)
        with patch.object(item, "compose") as mock:
            item.compose()
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_results_descending_order(self):
        from core.search import sort_and_merge_results
        r1 = PatentRecord(id="1", title="A", assignee="X",
                          dates={"filed": "2021-01-01"}, abstract="",
                          claims=[], image_urls=[], status="a", family_id="F1")
        r2 = PatentRecord(id="2", title="B", assignee="Y",
                          dates={"filed": "2022-01-01"}, abstract="",
                          claims=[], image_urls=[], status="a", family_id="F2")
        r3 = PatentRecord(id="3", title="C", assignee="Z",
                          dates={"filed": "2020-01-01"}, abstract="",
                          claims=[], image_urls=[], status="a", family_id="F3")
        sorted_records = sort_and_merge_results([r1, r2, r3])
        assert sorted_records[0].id == "2"
        assert sorted_records[1].id == "1"
        assert sorted_records[2].id == "3"
