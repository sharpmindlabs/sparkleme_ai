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
    provider: str = os.getenv("SPARKLEME_PROVIDER", "mock").lower()

    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    azure_endpoint: str = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
    azure_api_key: str = os.getenv("AZURE_FOUNDRY_API_KEY", "")
    azure_model: str = os.getenv("SPARKLEME_AZURE_MODEL", "gpt-5.6-sol")

    images_root: Path = Path(os.getenv("SPARKLEME_IMAGES_ROOT", str(ENGINE_ROOT / "fixtures" / "cases")))
    goldenset_path: Path = Path(os.getenv(
        "SPARKLEME_GOLDENSET", str(REPO_ROOT / "data" / "goldenset" / "top50_cases.json")))
    prompt_path: Path = Path(os.getenv(
        "SPARKLEME_PROMPT", str(ENGINE_ROOT / "prompts" / "consolidated_first_pass_prompt.md")))
    results_dir: Path = Path(os.getenv("SPARKLEME_RESULTS_DIR", str(ENGINE_ROOT / "results")))

    def model_label(self) -> str:
        if self.provider == "anthropic":
            return self.anthropic_model
        if self.provider == "azure_foundry":
            return self.azure_model
        return "mock"


@lru_cache
def get_settings() -> "Settings":
    return Settings()
