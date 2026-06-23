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
        
        def clean_text(text: str) -> str:
            if not text or text == "[?]" or text == "UNKNOWN":
                return text
            # 1. Fix "AbstractTranslated" -> "Abstract: Translated"
            text = re.sub(r'AbstractTranslated\b', 'Abstract: Translated', text)
            text = re.sub(r'AbstractTranslated\s+from', 'Abstract: Translated from', text)
            # 2. Fix camelCase/missing spaces between English words (e.g. fromChinese -> from Chinese)
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
            # Fix spacing around digits (e.g. Claim1 -> Claim 1, 1Abstract -> 1 Abstract)
            text = re.sub(r'([a-zA-Z]{2,})([0-9])', r'\1 \2', text)
            text = re.sub(r'([0-9])([a-zA-Z]{2,})', r'\1 \2', text)
            # 3. Fix missing spaces between English words and CJK characters (e.g. Chinese本发明 -> Chinese 本发明)
            text = re.sub(r'([A-Za-z0-9]+)([\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af])', r'\1 \2', text)
            # 4. Fix missing spaces between CJK characters and English words (e.g. 本发明The -> 本发明 The)
            text = re.sub(r'([\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af])([A-Za-z0-9])', r'\1 \2', text)
            return text

        self.title = clean_text(self.title) if self.title else "[?]"
        self.assignee = clean_text(self.assignee) if self.assignee else "[?]"
        self.abstract = clean_text(self.abstract) if self.abstract else "[?]"
        self.status = self.status if self.status else "UNKNOWN"
        self.family_id = self.family_id if self.family_id else "UNKNOWN"
        if not self.dates:
            self.dates = {"filed": "[?]"}
        for k, v in self.dates.items():
            if not v:
                self.dates[k] = "[?]"
        if not self.claims:
            self.claims = ["[?]"]
        else:
            self.claims = [clean_text(c) for c in self.claims]
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
