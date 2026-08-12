"""Provider interface: given prompts + images, return the model's raw JSON text."""
from __future__ import annotations
from typing import Protocol


class VisionProvider(Protocol):
    name: str
    supports_vision: bool

    def complete(self, system_prompt: str, user_prompt: str,
                 images: list[dict]) -> str:
        """Return the model's raw text response (expected to contain JSON).
        `images` is a list of {media_type, b64}."""
        ...


def get_provider(provider: str):
    provider = (provider or "mock").lower()
    if provider == "mock":
        from .mock import MockProvider
        return MockProvider()
    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if provider == "azure_foundry":
        from .azure_foundry import AzureFoundryProvider
        return AzureFoundryProvider()
    raise ValueError(f"unknown provider '{provider}'")
