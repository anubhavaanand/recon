from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import PatentRecord

SAMPLE_RECORD = PatentRecord(
    id="US12345678",
    title="Test Patent",
    assignee="ACME Corp",
    dates={"filed": "2020-01-01", "granted": "2022-06-15"},
    abstract="A test patent abstract with sufficient detail.",
    claims=["Claim 1: A method.", "Claim 2: The method of claim 1."],
    image_urls=["https://patentimages.storage.googleapis.com/img1.png"],
    status="active",
    family_id="FAM001",
)


@pytest.mark.asyncio
async def test_tab_initialization():
    from tui.screens import SearchScreen
    screen = SearchScreen()
    assert screen._active_tab == "info"


@pytest.mark.asyncio
async def test_tab_switching_via_set_active_tab():
    from tui.screens import SearchScreen
    screen = SearchScreen()
    screen._set_active_tab("claims")
    assert screen._active_tab == "claims"
    screen._set_active_tab("image")
    assert screen._active_tab == "image"
    screen._set_active_tab("info")
    assert screen._active_tab == "info"


@pytest.mark.asyncio
async def test_action_next_tab():
    from tui.screens import SearchScreen
    from tui.widgets.result_list import ResultList
    screen = SearchScreen()
    screen._current_record = lambda: None
    mock_rl = MagicMock(spec=ResultList)
    screen.query_one = lambda *a, **kw: mock_rl if a and a[0] == ResultList else MagicMock()
    screen._active_tab = "info"
    screen.action_next_tab()
    assert screen._active_tab == "claims"
    screen.action_next_tab()
    assert screen._active_tab == "image"
    screen.action_next_tab()
    assert screen._active_tab == "info"


@pytest.mark.asyncio
async def test_action_prev_tab():
    from tui.screens import SearchScreen
    from tui.widgets.result_list import ResultList
    screen = SearchScreen()
    screen._current_record = lambda: None
    mock_rl = MagicMock(spec=ResultList)
    screen.query_one = lambda *a, **kw: mock_rl if a and a[0] == ResultList else MagicMock()
    screen._active_tab = "info"
    screen.action_prev_tab()
    assert screen._active_tab == "image"
    screen.action_prev_tab()
    assert screen._active_tab == "claims"
    screen.action_prev_tab()
    assert screen._active_tab == "info"


@pytest.mark.asyncio
async def test_tab_content_loads_on_selection():
    from tui.screens import SearchScreen
    from tui.widgets.info_tab import InfoTab
    screen = SearchScreen()
    mock_info = MagicMock(spec=InfoTab)
    mock_info.update_record = MagicMock()

    def mock_query_one(selector, expected_type=None):
        if selector == InfoTab or selector == "#info_tab":
            return mock_info
        return MagicMock()

    screen.query_one = mock_query_one
    screen._enrich_current = MagicMock()
    screen._load_record(SAMPLE_RECORD)
    mock_info.update_record.assert_called_once_with(SAMPLE_RECORD)


@pytest.mark.asyncio
async def test_tab_no_blank_content_after_switch():
    from tui.screens import SearchScreen
    from tui.widgets.claims_tab import ClaimsTab
    from tui.widgets.image_tab import ImageTab
    from tui.widgets.info_tab import InfoTab
    screen = SearchScreen()
    mock_info = MagicMock(spec=InfoTab)
    mock_info.update_record = MagicMock()
    mock_claims = MagicMock(spec=ClaimsTab)
    mock_claims.load_claims = AsyncMock()
    mock_claims.reset = MagicMock()
    mock_image = MagicMock(spec=ImageTab)
    mock_image.reset = MagicMock()

    def mock_query_one(selector, expected_type=None):
        if selector == InfoTab or selector == "#info_tab":
            return mock_info
        if selector == ClaimsTab or selector == "#claims_tab":
            return mock_claims
        if selector == ImageTab or selector == "#image_tab":
            return mock_image
        return MagicMock()

    screen.query_one = mock_query_one
    screen._active_tab = "claims"
    screen._enrich_current = MagicMock()
    screen._load_record(SAMPLE_RECORD)
    assert mock_info.update_record.called
    assert mock_claims.reset.called
    assert mock_image.reset.called


@pytest.mark.asyncio
async def test_multiple_tab_switches_work():
    from tui.screens import SearchScreen
    screen = SearchScreen()
    screen._set_active_tab("info")
    assert screen._active_tab == "info"
    screen._set_active_tab("claims")
    assert screen._active_tab == "claims"
    screen._set_active_tab("image")
    assert screen._active_tab == "image"
    screen._set_active_tab("info")
    assert screen._active_tab == "info"


@pytest.mark.asyncio
async def test_preview_populated_on_record_load():
    from tui.screens import SearchScreen
    from tui.widgets.claims_tab import ClaimsTab
    from tui.widgets.image_tab import ImageTab
    from tui.widgets.info_tab import InfoTab
    screen = SearchScreen()
    mock_info = MagicMock(spec=InfoTab)
    mock_info.update_record = MagicMock()
    mock_claims = MagicMock(spec=ClaimsTab)
    mock_claims.reset = MagicMock()
    mock_image = MagicMock(spec=ImageTab)
    mock_image.reset = MagicMock()

    def mock_query_one(selector, expected_type=None):
        if selector == InfoTab or selector == "#info_tab":
            return mock_info
        if selector == ClaimsTab or selector == "#claims_tab":
            return mock_claims
        if selector == ImageTab or selector == "#image_tab":
            return mock_image
        return MagicMock()

    screen.query_one = mock_query_one
    screen._enrich_current = MagicMock()
    screen._load_record(SAMPLE_RECORD)
    mock_info.update_record.assert_called_once_with(SAMPLE_RECORD)
    assert mock_claims.reset.called
    assert mock_image.reset.called


@pytest.mark.asyncio
async def test_tab_help_overlay_initial_state():
    from tui.screens import SearchScreen
    screen = SearchScreen()
    assert screen._show_help is False


@pytest.mark.asyncio
async def test_render_tab_bar():
    from tui.screens import SearchScreen
    screen = SearchScreen()
    bar = screen._render_tab_bar()
    assert "<Info>" in bar
    assert " Claims " in bar
    assert " Image " in bar
