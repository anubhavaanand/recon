import httpx
import json

async def translate_text(text: str, target_language: str = "English") -> str:
    """
    Translates the provided text to the target language using a local Ollama instance.
    Follows the Constitution's Dry, Actionable Voice.
    """
    if not text or text == "[?]" or text == "UNKNOWN":
        return text

    ollama_url = "http://localhost:11434/api/generate"
    
    # We use deepseek-coder as a reasonable default for RECON if available, 
    # but llama3 is also common. User can override via config in the future.
    # We ask the model to be strict, deterministic, and dry.
    prompt = (
        f"Translate the following patent text to {target_language}. "
        "Provide ONLY the translation, with no conversational filler, no apologies, "
        "and maintain a dry, technical, and factual voice.\n\n"
        f"Text:\n{text}"
    )

    payload = {
        "model": "deepseek-coder",  # Or deepseek-r1, llama3, etc.
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0, # Deterministic (Zero-AI Default principle)
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ollama_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                # If model not found, return an actionable error
                if response.status_code == 404:
                    return "ERR: Ollama model 'deepseek-coder' not found. Run 'ollama pull deepseek-coder'."
                return f"ERR: Translation failed with status {response.status_code}."
                
    except httpx.ConnectError:
        return "ERR: Ollama not running on localhost:11434."
    except Exception as e:
        return f"ERR: Translation error: {str(e)}"
