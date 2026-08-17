"""OpenRouter API client — chat completions (topics, tutoring, diagnosis,
practice generation/scoring) and embeddings (RAG).
"""
import json
from typing import Any

import httpx

from app.config import get_settings


class OpenRouterError(RuntimeError):
    pass


def _error_message(resp: httpx.Response) -> str:
    """OpenRouter error bodies are JSON with an {"error": {"message": ...}}
    shape; fall back to raw text if that's not what came back."""
    try:
        detail = resp.json()["error"]["message"]
    except (json.JSONDecodeError, KeyError, TypeError):
        detail = resp.text
    return f"OpenRouter request failed ({resp.status_code}): {detail}"


def _headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://bodhi.app",
        "X-Title": "Bodhi",
    }


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    json_mode: bool = False,
    temperature: float = 0.3,
) -> str:
    """Returns the raw text content of the first choice."""
    settings = get_settings()
    payload: dict[str, Any] = {
        "model": model or settings.openrouter_chat_model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=_headers(),
            json=payload,
        )
    if resp.status_code >= 400:
        raise OpenRouterError(_error_message(resp))

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Unexpected OpenRouter response shape: {data}") from exc


async def chat_completion_json(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """Chat completion that expects strict JSON back; parses and returns it."""
    content = await chat_completion(messages, model=model, json_mode=True, temperature=temperature)
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise OpenRouterError(f"Model did not return valid JSON: {content[:500]}") from exc


async def embed_texts(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Returns one embedding vector per input text, in order."""
    if not texts:
        return []

    settings = get_settings()
    payload = {
        "model": model or settings.openrouter_embed_model,
        "input": texts,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.openrouter_base_url}/embeddings",
            headers=_headers(),
            json=payload,
        )
    if resp.status_code >= 400:
        raise OpenRouterError(_error_message(resp))

    data = resp.json()
    try:
        items = sorted(data["data"], key=lambda d: d["index"])
        return [item["embedding"] for item in items]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Unexpected OpenRouter embeddings response shape: {data}") from exc
