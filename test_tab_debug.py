#!/usr/bin/env python3
"""Test tab ID handling and widget queries."""

import asyncio
from textual.widgets import TabbedContent, TabPane, Static
from textual.app import App, ComposeResult
from tui.widgets.info_tab import InfoTab
from tui.widgets.claims_tab import ClaimsTab
from tui.widgets.image_tab import ImageTab
from core.models import PatentRecord, CrossReference

class TabTestApp(App):
    def compose(self) -> ComposeResult:
        with TabbedContent(id="tabs"):
            with TabPane("Info", id="tab_info"):
                yield InfoTab(id="info_tab")
            with TabPane("Claims", id="tab_claims"):
                yield ClaimsTab(id="claims_tab")
            with TabPane("Image", id="tab_image"):
                yield ImageTab(id="image_tab")

async def test_tab_queries():
    """Test what widgets can be queried."""
    app = TabTestApp()
    
    async with app.run_test() as pilot:
        print("✓ App initialized")
        
        # Test TabbedContent active property
        tabs = app.query_one(TabbedContent)
        active = tabs.active
        print(f"\nTabs.active returns: {active!r} (type: {type(active).__name__})")
        
        # Test querying by widget class
        try:
            info_tab = app.query_one(InfoTab)
            print(f"✓ QueryOne(InfoTab) found: {info_tab}")
        except Exception as e:
            print(f"✗ QueryOne(InfoTab) failed: {e}")
        
        try:
            claims_tab = app.query_one(ClaimsTab)
            print(f"✓ QueryOne(ClaimsTab) found: {claims_tab}")
        except Exception as e:
            print(f"✗ QueryOne(ClaimsTab) failed: {e}")
        
        try:
            image_tab = app.query_one(ImageTab)
            print(f"✓ QueryOne(ImageTab) found: {image_tab}")
        except Exception as e:
            print(f"✗ QueryOne(ImageTab) failed: {e}")
        
        # Test tab pane queries by ID
        try:
            pane = app.query_one("#tab_info", TabPane)
            print(f"✓ QueryOne('#tab_info') found TabPane: {pane.title}")
        except Exception as e:
            print(f"✗ QueryOne('#tab_info') failed: {e}")
        
        # Test simulating a tab switch
        print("\nSimulating tab activation...")
        tabs.active = "tab_claims"
        await pilot.pause()
        
        active_after = tabs.active
        print(f"After setting active='tab_claims': {active_after!r}")
        
        # Test widget method availability
        print("\nCheckingwidget methods:")
        test_record = PatentRecord(
            id="TEST001",
            title="Test Patent",
            assignee="Test Corp",
            dates={"filed": "2024-01-01"},
            abstract="Test abstract",
            claims=["Claim 1", "Claim 2"],
            image_urls=["http://example.com/image.png"],
            status="ACTIVE",
            family_id="FAM001",
            cross_references=[]
        )
        
        print(f"  - info_tab.update_record: {hasattr(info_tab, 'update_record')}")
        print(f"  - claims_tab.load_claims: {hasattr(claims_tab, 'load_claims')}")
        print(f"  - image_tab.load_image: {hasattr(image_tab, 'load_image')}")
        print(f"  - claims_tab.is_loaded: {hasattr(claims_tab, 'is_loaded')}")
        print(f"  - image_tab.is_loaded: {hasattr(image_tab, 'is_loaded')}")

if __name__ == "__main__":
    asyncio.run(test_tab_queries())
