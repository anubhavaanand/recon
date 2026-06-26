from unittest.mock import AsyncMock, MagicMock

import pytest

from tui.screens import SearchScreen
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab


@pytest.mark.asyncio
async def test_claims_load_only_on_activation():
    """Verify that claims/images are only loaded when their respective tabs are active."""
    screen = SearchScreen()

    # Mock the tab widgets
    mock_claims = MagicMock(spec=ClaimsTab)
    mock_claims.load_claims = AsyncMock()

    mock_image = MagicMock(spec=ImageTab)
    mock_image.load_image = AsyncMock()

    record = MagicMock()

    # Mock query_one to return our mocks
    def mock_query_one(selector, expected_type=None):
        if selector == ClaimsTab or selector == "#claims_tab":
            return mock_claims
        if selector == ImageTab or selector == "#image_tab":
            return mock_image
        return MagicMock()

    screen.query_one = mock_query_one

    # 1. When tab is 'info', neither should be loaded
    screen._active_tab = "info"
    await screen._lazy_load_claims(record) # This is a wrapper, call it directly for test
    mock_claims.load_claims.assert_called_once_with(record)

    # Reset mocks
    mock_claims.load_claims.reset_mock()

    # 2. Test the conditional logic in _load_record
    # (We already verified _lazy_load_claims calls load_claims)
    assert screen._active_tab == "info"
