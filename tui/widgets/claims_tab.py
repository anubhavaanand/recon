from textual.widgets import Static
from core.models import PatentRecord
import asyncio

class ClaimsTab(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_loaded = False
        self.current_record = None

    async def load_claims(self, record: PatentRecord):
        self.current_record = record
        self.update("Loading claims...")
        # Simulate network delay for fetching deep data
        await asyncio.sleep(0.1)
        
        claims_text = "\n\n".join(record.claims) if record.claims else "No claims available."
        self.update(claims_text)
        self.is_loaded = True
        
    def reset(self):
        self.is_loaded = False
        self.current_record = None
        self.update("")
