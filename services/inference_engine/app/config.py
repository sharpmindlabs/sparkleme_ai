"""Runtime configuration, loaded from environment / .env."""
from __future__ import annotations
import os
from pathlib import Path
from functools import lru_cache

try:
    from dotenv import load_dotenv
    # load services/inference_engine/.env if present
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINE_ROOT = Path(__file__).resolve().parents[1]


class Settings:
    def __init__(self):
        # Read env at instantiation (NOT at class-definition time) so callers
        # that mutate os.environ + get_settings.cache_clear() take effect.
        self.provider = os.getenv("SPARKLEME_PROVIDER", "mock").lower()

        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

        self.azure_endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
        self.azure_api_key = os.getenv("AZURE_FOUNDRY_API_KEY", "")
        self.azure_model = os.getenv("SPARKLEME_AZURE_MODEL", "gpt-5.6-sol")

        self.images_root = Path(os.getenv("SPARKLEME_IMAGES_ROOT", str(ENGINE_ROOT / "fixtures" / "cases")))
        self.goldenset_path = Path(os.getenv(
            "SPARKLEME_GOLDENSET", str(REPO_ROOT / "data" / "goldenset" / "top50_cases.json")))
        self.prompt_path = Path(os.getenv(
            "SPARKLEME_PROMPT", str(ENGINE_ROOT / "prompts" / "consolidated_first_pass_prompt.md")))
        self.results_dir = Path(os.getenv("SPARKLEME_RESULTS_DIR", str(ENGINE_ROOT / "results")))

    def model_label(self) -> str:
        if self.provider == "anthropic":
            return self.anthropic_model
        if self.provider == "azure_foundry":
            return self.azure_model
        return "mock"


@lru_cache
def get_settings() -> "Settings":
    return Settings()
