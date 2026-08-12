"""Level-1/Level-2 rule-out tables + candidate-set intersection (§5.1/§5.2)."""
from __future__ import annotations
import pytest

from services.api.domain import ruleouts
from services.api.domain.palettes import (
    TRUE_SPRING, TRUE_SUMMER, TRUE_AUTUMN, TRUE_WINTER, LIGHT, WARM, MUTED, PALETTES,
)


def test_hair_has_exactly_12_values():
    assert len(ruleouts.HAIR_VALUES) == 12


def test_blonde_level1():
    assert set(ruleouts.level1_candidates("Blonde")) == {TRUE_SPRING, TRUE_SUMMER, LIGHT}


def test_light_brown_keeps_light_and_warm():
    assert set(ruleouts.level1_candidates("Light Brown")) == {TRUE_SPRING, TRUE_SUMMER, LIGHT, WARM}


def test_brown_level1():
    assert set(ruleouts.level1_candidates("Brown")) == {
        TRUE_AUTUMN, TRUE_SPRING, TRUE_SUMMER, WARM, MUTED}


def test_black_is_all_but_light():
    assert set(ruleouts.level1_candidates("Black")) == set(PALETTES) - {LIGHT}


def test_red_hair_level1():
    assert set(ruleouts.level1_candidates("Obvious Red Hair")) == {TRUE_SPRING, TRUE_AUTUMN, WARM}


def test_i_do_not_know_is_all_ten():
    assert set(ruleouts.level1_candidates("I Do Not Know")) == set(PALETTES)


def test_fitz_v_vi_ruleout():
    for f in ("V", "VI"):
        cs = set(ruleouts.level2_candidates(f))
        assert TRUE_SUMMER not in cs and TRUE_SPRING not in cs and LIGHT not in cs


def test_fitz_iii_iv_only_rules_out_light():
    assert set(ruleouts.level2_candidates("III")) == set(PALETTES) - {LIGHT}
    assert set(ruleouts.level2_candidates("IV")) == set(PALETTES) - {LIGHT}


def test_fitz_i_ii_all_ten():
    assert set(ruleouts.level2_candidates("I")) == set(PALETTES)


# --- acceptance criterion #1: Blonde + Fitzpatrick II -> {True Spring, True Summer, Light}
def test_candidate_set_blonde_fitz_ii():
    assert set(ruleouts.candidate_set("Blonde", "II")) == {TRUE_SPRING, TRUE_SUMMER, LIGHT}


# --- acceptance criterion #2: Blonde + Fitzpatrick VI -> empty (CONFLICTING_INPUTS)
def test_candidate_set_blonde_fitz_vi_is_empty():
    assert ruleouts.candidate_set("Blonde", "VI") == []


def test_candidate_set_order_is_canonical():
    cs = ruleouts.candidate_set("Black", "III")
    assert cs == [p for p in PALETTES if p in set(cs)]


def test_invalid_hair_raises():
    with pytest.raises(ruleouts.InvalidRuleInput):
        ruleouts.level1_candidates("Purple")


def test_rule_preview_flags_conflict():
    pv = ruleouts.rule_out_preview("Blonde", "VI")
    assert pv["conflicting"] is True and pv["candidate_set"] == []
