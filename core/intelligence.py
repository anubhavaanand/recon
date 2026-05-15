import httpx
import json
from typing import List
from core.models import PatentRecord

class SynthesisEngine:
    """Local LLM synthesis via Ollama — PRD §5."""
    
    def __init__(self, model: str = "deepseek-v2"):
        self.model = model
        self.base_url = "http://localhost:11434/api"

    async def _query_ollama(self, prompt: str) -> str:
        """Query the local Ollama instance."""
        try:
            async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
                return f"ERR: Ollama returned {response.status_code}."
        except Exception as e:
            return f"ERR: Could not connect to Ollama. Ensure 'ollama serve' is running. ({str(e)})"

    async def summarize_results(self, records: List[PatentRecord]) -> str:
        """Generate a synthesis summary of multiple patent records."""
        if not records:
            return "No records to summarize."
        
        context = "\n".join([
            f"- {r.id}: {r.title}. Assignee: {r.assignee}. Abstract: {r.abstract[:200]}..."
            for r in records
        ])
        
        prompt = (
            "You are a patent intelligence analyst. Summarize the following patents, "
            "highlighting common trends, major players, and technical white space:\n\n"
            f"{context}\n\n"
            "Summary (Dry, authoritative voice):"
        )
        
        return await self._query_ollama(prompt)

    async def translate_text(self, text: str, target_lang: str = "English") -> str:
        """Translate patent content using local LLM."""
        prompt = (
            f"Translate the following patent text into {target_lang}. "
            "Maintain technical terminology accuracy:\n\n"
            f"{text}\n\n"
            "Translation:"
        )
        return await self._query_ollama(prompt)
