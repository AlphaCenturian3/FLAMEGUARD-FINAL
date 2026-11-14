"""Regression tests for schema loopholes found in the CP1 contract review.

Each case mutates a valid example into something the contract must reject.
Cases marked ALREADY_CLOSED were rejected at PR #1 head 1e34e3e and are kept as guards;
every other case was accepted at 1e34e3e (a confirmed loophole) and is closed by this change.
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _set(path, value):
    def mutate(doc):
        *parents, last = path
        target = doc
        for key in parents:
            target = target[key]
        target[last] = value

    return mutate


def _delete(path):
    def mutate(doc):
        *parents, last = path
        target = doc
        for key in parents:
            target = target[key]
        del target[last]

    return mutate


MEASURED = "finding.measured.example.json"
MISSING = "finding.measured_missing.example.json"
INTERP = "finding.interpretation.example.json"
COMPARE = "comparison.example.json"
RANKING = "ranking.example.json"
ANSWER = "assistant_answer.example.json"
SIM = "simulation_result.example.json"
INVEST = "investigation.example.json"

ALREADY_CLOSED = {
    "finding-interp-not-attributed",
    "conditions-oxygen-above-one",
    "source-date-wrong-shape",
    "source-empty-locator",
    "ranking-bad-context",
    "ranking-extra-simulation-key",
}

# (case id, example, schema, mutation)
CASES = [
    # Comparison rows
    (
        "compare-row-no-evidence-class",
        COMPARE,
        "comparison",
        _delete(["rows", 0, "evidence_class"]),
    ),
    ("compare-row-reported-null", COMPARE, "comparison", _set(["rows", 0, "value"], None)),
    ("compare-row-not-reported-filled", COMPARE, "comparison", _set(["rows", 1, "value"], 0.0)),
    ("compare-comparable-with-missing", COMPARE, "comparison", _set(["comparable"], True)),
    ("compare-unknown-quantity", COMPARE, "comparison", _set(["quantity"], "made_up_quantity")),
    ("compare-wrong-unit", COMPARE, "comparison", _set(["unit"], "cm/s")),
    ("compare-row-bad-id", COMPARE, "comparison", _set(["rows", 0, "finding_id"], "Has Spaces")),
    # Findings: units, values and quantities
    ("finding-unknown-quantity", MEASURED, "finding", _set(["quantity"], "made_up_quantity")),
    ("finding-wrong-unit", MEASURED, "finding", _set(["unit"], "cm/s")),
    ("finding-numeric-as-string", MEASURED, "finding", _set(["value"], "1.0")),
    ("finding-negative-spread-rate", MEASURED, "finding", _set(["value"], -1.0)),
    ("finding-unit-without-quantity", INTERP, "finding", _set(["unit"], "mm/s")),
    ("finding-missing-without-unit", MISSING, "finding", _set(["unit"], None)),
    # Findings: simulation data riding on measured or interpretation findings
    (
        "finding-extra-top-level-label",
        MEASURED,
        "finding",
        _set(["label"], "Fluid and thermal transport model. No combustion chemistry."),
    ),
    ("finding-measured-with-model", MEASURED, "finding", _set(["provenance", "model"], "solver")),
    ("finding-interp-with-model", INTERP, "finding", _set(["provenance", "model"], "solver")),
    ("finding-interp-not-attributed", INTERP, "finding", _delete(["provenance", "generated_by"])),
    # Conditions
    ("conditions-key-omitted", MEASURED, "finding", _delete(["conditions", "pressure_kpa"])),
    ("conditions-empty-string", MEASURED, "finding", _set(["conditions", "diluent"], "")),
    (
        "conditions-oxygen-above-one",
        MEASURED,
        "finding",
        _set(["conditions", "oxygen_mole_fraction"], 21),
    ),
    # Sources
    ("source-url-not-http", MEASURED, "finding", _set(["provenance", "sources", 0, "url"], "x")),
    ("source-empty-quote", MEASURED, "finding", _set(["provenance", "sources", 0, "quote"], "")),
    (
        "source-date-wrong-shape",
        MEASURED,
        "finding",
        _set(["provenance", "sources", 0, "retrieved"], "2026-11-14T10:00:00Z"),
    ),
    ("source-empty-locator", MEASURED, "finding", _set(["provenance", "locator"], "")),
    # Ranking
    ("ranking-no-criterion-scores", RANKING, "ranking", _set(["items", 0, "criterion_scores"], [])),
    (
        "ranking-positive-score-no-inputs",
        RANKING,
        "ranking",
        _set(["items", 0, "criterion_scores", 0, "inputs"], []),
    ),
    ("ranking-bad-context", RANKING, "ranking", _set(["context"], "mars")),
    (
        "ranking-extra-simulation-key",
        RANKING,
        "ranking",
        _set(["items", 0, "simulation_id"], "fixture-sim-1"),
    ),
    # Assistant
    ("answer-empty", ANSWER, "assistant_answer", _set(["answer"], "")),
    (
        "answer-citation-bad-id",
        ANSWER,
        "assistant_answer",
        _set(["citations", 0, "finding_id"], ""),
    ),
    # Investigation
    ("investigation-extra-key", INVEST, "investigation", _set(["score"], 0.9)),
    ("investigation-bad-dataset-id", INVEST, "investigation", _set(["datasets"], ["Bad Id"])),
    # Simulation result
    (
        "simulation-carries-investigation-value",
        SIM,
        "simulation_result",
        _set(["measured_value"], 1.0),
    ),
]


@pytest.mark.parametrize(("case", "example", "schema", "mutate"), CASES, ids=[c[0] for c in CASES])
def test_loophole_is_closed(validator_for, case, example, schema, mutate):
    doc = copy.deepcopy(_load(example))
    mutate(doc)
    with pytest.raises(ValidationError):
        validator_for(f"{schema}.schema.json").validate(doc)


def test_unformatted_validators_still_reject_bad_dates():
    """Frontend or other validators may skip `format`; the date rule must not depend on it."""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    schemas = ROOT / "contracts" / "schemas"
    registry = Registry().with_resources(
        (
            json.loads(p.read_text(encoding="utf-8"))["$id"],
            Resource.from_contents(json.loads(p.read_text(encoding="utf-8"))),
        )
        for p in schemas.glob("*.schema.json")
    )
    v = Draft202012Validator(
        json.loads((schemas / "finding.schema.json").read_text(encoding="utf-8")), registry=registry
    )  # no format_checker
    doc = copy.deepcopy(_load(MEASURED))
    doc["provenance"]["sources"][0]["retrieved"] = "yesterday"
    with pytest.raises(ValidationError):
        v.validate(doc)


def test_already_closed_names_are_real_cases():
    assert ALREADY_CLOSED <= {c[0] for c in CASES}


# --- P0 additions (draft PR #5): environment tags and limitations -------------

P0_CASES = [
    (
        "measured-with-environment-tag",
        MEASURED,
        "finding",
        _set(["relevant_environments"], ["lunar_base"]),
    ),
    ("measured-with-limitations", MEASURED, "finding", _set(["limitations"], ["x"])),
    ("interp-without-limitations", INTERP, "finding", _delete(["limitations"])),
    ("interp-empty-limitations", INTERP, "finding", _set(["limitations"], [])),
    ("interp-blank-limitation", INTERP, "finding", _set(["limitations"], [""])),
    ("interp-unknown-environment", INTERP, "finding", _set(["relevant_environments"], ["moon"])),
    ("interp-empty-environments", INTERP, "finding", _set(["relevant_environments"], [])),
    ("answer-without-limitations", ANSWER, "assistant_answer", _delete(["limitations"])),
    ("answer-fallback-empty-limitations", ANSWER, "assistant_answer", _set(["limitations"], [])),
]


@pytest.mark.parametrize(
    ("case", "example", "schema", "mutate"), P0_CASES, ids=[c[0] for c in P0_CASES]
)
def test_p0_addition_rule_holds(validator_for, case, example, schema, mutate):
    doc = copy.deepcopy(_load(example))
    mutate(doc)
    with pytest.raises(ValidationError):
        validator_for(f"{schema}.schema.json").validate(doc)


def test_no_evidence_answer_may_have_no_limitations(validator_for):
    doc = copy.deepcopy(_load(ANSWER))
    doc.update(mode="no_evidence", citations=[], limitations=[])
    validator_for("assistant_answer.schema.json").validate(doc)


def test_interpretation_environment_tag_is_optional(validator_for):
    doc = copy.deepcopy(_load(INTERP))
    del doc["relevant_environments"]
    validator_for("finding.schema.json").validate(doc)


# --- Curation notes and exclusions (CP1 amendment) -----------------------------

EXCLUDED = "finding.measured_excluded.example.json"
CAUTION_NOTE = {
    "kind": "caution",
    "text": "FIXTURE caution",
    "generated_by": "FlameGuard-SI",
    "flag_ref": {"manifest_id": "fixture-dataset-1.flags", "flag_id": "FIXTURE-F009"},
    "source": {
        "title": "FIXTURE PLACEHOLDER SOURCE",
        "url": "https://example.invalid/fixture",
        "quote": "FIXTURE QUOTE PLACEHOLDER",
        "retrieved": "2026-11-14",
    },
}

CURATION_CASES = [
    ("note-attributed-to-nasa", EXCLUDED, _set(["curation_notes", 0, "generated_by"], "NASA")),
    ("note-without-attribution", EXCLUDED, _delete(["curation_notes", 0, "generated_by"])),
    ("note-without-source", EXCLUDED, _delete(["curation_notes", 0, "source"])),
    ("note-source-null-quote", EXCLUDED, _set(["curation_notes", 0, "source", "quote"], None)),
    ("note-without-flag-ref", EXCLUDED, _delete(["curation_notes", 0, "flag_ref"])),
    (
        "note-bad-flag-manifest-id",
        EXCLUDED,
        _set(["curation_notes", 0, "flag_ref", "manifest_id"], "Bad Id"),
    ),
    ("note-unknown-kind", EXCLUDED, _set(["curation_notes", 0, "kind"], "opinion")),
    ("note-carries-value", EXCLUDED, _set(["curation_notes", 0, "value"], 0.37)),
    ("note-empty-text", EXCLUDED, _set(["curation_notes", 0, "text"], "")),
    ("excluded-with-value", EXCLUDED, _set(["value"], 0.37)),
    ("excluded-without-notes", EXCLUDED, _delete(["curation_notes"])),
    ("excluded-with-caution-only", EXCLUDED, _set(["curation_notes"], [CAUTION_NOTE])),
    ("exclusion-note-on-reported-value", EXCLUDED, _set(["value_status"], "reported")),
    ("empty-curation-notes", MEASURED, _set(["curation_notes"], [])),
    ("interp-with-curation-notes", INTERP, _set(["curation_notes"], [CAUTION_NOTE])),
    ("interp-excluded", INTERP, _set(["value_status"], "excluded")),
]


@pytest.mark.parametrize(
    ("case", "example", "mutate"), CURATION_CASES, ids=[c[0] for c in CURATION_CASES]
)
def test_curation_rule_holds(validator_for, case, example, mutate):
    doc = copy.deepcopy(_load(example))
    mutate(doc)
    with pytest.raises(ValidationError):
        validator_for("finding.schema.json").validate(doc)


def test_exclusion_note_requires_excluded_status(validator_for):
    """A reported number carrying an exclusion note is rejected by the note rule itself."""
    doc = copy.deepcopy(_load(EXCLUDED))
    doc.update(value_status="reported", value=0.37)
    with pytest.raises(ValidationError):
        validator_for("finding.schema.json").validate(doc)


def test_caution_note_on_reported_measured_value_is_allowed(validator_for):
    doc = copy.deepcopy(_load(MEASURED))
    doc["curation_notes"] = [CAUTION_NOTE]
    validator_for("finding.schema.json").validate(doc)
    assert doc["uncertainty"] is None  # curation text never goes into uncertainty


def test_excluded_row_makes_comparison_non_comparable(validator_for):
    v = validator_for("comparison.schema.json")
    doc = copy.deepcopy(_load(COMPARE))
    doc["rows"][0].update(value=None, value_status="excluded")
    v.validate(doc)  # allowed while comparable is false
    doc["comparable"] = True
    doc["non_comparable_reasons"] = []
    with pytest.raises(ValidationError):
        v.validate(doc)
