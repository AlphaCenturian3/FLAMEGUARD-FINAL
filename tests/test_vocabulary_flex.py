"""Regression tests for the D5/C4 FLEX vocabulary extension (contract v0.2.1, proposed).

The generic checks (vocabulary == quantity_rules, versions agree) live in test_contracts.py.
These pin the FLEX-specific decisions so they cannot drift silently.
"""

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VOCAB = json.loads((ROOT / "contracts" / "vocabulary.json").read_text(encoding="utf-8"))
Q = VOCAB["quantities"]
FLEX = {
    "initial_droplet_diameter": "mm",
    "visible_flame_extinction_diameter": "mm",
    "burning_rate_constant": "mm2/s",
    "burn_time": "s",
}


def test_flex_quantities_present_with_units_and_non_negative_bounds():
    for key, unit in FLEX.items():
        assert Q[key]["unit"] == unit
        assert Q[key]["minimum"] == 0
        assert "maximum" not in Q[key]


def test_flame_spread_rate_unchanged_and_distinct_from_burning_rate_constant():
    assert Q["flame_spread_rate"] == {
        "unit": "mm/s",
        "description": "Rate of flame front advance over a solid fuel surface.",
        "minimum": 0,
    }
    assert Q["burning_rate_constant"]["unit"] != Q["flame_spread_rate"]["unit"]
    assert "Not a flame spread rate" in Q["burning_rate_constant"]["description"]


def test_existing_quantities_kept_in_order():
    assert list(Q)[:5] == [
        "flame_spread_rate",
        "extinction_oxygen_mole_fraction",
        "ignition_delay",
        "flame_length",
        "flame_temperature",
    ]


@pytest.fixture
def rules(validator_for):
    return validator_for("quantity_rules.schema.json")


@pytest.mark.parametrize(("key", "unit"), FLEX.items())
def test_flex_value_accepted_and_null_allowed(rules, key, unit):
    rules.validate({"quantity": key, "unit": unit, "value": 1.5})
    rules.validate({"quantity": key, "unit": unit, "value": None})


@pytest.mark.parametrize(
    "bad",
    [
        {"quantity": "burning_rate_constant", "unit": "mm/s", "value": 0.6},
        {"quantity": "flame_spread_rate", "unit": "mm2/s", "value": 0.6},
        {"quantity": "burning_rate_constant", "unit": "mm2/s", "value": -0.1},
        {"quantity": "burn_time", "unit": "s", "value": "13.6"},
        {"quantity": "initial_droplet_diameter", "unit": "cm", "value": 0.2},
        {"quantity": "visible_flame_extinction_diameter", "unit": "m", "value": 0.0009},
    ],
)
def test_flex_misuse_rejected(rules, bad):
    assert not rules.is_valid(bad)


def test_measured_finding_with_burning_rate_constant_validates(validator_for):
    doc = json.loads(
        (ROOT / "contracts/examples/finding.measured.example.json").read_text(encoding="utf-8")
    )
    doc = copy.deepcopy(doc)
    doc.update(quantity="burning_rate_constant", unit="mm2/s", value=0.6)
    validator_for("finding.schema.json").validate(doc)
    doc["unit"] = "mm/s"
    assert not validator_for("finding.schema.json").is_valid(doc)
