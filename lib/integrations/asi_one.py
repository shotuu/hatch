"""ASI:One LLM wrapper (OpenAI-compatible).

Docs: https://docs.asi1.ai/docs/quick-start
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from openai import OpenAI

ASI_BASE_URL = "https://api.asi1.ai/v1"
DEFAULT_MODEL = "asi1-mini"


@lru_cache(maxsize=1)
def client() -> OpenAI:
    api_key = os.environ.get("ASI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ASI_API_KEY not set — copy .env.example to .env and fill it in"
        )
    return OpenAI(api_key=api_key, base_url=ASI_BASE_URL)


def chat(
    system: str,
    user: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 400,
) -> str:
    resp = client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


def chat_json(
    system: str,
    user: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
    max_tokens: int = 900,
) -> dict:
    """Same as chat() but parses output as JSON. Tolerates code-fence wrapping."""
    sys = system + "\n\nReturn ONLY valid JSON. No markdown fences. No prose before or after."
    raw = chat(sys, user, model=model, temperature=temperature, max_tokens=max_tokens).strip()

    if raw.startswith("```"):
        # strip ```json … ``` or ``` … ```
        nl = raw.find("\n")
        end = raw.rfind("```")
        if nl != -1 and end > nl:
            raw = raw[nl + 1 : end].strip()
        else:
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()

    return json.loads(raw)
