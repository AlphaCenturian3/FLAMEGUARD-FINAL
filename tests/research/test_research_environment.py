"""Cited environmental reference table (D-01 condition 2)."""

import json
from pathlib import Path

import pytest
from research.common import ENVIRONMENTS, GRAVITY_ENVIRONMENTS
from research.evidence import validate_source

FILE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "research"
    / "member5"
    / "environment_reference.json"
)


@pytest.fixture
def ref():
    return json.loads(FILE.read_text(encoding="utf-8"))


def _indices(entry):
    idx = entry.get("source_index")
    return [] if idx is None else (idx if isinstance(idx, list) else [idx])


def test_every_contract_environment_is_covered_once(ref):
    envs = [r["environment"] for r in ref["records"]]
    assert sorted(envs) == sorted(ENVIRONMENTS)


def test_physical_and_design_blocks_are_separate(ref):
    statuses = set(ref["status_values"])
    for r in ref["records"]:
        assert set(r) >= {"physical", "design_atmospheres", "sources"}
        for key in ("gravity", "contract_gravity_environment", "external_atmosphere"):
            assert r["physical"][key]["status"] in statuses
            assert r["physical"][key]["status"] not in ("operational", "design_assumption")
        for atm in r["design_atmospheres"]:
            assert atm["status"] in statuses
            assert atm["status"] != "physical_reference", (r["id"], atm["label"])


def test_every_stated_value_cites_a_valid_source(ref):
    for r in ref["records"]:
        for i, src in enumerate(r["sources"]):
            assert validate_source(src, f"{r['id']}.sources[{i}]") == []
            assert src["quote"], r["id"]
        blocks = [r["physical"]["gravity"], r["physical"]["external_atmosphere"]]
        blocks += r["design_atmospheres"]
        for b in blocks:
            has_value = any(
                b.get(k) is not None for k in ("value_m_s2", "pressure_kpa", "oxygen_mole_fraction")
            )
            if has_value or b["status"] in (
                "physical_reference",
                "operational",
                "design_assumption",
            ):
                if b["status"] != "editorial_classification":
                    assert _indices(b), (r["id"], b)
            for i in _indices(b):
                assert 0 <= i < len(r["sources"]), (r["id"], i)


def test_unknown_values_stay_null(ref):
    for r in ref["records"]:
        for atm in r["design_atmospheres"]:
            if atm["status"] == "unknown":
                assert atm["pressure_kpa"] is None and atm["oxygen_mole_fraction"] is None
    by_env = {r["environment"]: r for r in ref["records"]}
    current = [
        a
        for a in by_env["martian_base"]["design_atmospheres"]
        if a["status"] != "historical_recommendation"
    ]
    assert all(a["status"] == "unknown" for a in current)
    assert by_env["pressurized_rover"]["design_atmospheres"][0]["status"] == "unknown"


def test_gravity_categories_and_values(ref):
    by_env = {r["environment"]: r for r in ref["records"]}
    for r in ref["records"]:
        assert r["physical"]["contract_gravity_environment"]["value"] in GRAVITY_ENVIRONMENTS
    assert by_env["lunar_base"]["physical"]["gravity"]["value_m_s2"] == 1.62
    assert by_env["martian_base"]["physical"]["gravity"]["value_m_s2"] == 3.73
    # The contract category cannot tell lunar from Martian gravity (v0.3 candidate).
    assert (
        by_env["lunar_base"]["physical"]["contract_gravity_environment"]["value"]
        == by_env["martian_base"]["physical"]["contract_gravity_environment"]["value"]
        == "partial_gravity"
    )
    assert by_env["spacecraft"]["physical"]["gravity"]["status"] == "editorial_classification"


def test_conversions_are_exact_defined_factors(ref):
    by_env = {r["environment"]: r for r in ref["records"]}
    assert by_env["martian_base"]["physical"]["external_atmosphere"]["pressure_kpa"] == 0.636
    assert by_env["earth"]["physical"]["external_atmosphere"]["pressure_kpa"] == 101.4
    assert by_env["lunar_base"]["physical"]["external_atmosphere"]["pressure_kpa"] == 3e-13
    hist = [
        a
        for a in by_env["martian_base"]["design_atmospheres"]
        if a["status"] == "historical_recommendation"
    ]
    assert hist and hist[0]["pressure_kpa"] is None  # psia-only source, not converted


def test_member1_labels_and_authentication_status(ref):
    by_env = {r["environment"]: r for r in ref["records"]}
    assert by_env["spacecraft"]["physical"]["gravity"]["display_label"] == "assumed: coast phase"
    variants = {v["case"]: v for v in by_env["pressurized_rover"]["physical"]["variants"]}
    assert variants["Martian pressurized rover"]["display_label"] == "reference unknown"
    assert variants["Martian pressurized rover"]["contract_gravity_environment"] is None
    assert variants["lunar pressurized rover"]["display_label"] == "assumed: lunar rover"
    assert "not independently authenticated" in ref["status"]
