from rich.markup import escape
from textual.widgets import Static
from core.models import PatentRecord
import asyncio


class ClaimsTab(Static):
    """Claims tab: numbered claims with Independent/Dependent labels."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_loaded = False
        self.current_record: PatentRecord | None = None
        self._independent_only = False
        self._all_claims: list[str] = []

    async def load_claims(self, record: PatentRecord) -> None:
        self.current_record = record
        self._all_claims = record.claims or []
        self.is_loaded = True
        self._render()

    def toggle_independent(self) -> None:
        """Toggle independent-claims-only view (PRD key `i`)."""
        self._independent_only = not self._independent_only
        self._render()

    def _render(self) -> None:
        if not self._all_claims:
            self.update("No claims available.")
            return

        mode = "[i] Showing: Independent only" if self._independent_only else "[i] Showing: All claims"
        lines = [f"─── Claims ─────────────────────────────────────\n{mode}\n"]

        for idx, claim in enumerate(self._all_claims, 1):
            raw = claim.strip()
            is_dependent = "of claim" in raw.lower()

            if self._independent_only and is_dependent:
                continue

            label = "Dependent" if is_dependent else "Independent"
            lines.append(f"CLAIM {idx} ({label})")
            lines.append("─" * 48)
            lines.append(escape(raw))
            lines.append("")

        self.update("\n".join(lines))

    def reset(self) -> None:
        self.is_loaded = False
        self.current_record = None
        self._all_claims = []
        self._independent_only = False
        self.update("")
