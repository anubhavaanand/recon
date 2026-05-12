import pytest
from unittest.mock import AsyncMock, MagicMock

from tui.screens import SearchScreen
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab


@pytest.mark.asyncio
async def test_claims_load_only_on_activation():
    screen = SearchScreen()

    # Create mock tabs
    mock_claims = MagicMock(spec=ClaimsTab)
    mock_claims.is_loaded = False
    mock_claims.load_claims = AsyncMock()

    mock_image = MagicMock(spec=ImageTab)
    mock_image.is_loaded = False
    mock_image.load_image = AsyncMock()

    # Patch screen.query_one to return our mocks when asked for the tab classes
    def query_one(arg):
        if arg is ClaimsTab:
            return mock_claims
        if arg is ImageTab:
            return mock_image
        return MagicMock()

    screen.query_one = query_one

    # If a non-claims tab is active, ClaimsTab.load_claims should NOT be called
    await screen._load_active_tab("some_other_tab", record=MagicMock())
    mock_claims.load_claims.assert_not_called()

    # When the claims tab is active, load_claims should be awaited
    await screen._load_active_tab("tab_claims", record=MagicMock())
    mock_claims.load_claims.assert_awaited()
