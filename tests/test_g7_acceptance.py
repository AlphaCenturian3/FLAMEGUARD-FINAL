"""G7 acceptance criteria A1-A7 (docs/decisions/g7-flex-conditions.md), one assertion each."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


dv = _load("derive_flex_findings", "tools/derive_flex_findings.py")
au = _load("audit_flex_findings", "tools/audit_flex_findings.py")
vft = au.vft
DOC = (ROOT / "docs" / "decisions" / "g7-flex-conditions.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def findings():
    return dv.derive(ROOT)["findings"]


@pytest.fixture(scope="module")
def csv_rows():
    return {r["flex_test"]: r for r in dv.read_rows(vft.CSV_PATH)}


def test_a5_every_conditions_object_validates_against_the_schema(findings, validator_for):
    v = validator_for("conditions.schema.json")
    for f in findings:
        assert not list(v.iter_errors(f["conditions"])), f["id"]
    assert len(findings) == 40


def test_a1_diluent_is_the_printed_nonzero_fractions_in_fixed_order(findings, csv_rows):
    for f in findings:
        row = csv_rows[f["test_id"]]
        parts = [
            f"{s} {row[c]}"
            for s, c in (
                ("CO2", "co2_mole_fraction"),
                ("He", "he_mole_fraction"),
                ("N2", "n2_mole_fraction"),
            )
            if Decimal(row[c]) != 0
        ]
        assert f["conditions"]["diluent"] == ("; ".join(parts) or None), f["id"]
    assert {f["conditions"]["diluent"] for f in findings} == {"N2 0.79", "CO2 0.7; N2 0.09"}


def test_a2_fuel_is_the_printed_word(findings, csv_rows):
    for f in findings:
        assert f["conditions"]["fuel_or_material"] == csv_rows[f["test_id"]]["fuel"]


def test_a3_sample_geometry_is_null_on_all_forty(findings, validator_for):
    assert {f["conditions"]["sample_geometry"] for f in findings} == {None}


def test_a4_pressure_is_the_exact_conversion_and_the_printed_value_is_in_the_locator(
    findings, csv_rows
):
    for f in findings:
        mmhg = csv_rows[f["test_id"]]["ambient_pressure_mmhg"]
        exact = Decimal(mmhg) * Decimal("0.133322387415")
        assert Decimal(repr(f["conditions"]["pressure_kpa"])) == exact
        assert f"{mmhg} mmHg" in f["provenance"]["locator"]


def test_a6_mixtures_do_not_collide_and_bad_compositions_are_refused(csv_rows):
    seen = {}
    for row in csv_rows.values():
        key = (
            Decimal(row["n2_mole_fraction"]),
            Decimal(row["co2_mole_fraction"]),
            Decimal(row["he_mole_fraction"]),
        )
        assert seen.setdefault(dv.diluent_text(row), key) == key
    bad = dict(csv_rows["FLEX-001"], n2_mole_fraction="0.5")
    with pytest.raises(dv.DerivationError):
        dv.check_composition(bad)


def test_a7_the_decision_is_recorded_as_provisional_not_as_scientific_approval():
    gates = json.loads((ROOT / "tools" / "flex_derivation_gates.json").read_text(encoding="utf-8"))
    for c in gates["conditions"].values():
        assert c["status"] == "owner_provisional"
        assert "not an independent scientific approval" in c["decided_by"]
    assert (
        "not** an independent scientific approval" in DOC
        or "not an independent scientific approval" in DOC
    )
    assert dv.registrable(gates) is False


def test_the_g7_gate_is_closed_only_with_its_criteria_documented_and_satisfied():
    gates = json.loads((ROOT / "tools" / "flex_derivation_gates.json").read_text(encoding="utf-8"))
    g7 = next(g for g in gates["gates"] if g["id"] == "G7")
    assert g7["status"] == "closed"
    assert "g7-flex-conditions.md" in g7["what"] and "not an independent scientific" in g7["what"]
    for n in range(1, 8):
        assert f"| A{n} |" in DOC
    assert hashlib.sha256(DOC.encode()).hexdigest()  # the record exists and is readable
