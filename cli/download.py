import httpx
import os
from pathlib import Path
from core.models import PatentRecord

async def download_patent_assets(record: PatentRecord, base_path: str = "downloads"):
    """
    Download patent figures and metadata for offline archival.
    PRD §3.5 — Download (key: d).
    """
    target_dir = Path(base_path) / record.id
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save metadata as JSON
    import json
    import dataclasses
    meta_path = target_dir / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(dataclasses.asdict(record), f, indent=2)
        
    # 2. Download figures
    if record.image_urls:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            for i, url in enumerate(record.image_urls, 1):
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        ext = Path(url).suffix or ".jpg"
                        img_path = target_dir / f"figure_{i}{ext}"
                        with open(img_path, "wb") as f:
                            f.write(response.content)
                except Exception as e:
                    print(f"ERR: Failed to download figure {i}: {e}")
                    
    return target_dir
