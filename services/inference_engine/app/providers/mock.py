"""Deterministic mock provider: no network, stable output per client.

It does NOT look at ground truth — it derives a plausible-but-arbitrary verdict
from a hash of the image bytes so the full pipeline + UI run in the sandbox.
"""
from __future__ import annotations
import hashlib
import json

from ..palettes import HOME_SEASONS, FLOWS_BY_SEASON, neighbours


class MockProvider:
    name = "mock"
    supports_vision = True

    def complete(self, system_prompt: str, user_prompt: str, images: list[dict]) -> str:
        seed = hashlib.sha256(
            ("".join(i["b64"][:64] for i in images) or user_prompt).encode()
        ).hexdigest()
        h = int(seed, 16)
        season = HOME_SEASONS[h % 4]
        flows = FLOWS_BY_SEASON[season]
        flow = flows[(h >> 4) % len(flows)]
        conf = ["High", "Medium", "Low"][(h >> 8) % 3]
        lean = None
        if (h >> 12) % 3 == 0:
            nb = sorted(neighbours(flow))
            lean = nb[(h >> 16) % len(nb)] if nb else None
        result = {
            "home_season": season,
            "flow_result": flow,
            "leaning": lean,
            "confidence": conf,
            "steps": [
                {"step": "Undertone", "winner": "Cool" if season in ("Winter", "Summer") else "Warm",
                 "criteria_cited": [2, 3, 7], "reasoning": "[mock] deterministic placeholder"},
                {"step": "Home Season", "winner": season,
                 "criteria_cited": [1, 4, 5], "reasoning": "[mock] deterministic placeholder"},
                {"step": "Flow", "winner": flow,
                 "criteria_cited": [2, 5, 6, 7], "reasoning": "[mock] deterministic placeholder"},
            ],
            "final_reasoning": "[mock provider] Wire a real provider (anthropic / azure_foundry) for genuine analysis.",
        }
        return json.dumps(result)
