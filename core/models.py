import dataclasses
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class CrossReference:
    source: str  # NIH, NSF, SEC, OpenAlex, arXiv, OpenCorporates
    url: str
    date: Optional[str] = None  # ISO date string for temporal proximity scoring
    metadata: Dict = field(default_factory=dict)
    # Weight per signal. Default 1.0 meaning one equal signal.
    # Scoring code multiplies this by 20 to produce the final contribution.
    weight: float = 1.0

    def __repr__(self) -> str:
        return f"CrossReference(source={self.source}, url={self.url})"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CrossReference":
        return cls(**data)

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
        import re
        self.id = re.sub(r'[\s_\-]', '', self.id).upper()
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
        if not self.claims:
            self.claims = ["[?]"]
        if not self.image_urls:
            self.image_urls = ["[?]"]

    def __repr__(self) -> str:
        return f"PatentRecord(id={self.id}, title={self.title}, assignee={self.assignee})"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PatentRecord":
        if "cross_references" in data:
            data["cross_references"] = [
                CrossReference(**cr) if not isinstance(cr, CrossReference) else cr
                for cr in data["cross_references"]
            ]
        return cls(**data)
