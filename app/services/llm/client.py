import requests
import logging
from app.core.config import get_settings

logger = logging.getLogger("psc_agent.llm.client")
settings = get_settings()


def call_ollama(prompt: str, model: str | None = None) -> dict:
    model = model or settings.ollama_model
    logger.info(f"Calling Ollama with model: {model}")

    response = requests.post(
        f"{settings.ollama_base_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "num_predict": 4096,
                "temperature": 0.3,
            },
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def call_ollama_generate(prompt: str, model: str | None = None) -> dict:
    """Legacy generate endpoint (for simple tasks)."""
    model = model or settings.ollama_model
    response = requests.post(
        f"{settings.ollama_base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 4096,
            },
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()
