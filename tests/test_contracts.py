import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from flameguard import CONTRACT_VERSION, SIMULATION_LABEL

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"
SCHEMAS = ROOT / "contracts" / "schemas"
VOCAB = json.loads((ROOT / "contracts" / "vocabulary.json").read_text())["quantities"]

EXAMPLE_SCHEMA = {
    "finding.measured.example.json": "finding.schema.json",
    "finding.measured_missing.example.json": "finding.schema.json",
    "finding.interpretation.example.json": "finding.schema.json",
    "investigation.example.json": "investigation.schema.json",
    "investigation_list.example.json": "list_envelope.schema.json",
    "comparison.example.json": "comparison.schema.json",
    "ranking.example.json": "ranking.schema.json",
    "assistant_request.example.json": "assistant_request.schema.json",
    "assistant_answer.example.json": "assistant_answer.schema.json",
    "simulation_result.example.json": "simulation_result.schema.json",
    "health.example.json": "health.schema.json",
    "error.not_implemented.example.json": "error.schema.json",
}
NON_SCIENTIFIC = {
    "health.example.json",
    "error.not_implemented.example.json",
    "assistant_request.example.json",
    "investigation_list.example.json",
}


def _load(name):
    return json.loads((EXAMPLES / name).read_text())


def _invalid(validator, doc):
    with pytest.raises(ValidationError):
        validator.validate(doc)


def test_every_example_is_mapped():
    assert {p.name for p in EXAMPLES.glob("*.json")} == set(EXAMPLE_SCHEMA)


def test_every_schema_has_an_example():
    assert {p.name for p in SCHEMAS.glob("*.schema.json")} - set(EXAMPLE_SCHEMA.values()) == {
        "source.schema.json",  # embedded in finding/investigation examples
        "conditions.schema.json",  # embedded in finding/comparison examples
        "data_manifest.schema.json",  # exercised by data/manifest.json
    }


@pytest.mark.parametrize(("example", "schema"), EXAMPLE_SCHEMA.items())
def test_example_validates(validator_for, example, schema):
    validator_for(schema).validate(_load(example))


@pytest.mark.parametrize("example", sorted(set(EXAMPLE_SCHEMA) - NON_SCIENTIFIC))
def test_scientific_examples_are_marked_fixture(example):
    assert _load(example)["fixture"] is True


@pytest.mark.parametrize("example", sorted(set(EXAMPLE_SCHEMA)))
def test_examples_carry_current_contract_version(example):
    doc = _load(example)
    if "contract_version" in doc:
        assert doc["contract_version"] == CONTRACT_VERSION


# --- Finding rules -------------------------------------------------------------


@pytest.fixture
def finding(validator_for):
    return validator_for("finding.schema.json")


def test_simulation_is_not_a_finding(finding):
    bad = copy.deepcopy(_load("finding.interpretation.example.json"))
    bad["evidence_class"] = "illustrative_simulation"
    _invalid(finding, bad)


def test_measured_without_sources_is_rejected(finding):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    bad["provenance"]["sources"] = []
    _invalid(finding, bad)


def test_measured_without_locator_is_rejected(finding):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    del bad["provenance"]["locator"]
    _invalid(finding, bad)


def test_bad_retrieval_date_is_rejected(finding):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    bad["provenance"]["sources"][0]["retrieved"] = "yesterday"
    _invalid(finding, bad)


def test_numeric_value_needs_quantity_and_unit(finding):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    bad["unit"] = None
    _invalid(finding, bad)


def test_missing_value_cannot_be_filled(finding):
    bad = copy.deepcopy(_load("finding.measured_missing.example.json"))
    bad["value"] = 0.0  # gap-filling a not_reported value
    _invalid(finding, bad)


def test_reported_value_cannot_be_null(finding):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    bad["value"] = None
    _invalid(finding, bad)


def test_conditions_reject_unknown_keys(finding):
    bad = copy.deepcopy(_load("finding.measured.example.json"))
    bad["conditions"]["pressure_atm"] = 1
    _invalid(finding, bad)


def test_interpretation_must_be_attributed_to_flameguard(finding):
    bad = copy.deepcopy(_load("finding.interpretation.example.json"))
    bad["provenance"]["generated_by"] = "NASA"
    _invalid(finding, bad)


@pytest.mark.parametrize(
    "example", ["finding.measured.example.json", "finding.measured_missing.example.json"]
)
def test_example_quantities_and_units_match_vocabulary(example):
    doc = _load(example)
    assert doc["quantity"] in VOCAB
    assert doc["unit"] == VOCAB[doc["quantity"]]["unit"]


def test_comparison_example_quantity_matches_vocabulary():
    doc = _load("comparison.example.json")
    assert doc["unit"] == VOCAB[doc["quantity"]]["unit"]


# --- Ranking, comparison, assistant, simulation --------------------------------


def test_ranking_scores_are_weighted_sums():
    doc = _load("ranking.example.json")
    weights = {c["id"]: c["weight"] for c in doc["criteria"]}
    assert sum(weights.values()) == pytest.approx(1.0)
    for item in doc["items"]:
        total = sum(weights[c["criterion_id"]] * c["score"] for c in item["criterion_scores"])
        assert item["score"] == pytest.approx(total, abs=1e-9)


def test_ranking_rejects_simulation_inputs(validator_for):
    bad = copy.deepcopy(_load("ranking.example.json"))
    bad["items"][0]["criterion_scores"][0]["inputs"][0]["evidence_class"] = (
        "illustrative_simulation"
    )
    _invalid(validator_for("ranking.schema.json"), bad)


def test_comparison_rejects_simulation_rows(validator_for):
    bad = copy.deepcopy(_load("comparison.example.json"))
    bad["rows"][0]["evidence_class"] = "illustrative_simulation"
    _invalid(validator_for("comparison.schema.json"), bad)


def test_non_comparable_needs_reasons(validator_for):
    bad = copy.deepcopy(_load("comparison.example.json"))
    bad["non_comparable_reasons"] = []
    _invalid(validator_for("comparison.schema.json"), bad)


def test_assistant_rejects_simulation_citations(validator_for):
    bad = copy.deepcopy(_load("assistant_answer.example.json"))
    bad["citations"][0]["evidence_class"] = "illustrative_simulation"
    _invalid(validator_for("assistant_answer.schema.json"), bad)


def test_assistant_answer_needs_citations_unless_no_evidence(validator_for):
    v = validator_for("assistant_answer.schema.json")
    bad = copy.deepcopy(_load("assistant_answer.example.json"))
    bad["citations"] = []
    _invalid(v, bad)
    bad["mode"] = "no_evidence"
    v.validate(bad)


def test_simulation_label_is_required(validator_for):
    bad = copy.deepcopy(_load("simulation_result.example.json"))
    bad["label"] = "Simulated flame"
    _invalid(validator_for("simulation_result.schema.json"), bad)


def test_simulation_cannot_claim_measured_or_validated(validator_for):
    v = validator_for("simulation_result.schema.json")
    bad = copy.deepcopy(_load("simulation_result.example.json"))
    bad["evidence_class"] = "measured"
    _invalid(v, bad)
    bad = copy.deepcopy(_load("simulation_result.example.json"))
    bad["verification_status"] = "validated_against_measured"
    _invalid(v, bad)


def test_label_and_version_constants_match_contract():
    sim = json.loads((SCHEMAS / "simulation_result.schema.json").read_text())
    assert sim["properties"]["label"]["const"] == SIMULATION_LABEL
    spec = (ROOT / "FLAMEGUARD_MASTER_SPEC.md").read_text()
    assert f"**Spec version:** {CONTRACT_VERSION}" in spec
    vocab = json.loads((ROOT / "contracts" / "vocabulary.json").read_text())
    assert vocab["vocabulary_version"] == CONTRACT_VERSION
