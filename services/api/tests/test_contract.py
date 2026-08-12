"""Output-contract hard-constraint validation (§5.5)."""
from __future__ import annotations

from services.api.domain.contract import validate_output_contract


CS = ["True Spring", "True Summer", "Light"]


def test_valid_result_passes():
    c = validate_output_contract(undertone="Cool", home_season="Summer",
                                 flow_result="True Summer", candidate_set=CS)
    assert c.ok and c.violations == []


def test_flow_outside_candidate_set_fails():
    c = validate_output_contract(undertone="Cool", home_season="Winter",
                                 flow_result="True Winter", candidate_set=CS)
    assert not c.ok
    assert any("candidate_set" in v for v in c.violations)


def test_flow_invalid_for_home_season_fails():
    # Deep is not a valid flow of Summer.
    c = validate_output_contract(undertone="Cool", home_season="Summer",
                                 flow_result="Deep", candidate_set=["Deep", "True Summer"])
    assert not c.ok
    assert any("valid flow" in v for v in c.violations)


def test_undertone_inconsistent_with_home_season_fails():
    # Summer is Cool; asserting Warm is inconsistent.
    c = validate_output_contract(undertone="Warm", home_season="Summer",
                                 flow_result="True Summer", candidate_set=CS)
    assert not c.ok
    assert any("inconsistent" in v for v in c.violations)


def test_spring_is_warm():
    c = validate_output_contract(undertone="Warm", home_season="Spring",
                                 flow_result="True Spring", candidate_set=CS)
    assert c.ok
