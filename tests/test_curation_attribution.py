"""CP1 attribution correction: source uncertainty, curator caution, excluded values and
missing source measurements must stay distinguishable, and an excluded value must never be
numerically available. Each negative case mutates one valid example in one way.
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"

SOURCE_UNCERTAINTY = "finding.measured.example.json"
CAUTION = "finding.measured_caution.example.json"
WITHHELD = "finding.measured_withheld.example.json"
MISSING = "finding.measured_missing.example.json"
INTERP = "finding.interpretation.example.json"
COMPARE = "comparison.example.json"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


@pytest.fixture
def finding(validator_for):
    return validator_for("finding.schema.json")


def _kinds(doc):
    return {n["kind"] for n in doc.get("curation_notes", [])}


# --- The four cases are valid and mutually distinct ------------------------------


def test_four_cases_validate(finding):
    for name in (SOURCE_UNCERTAINTY, CAUTION, WITHHELD, MISSING):
        finding.validate(_load(name))


def test_source_uncertainty_case():
    doc = _load(SOURCE_UNCERTAINTY)
    assert doc["value_status"] == "reported" and isinstance(doc["value"], float)
    assert doc["uncertainty"] and "curation_notes" not in doc


def test_curator_caution_case():
    doc = _load(CAUTION)
    assert doc["value_status"] == "reported" and isinstance(doc["value"], float)
    assert _kinds(doc) == {"caution"}
    assert doc["uncertainty"] is None  # caution text is NOT put in source uncertainty
    assert all(n["generated_by"] == "FlameGuard-SI" for n in doc["curation_notes"])


def test_excluded_case():
    doc = _load(WITHHELD)
    assert doc["value_status"] == "withheld" and doc["value"] is None
    assert "exclusion" in _kinds(doc)
    note = next(n for n in doc["curation_notes"] if n["kind"] == "exclusion")
    assert note["note"] and note["flag_ref"]["manifest_id"] and note["flag_ref"]["flag_id"]
    prov = doc["provenance"]
    assert prov["locator"] and prov["sources"] and prov["manifest_id"]  # source traceability kept
    assert doc["quantity"] and doc["unit"]  # still says WHAT was withheld


def test_missing_case():
    doc = _load(MISSING)
    assert doc["value_status"] == "not_reported" and doc["value"] is None
    assert "curation_notes" not in doc


# --- Invalid cross-field combinations are rejected -------------------------------


def _set(key, value):
    def m(doc):
        doc[key] = value

    return m


FLAG = {"manifest_id": "fixture-quality-flags-1", "flag_id": "F1"}


def _note(**fields):
    """A valid note (every note carries flag_ref), changed only by `fields`."""
    base = {"kind": "caution", "note": "x", "generated_by": "FlameGuard-SI", "flag_ref": FLAG}
    return {**base, **fields}


def _note_without_flag_ref(**fields):
    note = _note(**fields)
    del note["flag_ref"]
    return note

REJECT = [
    # Excluded values can never be numerically available
    ("withheld-with-value", WITHHELD, _set("value", 0.37)),
    (
        "exclusion-note-on-reported-value",
        CAUTION,
        _set("curation_notes", [_note(kind="exclusion", flag_ref=FLAG)]),
    ),
    (
        "exclusion-note-on-not-reported",
        MISSING,
        _set("curation_notes", [_note(kind="exclusion", flag_ref=FLAG)]),
    ),
    # Withheld needs a reason, attribution and a traceable flag
    ("withheld-without-notes", WITHHELD, lambda d: d.pop("curation_notes")),
    ("withheld-with-only-caution", WITHHELD, _set("curation_notes", [_note()])),
    (
        "exclusion-without-flag-ref",
        WITHHELD,
        _set("curation_notes", [_note_without_flag_ref(kind="exclusion")]),
    ),
    ("caution-without-flag-ref", CAUTION, _set("curation_notes", [_note_without_flag_ref()])),
    (
        "exclusion-empty-reason",
        WITHHELD,
        _set("curation_notes", [_note(kind="exclusion", note="", flag_ref=FLAG)]),
    ),
    ("note-attributed-to-nasa", CAUTION, _set("curation_notes", [_note(generated_by="NASA")])),
    (
        "note-unattributed",
        CAUTION,
        _set("curation_notes", [{"kind": "caution", "note": "x", "flag_ref": FLAG}]),
    ),
    ("note-unknown-kind", CAUTION, _set("curation_notes", [_note(kind="estimate")])),
    ("note-extra-key-value", CAUTION, _set("curation_notes", [_note(value=1.0)])),
    ("notes-empty-list", CAUTION, _set("curation_notes", [])),
    (
        "flag-ref-incomplete",
        CAUTION,
        _set("curation_notes", [_note(flag_ref={"manifest_id": "x"})]),
    ),
    # Withheld is a measured-only status; notes are measured-only
    ("withheld-interpretation", INTERP, _set("value_status", "withheld")),
    ("curation-notes-on-interpretation", INTERP, _set("curation_notes", [_note()])),
    # Provenance is not weakened for withheld values
    ("withheld-without-locator", WITHHELD, lambda d: d["provenance"].pop("locator")),
    ("withheld-without-sources", WITHHELD, lambda d: d["provenance"].update(sources=[])),
    ("withheld-without-manifest-id", WITHHELD, lambda d: d["provenance"].pop("manifest_id")),
]


@pytest.mark.parametrize(("case", "example", "mutate"), REJECT, ids=[c[0] for c in REJECT])
def test_invalid_combination_rejected(finding, case, example, mutate):
    doc = copy.deepcopy(_load(example))
    mutate(doc)
    with pytest.raises(ValidationError):
        finding.validate(doc)


def test_caution_may_coexist_with_source_uncertainty(finding):
    doc = copy.deepcopy(_load(CAUTION))
    doc["uncertainty"] = "FIXTURE: +/- 0.1 mm/s, as printed"
    finding.validate(doc)


# --- Withheld values never make a comparison valid ------------------------------


def _withheld_row(doc):
    row = copy.deepcopy(doc["rows"][0])
    row.update(
        finding_id="fixture-finding-measured-withheld-1", value=None, value_status="withheld"
    )
    return row


def test_withheld_row_is_allowed_only_as_non_comparable(validator_for):
    v = validator_for("comparison.schema.json")
    doc = copy.deepcopy(_load(COMPARE))
    doc["rows"].append(_withheld_row(doc))
    v.validate(doc)  # comparable: false, with reasons
    doc["comparable"] = True
    doc["non_comparable_reasons"] = []
    doc["rows"] = [doc["rows"][0], doc["rows"][-1]]
    with pytest.raises(ValidationError):
        v.validate(doc)


def test_withheld_row_cannot_carry_a_value(validator_for):
    doc = copy.deepcopy(_load(COMPARE))
    row = _withheld_row(doc)
    row["value"] = 0.37
    doc["rows"].append(row)
    with pytest.raises(ValidationError):
        validator_for("comparison.schema.json").validate(doc)


# --- Flag mapping (rule S10, schema side) ---------------------------------------
# The cross-file half of S10 (flag_ref resolves to a registered flag row, every flag row is
# covered, quotes verified against the registered source) needs the curated files: Member 3
# implements it in the derivation tool and tests/data/; Member 5 checks it independently.

FLAG_RANKING_USE = {"caution": "caution", "exclusion": "exclude"}


def _common():
    path = ROOT / "contracts" / "schemas" / "common.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))["$defs"]


def test_flag_mapping_is_exact():
    kind = _common()["curation_note"]["properties"]["kind"]
    assert kind["x-flag-ranking-use"] == FLAG_RANKING_USE
    assert set(kind["enum"]) == set(FLAG_RANKING_USE)


def test_not_available_is_neither_a_note_kind_nor_a_value_status():
    common = _common()
    kind = common["curation_note"]["properties"]["kind"]
    assert "not_available" not in kind["enum"]
    assert "not_available" not in kind["x-flag-ranking-use"].values()
    assert "not_available" not in common["value_status"]["enum"]


def test_not_available_cell_is_not_reported_without_a_note(finding):
    doc = copy.deepcopy(_load(MISSING))
    assert doc["value_status"] == "not_reported"
    assert doc["value"] is None
    assert "curation_notes" not in doc
    finding.validate(doc)
    doc["value_status"] = "not_available"  # the flags-file term must not pass through
    with pytest.raises(ValidationError):
        finding.validate(doc)


@pytest.mark.parametrize("term", ["exclude", "not_available", "withheld"])
def test_flag_terms_are_not_note_kinds(finding, term):
    doc = copy.deepcopy(_load(CAUTION))
    assert _kinds(doc) == {"caution"}
    doc["curation_notes"][0]["kind"] = term  # only the kind enum can reject this
    with pytest.raises(ValidationError):
        finding.validate(doc)
