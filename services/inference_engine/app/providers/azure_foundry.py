"""Azure AI Foundry provider — one endpoint serves all configured models
(grok-4.3, gpt-5.6-sol, gpt-5.4, gpt-5.6-terra, Kimi-K2.6).

Uses the OpenAI-compatible `/models` inference route on the Foundry resource.
NOTE: this adapter is written to the documented Foundry contract but could not
be validated from the dev sandbox (the Azure host is egress-blocked here). The
base URL / api-version are env-overridable so it can be tuned on your infra.
"""
from __future__ import annotations
import re

from ..config import get_settings

# Models that cannot accept images — usable only as text adjudicators, not drape judges.
TEXT_ONLY_MODELS = {"kimi-k2.6", "kimi-k2", "kimi"}


def _derive_models_base(endpoint: str, override: str | None) -> str:
    if override:
        return override.rstrip("/")
    # strip a trailing /api/projects/<name> to get the resource root
    root = re.sub(r"/api/projects/[^/]+/?$", "", endpoint.rstrip("/"))
    return root.rstrip("/") + "/models"


class AzureFoundryProvider:
    name = "azure_foundry"

    def __init__(self):
        import os
        s = get_settings()
        if not s.azure_api_key or not s.azure_endpoint:
            raise RuntimeError("AZURE_FOUNDRY_ENDPOINT / AZURE_FOUNDRY_API_KEY not set")
        self._model = s.azure_model
        self.supports_vision = self._model.lower() not in TEXT_ONLY_MODELS
        base_url = _derive_models_base(s.azure_endpoint, os.getenv("AZURE_FOUNDRY_BASE_URL"))
        api_version = os.getenv("AZURE_FOUNDRY_API_VERSION", "2024-05-01-preview")
        from openai import OpenAI
        # Azure authenticates with the `api-key` header (not Bearer).
        self._client = OpenAI(
            base_url=base_url,
            api_key=s.azure_api_key,
            default_query={"api-version": api_version},
            default_headers={"api-key": s.azure_api_key},
        )

    def complete(self, system_prompt: str, user_prompt: str, images: list[dict]) -> str:
        user_content: list[dict] = []
        if self.supports_vision:
            for img in images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{img['media_type']};base64,{img['b64']}"},
                })
        user_content.append({"type": "text", "text": user_prompt})
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=0,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return resp.choices[0].message.content or ""
