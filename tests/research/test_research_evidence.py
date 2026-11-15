"""Evidence structure: citations, missing data, measured vs reported vs interpreted."""

import pytest
from research.common import CONDITION_KEYS
from research.evidence import (
    contract_evidence_class,
    index_records,
    missing_fields,
    validate_evidence,
)


def test_every_real_record_is_valid_and_cited(real_evidence):
    assert real_evidence, "expected the verified research records"
    for rec in real_evidence:
        assert validate_evidence(rec) == [], rec["id"]
        assert rec["sources"], rec["id"]
        for src in rec["sources"]:
            assert src["url"].startswith("https://")
            assert src["retrieved"] == "2026-11-14"
        assert any(s["quote"] for s in rec["sources"]), rec["id"]


def test_no_real_record_claims_a_measurement(real_evidence):
    # Nothing test-level has been imported yet; every real record is a quoted statement.
    for rec in real_evidence:
        assert rec["evidence_category"] == "reported"
        assert rec["quantity"] is None and rec["value"] is None and rec["unit"] is None
        assert "fixture" not in rec


def test_contract_mapping_does_not_upgrade_reported_to_measured():
    assert contract_evidence_class("measured") == "measured"
    assert contract_evidence_class("interpreted") == "interpretation"
    assert contract_evidence_class("reported") is None


def test_missing_fields_are_listed_explicitly(fx):
    rec = fx("fixture-b-1")
    missing = missing_fields(rec)
    assert "test_id" in missing and "doi" in missing and "uncertainty" in missing
    assert "conditions.oxygen_mole_fraction" in missing
    assert "conditions.pressure_kpa" not in missing
    assert "value" in missing_fields(fx("fixture-b-2"))


def test_missing_value_is_never_filled(fx):
    rec = fx("fixture-b-2")
    assert validate_evidence(rec) == []
    rec["value"] = 0.0  # filling a gap
    assert any("never filled in" in e for e in validate_evidence(rec))


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda r: r.pop("manifest_id"), "needs 'manifest_id'"),
        (lambda r: r.update(locator=""), "needs 'locator'"),
        (lambda r: r.update(sources=[]), "at least one source"),
        (lambda r: r.update(unit="cm/s"), "must use unit 'mm/s'"),
        (lambda r: r.update(quantity="burn_rate"), "unknown quantity"),
        (lambda r: r.update(value="1.0"), "must be a number"),
        (lambda r: r["conditions"].pop("pressure_kpa"), "every key"),
        (lambda r: r["conditions"].update(gravity_g=0.16), "unknown condition keys"),
        (lambda r: r["conditions"].update(oxygen_mole_fraction=21), "within 0..1"),
        (lambda r: r.pop("extrapolation_warning"), "extrapolation_warning"),
        (lambda r: r.update(limitations=[]), "limitation"),
        (lambda r: r["sources"][0].update(url="nasa.gov"), "http(s)"),
        (lambda r: r["sources"][0].update(retrieved="yesterday"), "YYYY-MM-DD"),
        (lambda r: r.update(doi="doi:abc"), "doi"),
        (lambda r: r.update(statement="According to NASA this is safe."), "banned phrase"),
        (lambda r: r.update(evidence_category="illustrative_simulation"), "evidence_category"),
    ],
)
def test_invalid_measured_records_are_rejected(fx, mutate, expected):
    rec = fx("fixture-a-1")
    mutate(rec)
    errors = validate_evidence(rec)
    assert any(expected in e for e in errors), errors


def test_reported_records_cannot_carry_numbers(fx):
    rec = fx("fixture-d-1")
    assert validate_evidence(rec) == []
    rec.update(quantity="flame_spread_rate", unit="mm/s", value=3.0, value_status="reported")
    assert any("qualitative" in e for e in validate_evidence(rec))


def test_reported_records_need_an_exact_quote_and_strength(fx):
    rec = fx("fixture-d-1")
    rec["sources"][0]["quote"] = None
    rec.pop("source_claim_strength")
    errors = validate_evidence(rec)
    assert any("exact quote" in e for e in errors)
    assert any("source_claim_strength" in e for e in errors)


def test_interpreted_records_need_derivation_and_method(fx):
    rec = fx("fixture-c-1")
    assert validate_evidence(rec) == []
    rec.update(derived_from=[], method="", generated_by="NASA")
    errors = validate_evidence(rec)
    assert any("derived_from" in e for e in errors)
    assert any("method" in e for e in errors)
    assert any("generated_by" in e for e in errors)


def _excluded_fixture(fx):
    rec = fx("fixture-a-1")
    rec.update(value=None, value_status="excluded")
    rec["curation_notes"] = [
        {
            "kind": "exclusion",
            "note": "FIXTURE exclusion reason.",
            "generated_by": "FlameGuard-SI",
            "flag_ref": {"manifest_id": "fixture-quality-flags-1", "flag_id": "F1"},
            "source": {
                "title": "FIXTURE source",
                "url": "https://example.invalid/fixture",
                "page": 1,
                "quote": "FIXTURE source quote.",
                "retrieved": "2026-11-14",
                "archive_id": None,
            },
        }
    ]
    return rec


def test_excluded_value_keeps_measured_provenance_and_attribution(fx):
    rec = _excluded_fixture(fx)
    assert validate_evidence(rec) == []
    assert rec["value"] is None
    assert rec["manifest_id"] and rec["locator"] and rec["sources"]


def test_excluded_value_cannot_be_numeric_unattributed_or_interpreted(fx):
    rec = _excluded_fixture(fx)
    rec["value"] = 1.0
    assert any("never filled in" in error for error in validate_evidence(rec))

    rec = _excluded_fixture(fx)
    rec.pop("curation_notes")
    assert any("attributed exclusion note" in error for error in validate_evidence(rec))

    rec = _excluded_fixture(fx)
    rec["evidence_category"] = "interpreted"
    assert any("must be measured evidence" in error for error in validate_evidence(rec))


def test_every_fixture_validates_and_lists_all_condition_keys(fixtures):
    for rec in fixtures:
        assert rec["fixture"] is True
        assert validate_evidence(rec) == [], rec["id"]
        assert set(rec["conditions"]) == set(CONDITION_KEYS)


def test_duplicate_ids_are_refused(fx):
    with pytest.raises(ValueError, match="duplicate"):
        index_records([fx("fixture-a-1"), fx("fixture-a-1")])
