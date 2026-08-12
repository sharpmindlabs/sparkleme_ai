"""Anthropic Claude vision provider (reachable from the dev sandbox)."""
from __future__ import annotations
import os

from ..config import get_settings


class AnthropicProvider:
    name = "anthropic"
    supports_vision = True

    def __init__(self):
        s = get_settings()
        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        # Use the public API, not any base-url override the harness may inject.
        os.environ.pop("ANTHROPIC_BASE_URL", None)
        from anthropic import Anthropic
        self._client = Anthropic(api_key=s.anthropic_api_key)
        self._model = s.anthropic_model

    def complete(self, system_prompt: str, user_prompt: str, images: list[dict]) -> str:
        content: list[dict] = []
        for img in images:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": img["media_type"], "data": img["b64"]},
            })
        content.append({"type": "text", "text": user_prompt})
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
