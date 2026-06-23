import httpx
from typing import List
from core.models import PatentRecord

async def search_patentsview(query: str) -> List[PatentRecord]:
    """Search USPTO PatentsView legacy endpoint. No auth required."""
    url = "https://api.patentsview.org/patents/query"
    payload = {
        "q": {"_text_any": {"patent_abstract": query}},
        "f": ["patent_number", "patent_title", "patent_abstract", "patent_date", "assignee_organization"],
        "o": {"per_page": 5},
        "s": [{"patent_date": "desc"}]
    }
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                patents = data.get("patents", [])
                if patents:
                    for p in patents:
                        assignees = p.get("assignees", [])
                        assignee_name = assignees[0].get("assignee_organization", "UNKNOWN") if assignees else "UNKNOWN"
                        
                        records.append(PatentRecord(
                            id="US" + p.get("patent_number", ""),
                            title=p.get("patent_title", "UNKNOWN"),
                            assignee=assignee_name,
                            dates={"filed": p.get("patent_date", "[?]")},
                            abstract=p.get("patent_abstract", ""),
                            claims=[],
                            image_urls=[],
                            status="ACTIVE",
                            family_id="UNKNOWN"
                        ))
    except Exception as e:
        import logging
        logging.getLogger("recon").error(f"PatentsView error: {e}")
        pass
        
    return records
