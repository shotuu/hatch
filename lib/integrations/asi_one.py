"""ASI:One LLM wrapper (OpenAI-compatible).

Docs: https://docs.asi1.ai/docs/quick-start
"""
from __future__ import annotations

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
