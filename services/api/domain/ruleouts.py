"""Deterministic Level-1 (hair) and Level-2 (Fitzpatrick) rule-outs.

Encodes the canonical tables in Functional Spec §5.1 / §5.2 verbatim. These are
hard rule-outs: ``candidate_set = L1 ∩ L2`` and an empty intersection is a
``CONFLICTING_INPUTS`` terminal state (§5.2).
"""
from __future__ import annotations

from .palettes import (
    PALETTES, PALETTE_SET,
    TRUE_WINTER, TRUE_SUMMER, TRUE_SPRING, TRUE_AUTUMN,
    COOL, WARM, DEEP, BRIGHT, LIGHT, MUTED,
)

# Versioned rule table (NFR: versioned rule tables for reproducibility).
RULE_TABLE_VERSION = "ruleout-v1"

# ---- Level 1: natural hair colour at age 17–20 (§5.1) --------------------
# The exactly-12 canonical hair selections.
HAIR_VALUES: list[str] = [
    "Dark Blonde", "Blonde", "Light Blonde", "Very Light Blonde", "Lightest Blonde",
    "Light Brown",
    "Brown",
    "Dark Brown", "Darkest Brown", "Black",
    "Obvious Red Hair",
    "I Do Not Know",
]

_ALL = list(PALETTES)

# "Remaining possibilities" column of §5.1, keyed by hair selection.
_BLONDE_GROUP = [TRUE_SPRING, TRUE_SUMMER, LIGHT]
_LEVEL1_REMAINING: dict[str, list[str]] = {
    "Dark Blonde": _BLONDE_GROUP,
    "Blonde": _BLONDE_GROUP,
    "Light Blonde": _BLONDE_GROUP,
    "Very Light Blonde": _BLONDE_GROUP,
    "Lightest Blonde": _BLONDE_GROUP,
    # Light Brown keeps Light/Warm "for safety" per the table.
    "Light Brown": [TRUE_SPRING, TRUE_SUMMER, LIGHT, WARM],
    "Brown": [TRUE_AUTUMN, TRUE_SPRING, TRUE_SUMMER, WARM, MUTED],
    # Dark/Darkest Brown/Black: cannot be Light -> all nine others.
    "Dark Brown": [p for p in _ALL if p != LIGHT],
    "Darkest Brown": [p for p in _ALL if p != LIGHT],
    "Black": [p for p in _ALL if p != LIGHT],
    "Obvious Red Hair": [TRUE_SPRING, TRUE_AUTUMN, WARM],
    "I Do Not Know": list(_ALL),
}

# ---- Level 2: Fitzpatrick type (§5.2) ------------------------------------
FITZPATRICK_VALUES = ["I", "II", "III", "IV", "V", "VI"]

_LEVEL2_REMAINING: dict[str, list[str]] = {
    # V, VI cannot be True Summer / True Spring / Light.
    "V": [p for p in _ALL if p not in {TRUE_SUMMER, TRUE_SPRING, LIGHT}],
    "VI": [p for p in _ALL if p not in {TRUE_SUMMER, TRUE_SPRING, LIGHT}],
    # III, IV cannot be Light.
    "III": [p for p in _ALL if p != LIGHT],
    "IV": [p for p in _ALL if p != LIGHT],
    # I, II: all ten.
    "I": list(_ALL),
    "II": list(_ALL),
}


class InvalidRuleInput(ValueError):
    """Raised when hair/fitzpatrick selection is not a canonical value."""


def level1_candidates(hair_colour: str) -> list[str]:
    if hair_colour not in _LEVEL1_REMAINING:
        raise InvalidRuleInput(f"hair_colour '{hair_colour}' is not one of the 12 canonical values")
    # Preserve canonical palette order for deterministic output.
    remaining = set(_LEVEL1_REMAINING[hair_colour])
    return [p for p in PALETTES if p in remaining]


def level2_candidates(fitzpatrick: str) -> list[str]:
    if fitzpatrick not in _LEVEL2_REMAINING:
        raise InvalidRuleInput(f"fitzpatrick '{fitzpatrick}' is not one of I..VI")
    remaining = set(_LEVEL2_REMAINING[fitzpatrick])
    return [p for p in PALETTES if p in remaining]


def candidate_set(hair_colour: str, fitzpatrick: str) -> list[str]:
    """Level 1 ∩ Level 2, in canonical palette order. May be empty."""
    l1 = set(level1_candidates(hair_colour))
    l2 = set(level2_candidates(fitzpatrick))
    inter = l1 & l2
    return [p for p in PALETTES if p in inter]


def rule_out_preview(hair_colour: str, fitzpatrick: str) -> dict:
    """Live preview payload for FR-2.5 (Level 1, Level 2, intersection)."""
    l1 = level1_candidates(hair_colour)
    l2 = level2_candidates(fitzpatrick)
    cs = candidate_set(hair_colour, fitzpatrick)
    return {
        "rule_table_version": RULE_TABLE_VERSION,
        "level1": l1,
        "level2": l2,
        "candidate_set": cs,
        "conflicting": len(cs) == 0,
    }


def is_palette(value: str) -> bool:
    return value in PALETTE_SET
