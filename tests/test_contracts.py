import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from flameguard import CONTRACT_VERSION, SIMULATION_LABEL

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"

EXAMPLE_SCHEMA = {
    "finding.measured.example.json": "finding.schema.json",
    "finding.interpretation.example.json": "finding.schema.json",
    "investigation.example.json": "investigation.schema.json",
    "simulation_result.example.json": "simulation_result.schema.json",
    "health.example.json": "health.schema.json",
    "error.not_implemented.example.json": "error.schema.json",
}


def _load(name):
    return json.loads((EXAMPLES / name).read_text())


def test_every_example_is_mapped():
    assert {p.name for p in EXAMPLES.glob("*.json")} == set(EXAMPLE_SCHEMA)


@pytest.mark.parametrize(("example", "schema"), EXAMPLE_SCHEMA.items())
def test_example_validates(validator_for, example, schema):
    validator_for(schema).validate(_load(example))


@pytest.mark.parametrize(
    "example", [e for e in EXAMPLE_SCHEMA if "health" not in e and "error" not in e]
)
def test_scientific_examples_are_marked_fixture(example):
    assert _load(example)["fixture"] is True


def test_measured_without_sources_is_rejected(validator_for):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    bad["provenance"]["sources"] = []
    with pytest.raises(ValidationError):
        validator_for("finding.schema.json").validate(bad)


def test_interpretation_must_be_attributed_to_flameguard(validator_for):
    bad = copy.deepcopy(_load("finding.interpretation.example.json"))
    bad["provenance"]["generated_by"] = "NASA"
    with pytest.raises(ValidationError):
        validator_for("finding.schema.json").validate(bad)


def test_simulation_label_is_required(validator_for):
    bad = copy.deepcopy(_load("simulation_result.example.json"))
    bad["label"] = "Simulated flame"
    with pytest.raises(ValidationError):
        validator_for("simulation_result.schema.json").validate(bad)


def test_simulation_cannot_claim_measured(validator_for):
    bad = copy.deepcopy(_load("simulation_result.example.json"))
    bad["evidence_class"] = "measured"
    with pytest.raises(ValidationError):
        validator_for("simulation_result.schema.json").validate(bad)


def test_label_and_version_constants_match_contract():
    sim = json.loads((ROOT / "contracts/schemas/simulation_result.schema.json").read_text())
    assert sim["properties"]["label"]["const"] == SIMULATION_LABEL
    assert _load("health.example.json")["contract_version"] == CONTRACT_VERSION
    assert (
        f"**Spec version:** {CONTRACT_VERSION}" in (ROOT / "FLAMEGUARD_MASTER_SPEC.md").read_text()
    )
