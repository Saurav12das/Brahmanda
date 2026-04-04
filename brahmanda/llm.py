"""LLM Backend Abstraction — supports both Claude API and local Ollama.

Usage:
    BRAHMANDA_BACKEND=ollama python -m brahmanda.main    # local Qwen
    BRAHMANDA_BACKEND=claude python -m brahmanda.main    # Claude API
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Protocol

import httpx

from brahmanda.config import (
    ANTHROPIC_API_KEY,
    LLM_BACKEND,
    OLLAMA_BASE_URL,
)


@dataclass
class LLMResponse:
    """Unified response from any LLM backend."""
    text: str


class LLMClient(Protocol):
    """Protocol for LLM backends."""

    async def generate(self, model: str, system: str, prompt: str, max_tokens: int = 300) -> LLMResponse:
        ...


class ClaudeClient:
    """Anthropic Claude API client."""

    def __init__(self) -> None:
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    async def generate(self, model: str, system: str, prompt: str, max_tokens: int = 300) -> LLMResponse:
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(text=response.content[0].text)


class OllamaClient:
    """Local Ollama client using HTTP API."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL) -> None:
        self.base_url = base_url
        self._semaphore = asyncio.Semaphore(2)  # limit concurrent local model calls

    async def generate(self, model: str, system: str, prompt: str, max_tokens: int = 300) -> LLMResponse:
        async with self._semaphore:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.8,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("message", {}).get("content", "")
                return LLMResponse(text=text)


def strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from LLM output."""
    import re
    return re.sub(r'```(?:json)?\s*', '', text).strip()


def create_client() -> LLMClient:
    """Factory: create the appropriate LLM client based on config."""
    if LLM_BACKEND == "ollama":
        return OllamaClient()
    else:
        return ClaudeClient()
