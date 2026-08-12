from app.palettes import extract_palettes, is_valid_flow, neighbours, canonical_ground_truth
from app.scoring import score_case


def test_extract_simple():
    assert extract_palettes("True Autumn") == ["True Autumn"]


def test_extract_boundary_deep_winter():
    # "True Winter" must match before "Winter"; both palettes captured in order
    got = extract_palettes("Deep or True Winter moving towards Deep. It is a very close call.")
    assert got == ["Deep", "True Winter"]


def test_extract_boundary_summer_cool():
    assert extract_palettes("True Summer, moving slightly toward Cool") == ["True Summer", "Cool"]


def test_extract_muted_summer():
    assert extract_palettes("Muted or True Summer Moving Towards Muted") == ["Muted", "True Summer"]


def test_valid_flow():
    assert is_valid_flow("Cool", "Winter")
    assert is_valid_flow("Light", "Summer")
    assert not is_valid_flow("Warm", "Winter")


def test_neighbours_shared_season():
    assert "Cool" in neighbours("True Winter")   # both Winter flows
    assert "Deep" in neighbours("True Autumn")


def test_score_exact():
    m, kind, primary, acc = score_case("True Autumn", "True Autumn")
    assert m and kind == "exact" and primary == "True Autumn"


def test_score_boundary_named():
    # Carol named Deep OR True Winter -> predicting the neighbour counts as boundary
    m, kind, primary, acc = score_case("True Winter", "Deep or True Winter moving towards Deep")
    assert m and kind == "boundary" and primary == "Deep" and set(acc) == {"Deep", "True Winter"}


def test_score_miss():
    m, kind, primary, acc = score_case("Bright", "True Autumn")
    assert (not m) and kind == "miss"


def test_score_error_when_none():
    m, kind, primary, acc = score_case(None, "True Autumn")
    assert (not m) and kind == "error"


def test_canonical_ground_truth():
    g = canonical_ground_truth("True Summer, moving slightly toward Cool")
    assert g["primary"] == "True Summer" and "Cool" in g["accepted"]
