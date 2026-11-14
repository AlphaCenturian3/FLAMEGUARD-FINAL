"""Numerical comparison is refused unless evidence is scientifically comparable."""

import pytest

from flameguard.research.comparability import (
    IncomparableEvidenceError,
    check_comparability,
    numeric_difference,
)


def test_matching_measured_records_are_comparable(fx):
    result = check_comparability([fx("fixture-a-1"), fx("fixture-a-2")])
    assert result.comparable, result.reasons
    assert (result.quantity, result.unit) == ("flame_spread_rate", "mm/s")
    assert numeric_difference(fx("fixture-a-1"), fx("fixture-a-2")) == pytest.approx(0.5)


def test_different_conditions_block_comparison(fx):
    result = check_comparability([fx("fixture-a-1"), fx("fixture-b-1")])
    assert not result.comparable
    text = " | ".join(result.reasons)
    assert "gravity_environment' differs" in text
    assert "oxygen_mole_fraction' is reported for some records and missing" in text
    with pytest.raises(IncomparableEvidenceError) as err:
        numeric_difference(fx("fixture-a-1"), fx("fixture-b-1"))
    assert err.value.reasons == result.reasons


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("unit", "cm/s", "units are never converted"),
        ("conditions.fuel_or_material", "fixture-material-z", "'fuel_or_material' differs"),
        ("conditions.sample_geometry", "fixture-thick-slab", "'sample_geometry' differs"),
        ("conditions.pressure_kpa", 70.0, "'pressure_kpa' differs"),
        ("conditions.oxygen_mole_fraction", 0.30, "'oxygen_mole_fraction' differs"),
        ("conditions.gravity_environment", "partial_gravity", "'gravity_environment' differs"),
        ("conditions.flow_velocity_mm_s", 100, "'flow_velocity_mm_s' differs"),
        ("conditions.flow_configuration", "opposed", "'flow_configuration' differs"),
        ("conditions.diluent", "helium", "'diluent' differs"),
    ],
)
def test_each_inconsistent_condition_blocks_comparison(fx, field, value, expected):
    """Kickoff requirement: no cross-comparison across inconsistent units, fuel, pressure,
    O2, gravity or flow without an explicit comparability rationale (none is accepted)."""
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    assert check_comparability([a, b]).comparable
    target = b
    *path, key = field.split(".")
    for part in path:
        target = target[part]
    target[key] = value
    result = check_comparability([a, b])
    assert not result.comparable
    assert any(expected in r for r in result.reasons), result.reasons
    with pytest.raises(IncomparableEvidenceError):
        numeric_difference(a, b)


def test_missing_value_blocks_comparison(fx):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    b.update(value=None, value_status="not_reported")
    assert any("not_reported" in r for r in check_comparability([a, b]).reasons)


def test_units_are_never_converted(fx):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    b["unit"] = "cm/s"
    assert any("never converted" in r for r in check_comparability([a, b]).reasons)


def test_different_quantities_are_not_compared(fx):
    a, b = fx("fixture-b-1"), fx("fixture-b-2")
    reasons = check_comparability([a, b]).reasons
    assert any("different quantities" in r for r in reasons)


def test_reported_and_interpreted_records_are_not_compared_numerically(fx):
    reasons = check_comparability([fx("fixture-a-1"), fx("fixture-c-1")]).reasons
    assert any("only measured evidence" in r for r in reasons)
    assert any("qualitative record" in r for r in reasons)


def test_fixture_and_real_records_are_never_mixed(fx):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    b.pop("fixture")
    assert any("fixture" in r for r in check_comparability([a, b]).reasons)


def test_single_record_is_not_a_comparison(fx):
    assert not check_comparability([fx("fixture-a-1")]).comparable


def test_strict_mode_requires_core_conditions_to_be_known(fx):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    for r in (a, b):
        r["conditions"]["oxygen_mole_fraction"] = None
    strict = check_comparability([a, b])
    assert not strict.comparable
    assert any("not reported for any record" in r for r in strict.reasons)
    # Contract rule S5 alone accepts a key that is null for every row.
    assert check_comparability([a, b], strict=False).comparable
