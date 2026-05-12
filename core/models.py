from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class CrossReference:
    source: str  # NIH, NSF, SEC, OpenAlex, arXiv, OpenCorporates
    url: str
    metadata: Dict = field(default_factory=dict)
    # Weight per signal. Default 1.0 meaning one equal signal.
    # Scoring code multiplies this by 20 to produce the final contribution.
    weight: float = 1.0

@dataclass
class PatentRecord:
    id: str
    title: str
    assignee: str
    dates: Dict[str, str]  # Mapping of date types to date strings
    abstract: str
    claims: List[str]
    image_urls: List[str]
    status: str
    family_id: str
    cross_references: List[CrossReference] = field(default_factory=list)

    def __post_init__(self):
        self.id = self.id if self.id else "UNKNOWN"
        self.title = self.title if self.title else "[?]"
        self.assignee = self.assignee if self.assignee else "[?]"
        self.abstract = self.abstract if self.abstract else "[?]"
        self.status = self.status if self.status else "UNKNOWN"
        self.family_id = self.family_id if self.family_id else "UNKNOWN"
        if not self.dates:
            self.dates = {"filed": "[?]"}
        for k, v in self.dates.items():
            if not v:
                self.dates[k] = "[?]"
        # Ensure claims and image_urls are flagged when empty per constitution
        if not self.claims:
            self.claims = ["[?]"]
        if not self.image_urls:
            self.image_urls = ["[?]"]
