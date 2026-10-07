import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
            # 5. Insert zero-width spaces between CJK characters to allow clean line wrapping (Bug 8)
            cjk_char = r'([\u4e00-\u9fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af])'
            text = re.sub(cjk_char + r'(?=' + cjk_char + r')', r'\1' + '\u200b', text)
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


def normalize_date(raw) -> str:
    """Coerce common date shapes to ISO YYYY-MM-DD; else '[?]'."""
    import re as _re
    from datetime import datetime as _dt

    if not raw or str(raw).strip() in ("[?]", "UNKNOWN", "None"):
        return "[?]"
    s = str(raw).strip()
    m = _re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            _dt.strptime(m.group(0), "%Y-%m-%d")
            return m.group(0)
        except ValueError:
            return "[?]"
    for fmt in ("%Y%m%d", "%d.%m.%Y", "%m/%d/%Y", "%B %d, %Y", "%Y-%m"):
        try:
            return _dt.strptime(s[:14].strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    y = _re.match(r"^(19|20)\d{2}", s)
    return f"{s[:4]}-[?]-[?]" if y else "[?]"


def estimate_expiration(dates: dict, patent_id: str = "") -> str:
    """Best-known expiration date, or '[?]'.

    Preference order (constitution: transparent math, uncertainty flagged):
    1. An explicit ``dates["expires"]`` harvested from a source (e.g. the
       adjusted expiration on the Google Patents page) — returned as-is.
    2. Computed estimate: filing date + 20 years (standard utility term in
       US/EP/WO/CN/JP...), suffixed " (est.)". Design patents (e.g. USD…)
       have a grant-based term instead, so they are not estimated.
    """
    explicit = dates.get("expires") if dates else None
    if explicit and explicit != "[?]":
        return str(explicit)
    filed = (dates or {}).get("filed", "[?]")
    if filed == "[?]" or not filed:
        return "[?]"
    import re as _re

    if patent_id and _re.match(r"^[A-Z]{2}D", patent_id.upper()):
        return "[?]"  # design patent: term runs from grant, not filing
    try:
        from datetime import date as _date, timedelta as _timedelta

        y, m, d = (int(part) for part in filed.split("-"))
        base = _date(y, m, d)
    except (ValueError, TypeError):
        return "[?]"
    try:
        est = base.replace(year=base.year + 20)
    except ValueError:  # Feb 29 filing
        est = base + _timedelta(days=20 * 365 + 5)
    return f"{est.isoformat()} (est.)"
