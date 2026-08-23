
from rich.markup import escape
from textual.widgets import Static

from core.models import PatentRecord


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
        self._all_claims = [c for c in (record.claims or []) if c and c != "[?]"]
        self.is_loaded = True

        if not self._all_claims:
            # Lazy deep-fetch: claims live on the patent's detail page.
            self.update("[dim]Loading claims…[/]")
            fetched = await self._fetch_full_claims(record)
            if fetched:
                self._all_claims = fetched
            else:
                self._render_empty()
                return

        self._render_claims()

    async def _fetch_full_claims(self, record: PatentRecord) -> list[str]:
        """Fetch claims from the patent detail page via source scraper."""
        import asyncio as _asyncio

        try:
            from clients.scrapers import (
                EPOScraper,
                GooglePatentsScraper,
            )

            pid = (record.id or "").upper()
            scraper = None
            if pid.startswith("EP"):
                scraper = EPOScraper()
            elif pid[:2] in ("US", "WO", "CN", "JP", "KR", "DE", "GB", "FR"):
                scraper = GooglePatentsScraper()
            if scraper is None:
                return []
            full = await _asyncio.wait_for(scraper.fetch(record.id), timeout=8.0)
            if full and full.claims:
                return [c for c in full.claims if c and c != "[?]"]
        except Exception:
            pass
        return []

    def _render_empty(self) -> None:
        self.update(
            "[dim]No claims available for this record.[/]\n"
            "[dim]Source did not expose claim text; USPTO-keyed records carry claims natively.[/]"
        )

    def toggle_independent(self) -> None:
        """Toggle independent-claims-only view (PRD key `i`)."""
        self._independent_only = not self._independent_only
        self._render_claims()

    def _render_claims(self) -> None:
        if not self._all_claims:
            self._render_empty()
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
