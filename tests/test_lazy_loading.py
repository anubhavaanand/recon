import pytest
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab
from core.models import PatentRecord

@pytest.mark.asyncio
async def test_claims_lazy_loading():
    record = PatentRecord(id="1", title="A", assignee="X", dates={}, abstract="Ab", claims=[], image_urls=[], status="active", family_id="F1")
    tab = ClaimsTab()
    
    # Assert not loaded initially
    assert not tab.is_loaded
    
    # Trigger load
    await tab.load_claims(record)
    
    # Assert loaded
    assert tab.is_loaded

@pytest.mark.asyncio
async def test_image_lazy_loading():
    record = PatentRecord(id="1", title="A", assignee="X", dates={}, abstract="Ab", claims=[], image_urls=["http://example.com/img.png"], status="active", family_id="F1")
    tab = ImageTab()
    
    # Assert not loaded initially
    assert not tab.is_loaded
    
    # Trigger load
    await tab.load_image(record)
    
    # Assert loaded
    assert tab.is_loaded
