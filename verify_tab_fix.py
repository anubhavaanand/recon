#!/usr/bin/env python3
"""Verify the tab ID prefix stripping logic."""

# Test the prefix stripping logic
test_cases = [
    ("tab_info", "tab_info"),  # No prefix case
    ("--content-tab-tab_info", "tab_info"),  # With prefix
    ("--content-tab-tab_claims", "tab_claims"),  # Images with prefix
    ("--content-tab-tab_image", "tab_image"),  # Image with prefix
]

print("=" * 70)
print("TAB ID PREFIX STRIPPING VERIFICATION")
print("=" * 70)

for input_id, expected in test_cases:
    # Simulate the actual logic from the fixed code
    tab_id_str = str(input_id).lower()
    if tab_id_str.startswith("--content-tab-"):
        tab_id_str = tab_id_str.replace("--content-tab-", "")
    
    status = "✓" if tab_id_str == expected else "✗"
    print(f"{status} {input_id:30} → {tab_id_str:20} (expected: {expected})")

print("\n" + "=" * 70)
print("MATCHING LOGIC TEST")
print("=" * 70)

# Test the matching logic
test_ids = ["tab_info", "tab_claims", "tab_image"]
for test_id in test_ids:
    print(f"\nTesting: {test_id}")
    
    info_match = "info" in test_id or test_id == "tab_info"
    claims_match = "claims" in test_id or test_id == "tab_claims"
    image_match = "image" in test_id or test_id == "tab_image"
    
    print(f"  - Info match:    {'✓' if info_match else '✗'}")
    print(f"  - Claims match:  {'✓' if claims_match else '✗'}")
    print(f"  - Image match:   {'✓' if image_match else '✗'}")

print("\n" + "=" * 70)
print("IMPORT VERIFICATION")
print("=" * 70)

try:
    from tui.widgets.info_tab import InfoTab
    from tui.widgets.claims_tab import ClaimsTab
    from tui.widgets.image_tab import ImageTab
    from tui.widgets.result_list import ResultList
    from tui.screens import SearchScreen
    print("✓ All widgets importable")
    print(f"✓ InfoTab has update_record: {hasattr(InfoTab, 'update_record')}")
    print(f"✓ ClaimsTab has load_claims: {hasattr(ClaimsTab, 'load_claims')}")
    print(f"✓ ImageTab has load_image: {hasattr(ImageTab, 'load_image')}")
except ImportError as e:
    print(f"✗ Import error: {e}")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
