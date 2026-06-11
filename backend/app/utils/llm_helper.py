import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

async def call_groq_llm(prompt: str, system_prompt: str = "You are an expert supply chain management AI assistant.") -> Optional[str]:
    """
    Call Groq API using HTTPX to generate intelligent supply chain reasoning/decisions.
    Falls back to None if API key is not configured or request fails.
    """
    if not settings.use_llm_agents or not settings.groq_api_key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.groq_model or "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logger.warning(f"Groq API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Failed to communicate with Groq API: {e}")

    return None
