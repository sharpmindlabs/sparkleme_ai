"""Canonical palette / season structure for the platform (mirrors §1.1 of the
Functional Spec and the inference engine's ``palettes.py``)."""
from __future__ import annotations

TRUE_WINTER = "True Winter"
TRUE_SUMMER = "True Summer"
TRUE_SPRING = "True Spring"
TRUE_AUTUMN = "True Autumn"
COOL = "Cool"
WARM = "Warm"
DEEP = "Deep"
BRIGHT = "Bright"
LIGHT = "Light"
MUTED = "Muted"

PALETTES: list[str] = [
    TRUE_WINTER, TRUE_SUMMER, TRUE_SPRING, TRUE_AUTUMN,
    COOL, WARM, DEEP, BRIGHT, LIGHT, MUTED,
]
PALETTE_SET = set(PALETTES)

HOME_SEASONS = ["Winter", "Summer", "Spring", "Autumn"]

# Valid flows within each home season (§1.1).
FLOWS_BY_SEASON: dict[str, list[str]] = {
    "Winter": [TRUE_WINTER, COOL, DEEP, BRIGHT],
    "Summer": [TRUE_SUMMER, COOL, LIGHT, MUTED],
    "Spring": [TRUE_SPRING, WARM, LIGHT, BRIGHT],
    "Autumn": [TRUE_AUTUMN, WARM, DEEP, MUTED],
}

TRUE_SEASON = {
    TRUE_WINTER: "Winter", TRUE_SUMMER: "Summer",
    TRUE_SPRING: "Spring", TRUE_AUTUMN: "Autumn",
}

# §1.1 undertone per home season.
SEASON_UNDERTONE = {"Winter": "Cool", "Summer": "Cool", "Spring": "Warm", "Autumn": "Warm"}


def is_valid_flow(flow_result: str, home_season: str) -> bool:
    return flow_result in FLOWS_BY_SEASON.get(home_season, [])


def seasons_for_palette(palette: str) -> list[str]:
    """Home seasons a palette can belong to (True palettes -> one; flows -> two)."""
    return [s for s in HOME_SEASONS if palette in FLOWS_BY_SEASON[s]]


def derive_home_season(palette: str, prefer: str | None = None) -> str | None:
    """Pick a home season for a palette. Deterministic: honour ``prefer`` when the
    palette is a valid flow of it, otherwise the first season (in canonical order)."""
    options = seasons_for_palette(palette)
    if not options:
        return None
    if prefer and prefer in options:
        return prefer
    return options[0]
