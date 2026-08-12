"""Azure AI Foundry provider — one endpoint serves all configured models
(grok-4.3, gpt-5.6-sol, gpt-5.4, gpt-5.6-terra, Kimi-K2.6).

Validated contract (2026-08): POST {resource}/models/chat/completions with
`api-key` header and the model in the body. GPT-5-class models:
  - require `max_completion_tokens` (NOT `max_tokens`)
  - reject `temperature` other than the default (1) -> we omit temperature
  - are reasoning models -> need a generous completion budget or output is empty
Kimi-K2.6 is text-only (no image input).
"""
from __future__ import annotations
import os
import re
import httpx

from ..config import get_settings

TEXT_ONLY_MODELS = {"kimi-k2.6", "kimi-k2", "kimi"}


def _resource_root(endpoint: str) -> str:
    return re.sub(r"/api/projects/[^/]+/?$", "", endpoint.rstrip("/")).rstrip("/")


class AzureFoundryProvider:
    name = "azure_foundry"

    def __init__(self, model: str | None = None):
        s = get_settings()
        if not s.azure_api_key or not s.azure_endpoint:
            raise RuntimeError("AZURE_FOUNDRY_ENDPOINT / AZURE_FOUNDRY_API_KEY not set")
        self._model = model or s.azure_model
        self.supports_vision = self._model.lower() not in TEXT_ONLY_MODELS
        self._url = os.getenv("AZURE_FOUNDRY_CHAT_URL") or (
            _resource_root(s.azure_endpoint) + "/models/chat/completions")
        self._api_version = os.getenv("AZURE_FOUNDRY_API_VERSION", "2024-05-01-preview")
        self._key = s.azure_api_key
        self._max_completion_tokens = int(os.getenv("AZURE_MAX_COMPLETION_TOKENS", "4096"))
        # temperature omitted by default (GPT-5 rejects non-default); set to opt in
        self._temperature = os.getenv("AZURE_TEMPERATURE")
        self._timeout = float(os.getenv("AZURE_TIMEOUT", "180"))

    def complete(self, system_prompt: str, user_prompt: str, images: list[dict]) -> str:
        content: list[dict] = [{"type": "text", "text": user_prompt}]
        if self.supports_vision:
            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{img['media_type']};base64,{img['b64']}"},
                })
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "max_completion_tokens": self._max_completion_tokens,
        }
        if self._temperature is not None:
            body["temperature"] = float(self._temperature)
        import time
        max_retries = int(os.getenv("AZURE_MAX_RETRIES", "5"))
        for attempt in range(max_retries + 1):
            r = httpx.post(
                self._url, params={"api-version": self._api_version},
                headers={"api-key": self._key, "Content-Type": "application/json"},
                json=body, timeout=self._timeout,
            )
            if r.status_code == 429 and attempt < max_retries:
                wait = float(r.headers.get("retry-after") or (2 ** attempt))
                time.sleep(min(wait, 30))
                continue
            break
        if r.status_code != 200:
            raise RuntimeError(f"Azure {self._model} HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        return data["choices"][0]["message"]["content"] or ""
