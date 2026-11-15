"""B3 comparability (S5, S9, S11) against contract v0.2.2.

All data is SYNTHETIC (tests/backend/conftest.py). Nothing here is NASA data.

Three independent checks are applied to what the engine returns:
- the real `comparison.schema.json`
- the contract's own outcome oracle, `outcome_violations` (tests/test_comparability_outcome.py)
- `s5_allows` below, a separate brute-force statement of S5 written for these tests

The endpoint is not served: the last section proves `/api/compare` is still HTTP 501 in the real
application whatever the data.
"""

import ast
import itertools
import json
import random
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from conftest import excluded, interpretation, investigation, measured
from flameguard import CONTRACT_VERSION
from flameguard.api.app import create_app
from flameguard.api.compare import router
from flameguard.api.explorer import REJECTED_HEADER, EvidenceSource
from flameguard.compare import ComparisonError, build_comparison
from flameguard.data.loader import EvidenceStore
from test_comparability_outcome import outcome_rules, outcome_violations

REPO = Path(__file__).resolve().parents[2]
Q, UNIT = "flame_spread_rate", "mm/s"
SENTINEL = 987654.321  # a number that must never appear in any output
A, B = "Extinction", "Disruption"


# --- builders -------------------------------------------------------------------------------


def finding(fid, inv="inv-a", status="reported", value=1.0, tid=None, outcome=None, **cond):
    doc = measured(fid, inv, "ds-" + inv.removeprefix("inv-"))
    doc.update(value=value if status == "reported" else None, value_status=status)
    doc["conditions"] = {**doc["conditions"], **cond}
    if tid is not None or outcome is not None:
        doc.update(test_id=tid, test_outcome=outcome)
    return doc


def store_of(*findings):
    return EvidenceStore(findings=MappingProxyType({f["id"]: f for f in findings}))


def s5_allows(findings):
    """Independent statement of S5: may these findings be reported as comparable?"""
    if len(findings) < 2 or any(f["value_status"] != "reported" for f in findings):
        return False
    for key in findings[0]["conditions"]:
        values = [f["conditions"][key] for f in findings]
        reported = [v for v in values if v is not None]
        if len(reported) not in (0, len(values)) or any(v != reported[0] for v in reported):
            return False
    rows = [
        {"finding_id": f["id"], **{k: f.get(k) for k in ("test_id", "test_outcome")}}
        for f in findings
    ]
    return outcome_rules(rows) == []


def check(comparison, findings, validator):
    """Every invariant that must hold for any response."""
    validator.validate(comparison)
    by_id = {f["id"]: f for f in findings}
    assert outcome_violations(comparison, by_id) == []
    assert comparison["comparable"] == (comparison["non_comparable_reasons"] == [])
    assert comparison["contract_version"] == CONTRACT_VERSION
    for row in comparison["rows"]:
        src = by_id[row["finding_id"]]
        assert src["evidence_class"] == "measured" and src["quantity"] == comparison["quantity"]
        assert src["unit"] == comparison["unit"]
        if row["value_status"] == "reported":
            assert row["value"] == src["value"]
        else:
            assert row["value"] is None
    assert str(SENTINEL) not in json.dumps(comparison)


@pytest.fixture
def validator(validator_for):
    return validator_for("comparison.schema.json")


# --- positive oracle cases ------------------------------------------------------------------


def test_two_reported_rows_under_the_same_conditions_are_comparable(validator):
    fs = [finding("m1", "inv-a", value=1.5), finding("m2", "inv-b", value=2.5)]
    c = build_comparison(store_of(*fs), Q, UNIT)
    check(c, fs, validator)
    assert c["comparable"] is True and c["non_comparable_reasons"] == []
    assert [(r["finding_id"], r["value"]) for r in c["rows"]] == [("m1", 1.5), ("m2", 2.5)]
    assert all("test_id" not in r and "test_outcome" not in r for r in c["rows"])


def test_same_outcome_and_same_reported_conditions_are_comparable(validator):
    fs = [
        finding("m1", "inv-a", tid="T-1", outcome=A, oxygen_mole_fraction=0.21),
        finding("m2", "inv-b", tid="T-2", outcome=A, oxygen_mole_fraction=0.21),
        finding("m3", "inv-b", tid="T-3", outcome=A, oxygen_mole_fraction=0.21),
    ]
    c = build_comparison(store_of(*fs), Q, UNIT)
    check(c, fs, validator)
    assert c["comparable"] is True
    assert [(r["test_id"], r["test_outcome"]) for r in c["rows"]] == [
        ("T-1", A),
        ("T-2", A),
        ("T-3", A),
    ]


def test_integer_and_float_forms_of_one_condition_value_are_the_same_value(validator):
    fs = [finding("m1", pressure_kpa=101), finding("m2", "inv-b", pressure_kpa=101.0)]
    assert build_comparison(store_of(*fs), Q, UNIT)["comparable"] is True


# --- negative oracle cases: each S5 case gives its reason ------------------------------------

NEGATIVE = [
    (
        "not-reported",
        [finding("m1"), finding("m2", "inv-b", status="not_reported")],
        "m2: the source does not report a value",
    ),
    (
        "not-applicable",
        [finding("m1"), finding("m2", "inv-b", status="not_applicable")],
        "m2: no numeric value applies",
    ),
    (
        "excluded",
        [finding("m1"), finding("m2", "inv-b", status="excluded")],
        "m2: the value is excluded",
    ),
    (
        "condition-differs",
        [
            finding("m1", oxygen_mole_fraction=0.21),
            finding("m2", "inv-b", oxygen_mole_fraction=0.18),
        ],
        "condition oxygen_mole_fraction differs across rows: 0.18, 0.21",
    ),
    (
        "condition-partial",
        [finding("m1", pressure_kpa=101.3), finding("m2", "inv-b")],
        "condition pressure_kpa is reported for some rows and not for others (m2)",
    ),
    (
        "gravity-differs",
        [finding("m1"), finding("m2", "inv-b", gravity_environment="normal_gravity")],
        "condition gravity_environment differs across rows",
    ),
    (
        "outcome-differs",
        [finding("m1", tid="T-1", outcome=A), finding("m2", "inv-b", tid="T-2", outcome=B)],
        "rows report different test outcomes: Disruption, Extinction",
    ),
    (
        "outcome-partial",
        [finding("m1", tid="T-1", outcome=A), finding("m2", "inv-b")],
        "test outcome is reported for some rows and not for others",
    ),
    (
        "id-without-outcome",
        [finding("m1", tid="T-1"), finding("m2", "inv-b", tid="T-2")],
        "m1: the test is identified but its outcome is not reported",
    ),
    ("single-row", [finding("m1")], "fewer than two measured findings"),
]


@pytest.mark.parametrize(("fs", "reason"), [n[1:] for n in NEGATIVE], ids=[n[0] for n in NEGATIVE])
def test_each_non_comparable_case_is_explained(fs, reason, validator):
    c = build_comparison(store_of(*fs), Q, UNIT)
    check(c, fs, validator)
    assert c["comparable"] is False
    assert any(reason in r for r in c["non_comparable_reasons"]), c["non_comparable_reasons"]
    assert not s5_allows(fs)


def test_every_problem_is_reported_not_only_the_first(validator):
    fs = [
        finding("m1", tid="T-1", outcome=A, oxygen_mole_fraction=0.21, pressure_kpa=101.3),
        finding("m2", "inv-b", status="excluded", tid="T-2", outcome=B, oxygen_mole_fraction=0.18),
    ]
    c = build_comparison(store_of(*fs), Q, UNIT)
    check(c, fs, validator)
    text = " | ".join(c["non_comparable_reasons"])
    for part in (
        "m2: the value is excluded",
        "oxygen_mole_fraction differs",
        "pressure_kpa is reported for some",
        "different test outcomes",
    ):
        assert part in text


def test_no_rows_is_an_honest_non_comparable_answer(validator):
    c = build_comparison(store_of(), Q, UNIT)
    validator.validate(c)
    assert c["rows"] == [] and c["comparable"] is False and c["non_comparable_reasons"]


def test_a_selected_investigation_without_the_quantity_blocks_the_comparison(validator):
    fs = [finding("m1"), finding("m2")]
    c = build_comparison(store_of(*fs), Q, UNIT, ["inv-a", "inv-b"])
    check(c, fs, validator)
    assert c["comparable"] is False
    assert "inv-b has no measured finding for flame_spread_rate" in c["non_comparable_reasons"]


# --- exhaustive agreement with the independent oracles ---------------------------------------

STATUSES = ("reported", "not_reported", "not_applicable", "excluded")
IDENTITIES = ((None, None), ("T", None), ("T", A), ("T", B))
OXYGEN = (None, 0.21, 0.18)
VARIANTS = list(itertools.product(STATUSES, IDENTITIES, OXYGEN))


def _build(combo):
    out = []
    for n, (status, (tid, outcome), oxygen) in enumerate(combo):
        tid = f"{tid}-{n}" if tid else None
        out.append(
            finding(
                f"m{n}",
                f"inv-{'abc'[n]}",
                status=status,
                tid=tid,
                outcome=outcome,
                oxygen_mole_fraction=oxygen,
            )
        )
    return out


def _combos():
    yield from itertools.product(VARIANTS, repeat=2)
    rng = random.Random(20261115)  # noqa: S311 - reproducible sample, not security
    for _ in range(1500):
        yield tuple(rng.choice(VARIANTS) for _ in range(3))


def test_the_decision_agrees_with_the_independent_oracles_for_every_combination(validator):
    comparable = 0
    for combo in _combos():
        fs = _build(combo)
        c = build_comparison(store_of(*fs), Q, UNIT)
        check(c, fs, validator)
        assert c["comparable"] == s5_allows(fs), (combo, c["non_comparable_reasons"])
        comparable += c["comparable"]
    assert comparable > 0  # the sweep exercises both answers


# --- S9: excluded and missing values never appear -------------------------------------------


def test_a_value_left_on_a_non_reported_finding_is_never_copied(validator):
    for status in ("excluded", "not_reported", "not_applicable"):
        leaked = finding("m2", "inv-b", status=status)
        leaked["value"] = (
            SENTINEL  # the loader would reject this; the engine must still withhold it
        )
        c = build_comparison(store_of(finding("m1"), leaked), Q, UNIT)
        validator.validate(c)
        assert c["comparable"] is False
        assert c["rows"][1]["value"] is None and str(SENTINEL) not in json.dumps(c)


def test_reasons_never_quote_measured_values_or_curation_notes(validator):
    ex = excluded("ex1", "inv-b", "ds-b")
    fs = [finding("m1", value=SENTINEL), ex]
    c = build_comparison(store_of(*fs), Q, UNIT)
    validator.validate(c)
    reasons = " ".join(c["non_comparable_reasons"])
    assert str(SENTINEL) not in reasons and "987654" not in reasons
    assert ex["curation_notes"][0]["note"] not in reasons


def test_interpretations_are_never_rows(validator):
    interp = interpretation("i1", "inv-a", ["m1"], quantity=Q, unit=UNIT, value=SENTINEL)
    fs = [finding("m1"), finding("m2", "inv-b")]
    c = build_comparison(store_of(*fs, interp), Q, UNIT)
    check(c, fs, validator)
    assert [r["finding_id"] for r in c["rows"]] == ["m1", "m2"]


def test_other_quantities_are_never_rows(validator):
    other = finding("m3", "inv-b")
    other.update(quantity="flame_length", unit="mm")
    c = build_comparison(store_of(finding("m1"), finding("m2", "inv-b"), other), Q, UNIT)
    assert [r["finding_id"] for r in c["rows"]] == ["m1", "m2"]


# --- outcomes are copied, never inferred ----------------------------------------------------


def test_an_outcome_is_never_inferred_from_prose_or_values(validator):
    fs = [finding("m1", value=0.0), finding("m2", "inv-b", value=0.0)]
    for f in fs:
        f["statement"] = "SYNTHETIC: Test end: Extinction. The flame went out."
        f["provenance"]["locator"] = "SYNTHETIC row, outcome Extinction"
        f["uncertainty"] = "SYNTHETIC Disruption"
    c = build_comparison(store_of(*fs), Q, UNIT)
    check(c, fs, validator)
    assert c["comparable"] is True
    assert all("test_outcome" not in r and "test_id" not in r for r in c["rows"])
    assert "Extinction" not in json.dumps(c) and "Disruption" not in json.dumps(c)


def test_the_engine_reads_no_prose_field():
    source = (REPO / "backend/flameguard/compare/engine.py").read_text(encoding="utf-8")
    strings = {
        n.value
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }
    assert not strings & {
        "statement",
        "locator",
        "uncertainty",
        "limitations",
        "curation_notes",
        "note",
    }
    assert {"test_id", "test_outcome"} <= strings


def test_the_engine_does_no_arithmetic_on_values():
    tree = ast.parse((REPO / "backend/flameguard/compare/engine.py").read_text(encoding="utf-8"))
    assert not [
        n for n in ast.walk(tree) if isinstance(n, ast.BinOp) and not isinstance(n.op, ast.BitOr)
    ]
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not names & {"sum", "min", "max", "mean", "abs", "round", "statistics"}


# --- fail closed on broken invariants -------------------------------------------------------


def test_a_unit_other_than_the_vocabulary_unit_refuses_the_comparison():
    wrong = finding("m2", "inv-b")
    wrong["unit"] = "cm/s"
    with pytest.raises(ComparisonError, match="unit"):
        build_comparison(store_of(finding("m1"), wrong), Q, UNIT)


@pytest.mark.parametrize("bad", [None, "1.0", True])
def test_a_reported_finding_without_a_number_refuses_the_comparison(bad):
    broken = finding("m2", "inv-b")
    broken["value"] = bad
    with pytest.raises(ComparisonError, match="numeric"):
        build_comparison(store_of(finding("m1"), broken), Q, UNIT)


# --- ordering and determinism ---------------------------------------------------------------


def test_rows_follow_the_requested_investigation_order_then_finding_id():
    fs = [finding("m3", "inv-a"), finding("m1", "inv-b"), finding("m2", "inv-a")]
    ids = lambda c: [r["finding_id"] for r in c["rows"]]  # noqa: E731
    assert ids(build_comparison(store_of(*fs), Q, UNIT)) == ["m2", "m3", "m1"]
    assert ids(build_comparison(store_of(*fs), Q, UNIT, ["inv-b", "inv-a"])) == ["m1", "m2", "m3"]
    assert ids(build_comparison(store_of(*fs), Q, UNIT, ["inv-b"])) == ["m1"]
    assert build_comparison(store_of(*fs), Q, UNIT) == build_comparison(
        store_of(*reversed(fs)), Q, UNIT
    )


def test_the_store_is_not_modified():
    fs = [finding("m1", tid="T-1", outcome=A), finding("m2", "inv-b", status="excluded")]
    before = json.dumps(fs, sort_keys=True)
    c = build_comparison(store_of(*fs), Q, UNIT)
    c["rows"][0]["conditions"]["pressure_kpa"] = 1.0
    assert json.dumps(fs, sort_keys=True) == before


# --- through the real loader and the (unmounted) endpoint handler -----------------------------


def private_client(root):
    app = FastAPI()
    app.state.evidence_source = EvidenceSource(root)
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def two(scenario):
    """inv-a: m1 reported + ex1 excluded (conftest); inv-b: m2 reported."""
    scenario.investigations.append(investigation("inv-b", ["ds-b"]))
    scenario.findings["inv-b"] = [measured("m2", "inv-b", "ds-b")]
    return scenario


def _err(validator_for, r, status, code):
    assert r.status_code == status, r.text
    validator_for("error.schema.json").validate(r.json())
    assert r.json()["error"]["code"] == code


def test_endpoint_returns_a_contract_comparison_from_loaded_evidence(two, validator):
    two.findings["inv-a"] = [measured("m1", "inv-a", "ds-a")]
    two.interps = {}
    client = private_client(two.write())
    r = client.get(f"/api/compare?quantity={Q}&investigation_ids=inv-a,inv-b")
    assert r.status_code == 200 and REJECTED_HEADER not in r.headers
    body = r.json()
    validator.validate(body)
    assert body["comparable"] is True and [x["finding_id"] for x in body["rows"]] == ["m1", "m2"]
    assert body["unit"] == UNIT and body["contract_version"] == CONTRACT_VERSION


def test_endpoint_shows_an_excluded_finding_only_as_a_non_comparable_row(two, validator):
    body = private_client(two.write()).get(f"/api/compare?quantity={Q}").json()
    validator.validate(body)
    assert body["comparable"] is False
    ex = next(x for x in body["rows"] if x["finding_id"] == "ex1")
    assert ex["value"] is None and ex["value_status"] == "excluded"
    assert any(x.startswith("ex1: the value is excluded") for x in body["non_comparable_reasons"])
    assert {x["finding_id"] for x in body["rows"]} == {"m1", "m2", "ex1"}  # no interpretation


def test_endpoint_with_real_outcome_vocabulary(two, validator):
    def with_outcomes(second):
        two.findings["inv-a"] = [measured("m1", "inv-a", "ds-a", test_id="T-1", test_outcome=A)]
        two.findings["inv-b"] = [
            measured("m2", "inv-b", "ds-b", test_id="T-2", test_outcome=second)
        ]
        two.interps = {}

    with_outcomes(A)
    same = private_client(two.write()).get(f"/api/compare?quantity={Q}").json()
    validator.validate(same)
    assert same["comparable"] is True and {x["test_outcome"] for x in same["rows"]} == {A}


def test_endpoint_refuses_different_outcomes(two, validator):
    two.findings["inv-a"] = [measured("m1", "inv-a", "ds-a", test_id="T-1", test_outcome=A)]
    two.findings["inv-b"] = [
        measured("m2", "inv-b", "ds-b", test_id="T-2", test_outcome="Completion")
    ]
    two.interps = {}
    body = private_client(two.write()).get(f"/api/compare?quantity={Q}").json()
    validator.validate(body)
    assert body["comparable"] is False
    assert (
        "rows report different test outcomes: Completion, Extinction"
        in body["non_comparable_reasons"]
    )


def test_endpoint_parameter_errors(two, validator_for):
    client = private_client(two.write())
    for url in (
        "/api/compare",
        "/api/compare?quantity=",
        "/api/compare?quantity=not_a_quantity",
        f"/api/compare?quantity={Q}&x=1",
        f"/api/compare?quantity={Q}&quantity={Q}",
        f"/api/compare?quantity={Q}&investigation_ids=inv-a,nope",
        f"/api/compare?quantity={Q}&investigation_ids=",
        f"/api/compare?quantity={Q}&investigation_ids=inv-a,,inv-b",
        f"/api/compare?quantity={Q}&investigation_ids=inv-a,inv-a",
        f"/api/compare?quantity={Q}&investigation_ids=inv-a&investigation_ids=inv-b",
    ):
        _err(validator_for, client.get(url), 400, "invalid_request")


def test_endpoint_fails_closed_when_evidence_cannot_be_loaded(two, validator_for):
    two.raw["data/manifest.json"] = "{ not json"
    _err(
        validator_for,
        private_client(two.write()).get(f"/api/compare?quantity={Q}"),
        503,
        "unavailable",
    )


def test_endpoint_announces_rejected_entries_and_never_uses_them(two, validator):
    two.tamper["ds-b"] = "0" * 64  # inv-b's file no longer matches its registered hash
    r = private_client(two.write()).get(f"/api/compare?quantity={Q}")
    validator.validate(r.json())
    assert r.headers[REJECTED_HEADER] == "1"
    assert "m2" not in {x["finding_id"] for x in r.json()["rows"]}


def test_s11_violations_never_reach_a_comparison(two, validator):
    """Mixed test identity inside one investigation is rejected by the loader, not compared."""
    two.findings["inv-b"] = [
        measured("m2", "inv-b", "ds-b", test_id="T-2", test_outcome=A),
        measured("m3", "inv-b", "ds-b"),
    ]
    r = private_client(two.write()).get(f"/api/compare?quantity={Q}")
    validator.validate(r.json())
    assert r.headers[REJECTED_HEADER] == "1"
    assert not {"m2", "m3"} & {x["finding_id"] for x in r.json()["rows"]}


# --- the served application still answers 501 -----------------------------------------------


def test_served_compare_is_still_501_even_with_comparable_evidence(two, validator_for):
    two.findings["inv-a"] = [measured("m1", "inv-a", "ds-a")]
    two.interps = {}
    client = TestClient(create_app(EvidenceSource(two.write())))
    for url in (
        "/api/compare",
        f"/api/compare?quantity={Q}",
        f"/api/compare?quantity={Q}&investigation_ids=inv-a,inv-b",
    ):
        _err(validator_for, client.get(url), 501, "not_implemented")


def test_the_application_does_not_load_the_compare_code():
    code = (
        "import sys, flameguard.api.app; "
        "print(sorted(m for m in sys.modules if m.startswith('flameguard') and 'compare' in m))"
    )
    out = subprocess.run(  # noqa: S603 - fixed command, this interpreter
        [sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", check=True
    )
    assert out.stdout.strip() == "[]"
    app_source = (REPO / "backend/flameguard/api/app.py").read_text(encoding="utf-8")
    assert ("GET", "/api/compare") in ast.literal_eval(
        app_source.split("PLANNED_ENDPOINTS: list[tuple[str, str]] = ")[1].split("]\n")[0] + "]"
    )


def test_no_switch_can_serve_the_endpoint():
    for rel in (
        "backend/flameguard/api/compare.py",
        "backend/flameguard/compare/engine.py",
        "backend/flameguard/compare/__init__.py",
    ):
        source = (REPO / rel).read_text(encoding="utf-8")
        assert "os.environ" not in source and "getenv" not in source
        imports = [
            n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Import | ast.ImportFrom)
        ]
        modules = {getattr(n, "module", None) or n.names[0].name for n in imports}
        assert not {
            m
            for m in modules
            if any(part in m for part in ("ranking", "assistant", "simulation", "research"))
        }
