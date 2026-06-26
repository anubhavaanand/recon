from typing import Dict

from core.models import PatentRecord


def calculate_arbitrage_status(record: PatentRecord) -> Dict[str, str]:
    """
    Calculate simulated jurisdiction status for arbitrage panel.
    In a real app, this would query Espacenet/WIPO APIs.
    """
    # Simulate coverage based on family size or ID prefixes
    countries = ["US", "EP", "JP", "CN", "KR", "DE", "FR", "GB"]
    status_map = {}

    # Simple heuristic: if ID starts with country code, it's ACTIVE there
    # Otherwise, simulate based on a simple hash of the patent ID
    import hashlib
    h = int(hashlib.md5(record.id.encode()).hexdigest(), 16)

    for i, c in enumerate(countries):
        if record.id.startswith(c):
            status_map[c] = "ACTIVE"
        else:
            # Deterministic simulation
            state = (h >> i) & 0x3
            if state == 0:
                status_map[c] = "ACTIVE"
            elif state == 1:
                status_map[c] = "PENDING"
            elif state == 2:
                status_map[c] = "EXPIRED"
            else:
                status_map[c] = "NO_FILING"

    return status_map

def render_arbitrage_table(status_map: Dict[str, str]) -> str:
    """Render a clean rule-based table for the arbitrage panel."""
    lines = ["Country │ Status      │ Coverage", "────────┼─────────────┼──────────"]
    for c, s in status_map.items():
        cov = "● Full" if s == "ACTIVE" else "○ Partial" if s == "PENDING" else "  None"
        lines.append(f"{c:<8}│ {s:<12}│ {cov}")
    return "\n".join(lines)
