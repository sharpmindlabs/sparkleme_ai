"""The ten SparkleMe palettes, home-season/flow structure, and helpers to
normalize Carol's free-text ground-truth answers (column O) into palettes."""
from __future__ import annotations

# Canonical palette identifiers
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

HOME_SEASONS = ["Winter", "Summer", "Spring", "Autumn"]

# Valid flows within each home season (from the spec / expert workbook)
FLOWS_BY_SEASON: dict[str, list[str]] = {
    "Winter": [TRUE_WINTER, COOL, DEEP, BRIGHT],
    "Summer": [TRUE_SUMMER, COOL, LIGHT, MUTED],
    "Spring": [TRUE_SPRING, WARM, LIGHT, BRIGHT],
    "Autumn": [TRUE_AUTUMN, WARM, DEEP, MUTED],
}

# The home season a "True" palette belongs to
TRUE_SEASON = {
    TRUE_WINTER: "Winter", TRUE_SUMMER: "Summer",
    TRUE_SPRING: "Spring", TRUE_AUTUMN: "Autumn",
}

# Neighbouring palettes used for lenient boundary scoring: two palettes are
# "neighbours" when they share a home season (i.e. appear together in a flow set).
def neighbours(palette: str) -> set[str]:
    out: set[str] = set()
    for flows in FLOWS_BY_SEASON.values():
        if palette in flows:
            out.update(flows)
    out.discard(palette)
    return out


def is_valid_flow(flow_result: str, home_season: str) -> bool:
    return flow_result in FLOWS_BY_SEASON.get(home_season, [])


# Longest names first so "True Winter" matches before "Winter"/"True".
_MATCH_ORDER = sorted(PALETTES, key=len, reverse=True)


def extract_palettes(text: str) -> list[str]:
    """Return every canonical palette named in a free-text answer, in the order
    they first appear. Handles Carol's boundary phrasings, e.g.
    'Deep or True Winter moving towards Deep'  -> [Deep, True Winter]
    'True Summer, moving slightly toward Cool' -> [True Summer, Cool]
    'True Autumn' -> [True Autumn]
    """
    if not text:
        return []
    import re
    hits: list[tuple[int, str]] = []
    masked = text
    for p in _MATCH_ORDER:
        # word-boundary match so "Light" doesn't match inside "slightly"
        m = re.search(r"\b" + re.escape(p) + r"\b", masked, re.IGNORECASE)
        if m:
            hits.append((m.start(), p))
            # blank out the match so shorter names don't re-match inside it
            masked = masked[:m.start()] + ("#" * (m.end() - m.start())) + masked[m.end():]
    return [p for _, p in sorted(hits, key=lambda x: x[0])]


def canonical_ground_truth(text: str) -> dict:
    """Parse a column-O answer into a primary palette + accepted set (primary
    plus any explicitly-named boundary neighbour)."""
    found = extract_palettes(text)
    if not found:
        return {"primary": None, "accepted": [], "raw": text}
    primary = found[0]
    return {"primary": primary, "accepted": found, "raw": text}
