"""PROPOSAL tests for R1 and R4 (Member 3, PR #38 audit). Discussion only.

These invariants are NOT enforced by the B1 loader at the time of writing (PR #37 `17dab2d`):

- R1 (required by the audit, subject to owner approval): within one investigation, at most one
  measured finding per (test_id, quantity).
- R4 (recommendation): all measured findings of one test share one `test_outcome` and one
  `conditions` object.

Tests that describe the proposed behaviour are marked `xfail(strict=True)`. They fail today,
which is the documented gap. If the loader starts enforcing a rule, the test passes, strict
xfail turns that into a failure, and the marker must be removed in the same change. Nothing
here modifies production code.

All synthetic records are built at test time in a temporary directory and are labelled
SYNTHETIC. They are not NASA data and are never written under the repository's data/.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path

import pytest

from flameguard.data.loader import Status, load_evidence

REPO = Path(__file__).resolve().parents[2]
STAGED_FLEX = REPO / "data" / "curated" / "findings" / "flex.json"

R1 = pytest.mark.xfail(
    strict=True,
    reason="R1 proposed (PR #38 audit); not enforced by the B1 loader; subject to owner approval",
)
R4 = pytest.mark.xfail(
    strict=True,
    reason="R4 recommended (PR #38 audit); not enforced by the B1 loader",
)

CONDITIONS = {
    "gravity_environment": "microgravity",
    "oxygen_mole_fraction": 0.21,
    "pressure_kpa": 101.3,
    "flow_velocity_mm_s": None,
    "flow_configuration": None,
    "diluent": "N2",
    "fuel_or_material": "synthetic fuel",
    "sample_geometry": None,
}
UNITS = {"burn_time": "s", "initial_droplet_diameter": "mm"}
SOURCE = {
    "title": "SYNTHETIC TEST SOURCE (not NASA)",
    "url": "https://example.invalid/synthetic",
    "page": None,
    "quote": None,
    "retrieved": "2026-11-15",
    "archive_id": None,
}


# --- independent oracle (test-only; not the production rule) -----------------------------


def identity_invariant_violations(findings: list[dict]) -> list[str]:
    """R1 and R4 over measured findings that carry a test_id. Absent/null/"" = no identity."""
    by_key: dict[tuple, list[str]] = defaultdict(list)
    outcome: dict[tuple, set] = defaultdict(set)
    conditions: dict[tuple, set] = defaultdict(set)
    for f in findings:
        if f.get("evidence_class") != "measured" or not f.get("test_id"):
            continue
        test = (f["investigation_id"], f["test_id"])
        by_key[(*test, f["quantity"])].append(f["id"])
        outcome[test].add(f.get("test_outcome"))
        conditions[test].add(json.dumps(f.get("conditions"), sort_keys=True))
    out = [f"R1 {k}: {sorted(v)}" for k, v in by_key.items() if len(v) > 1]
    out += [f"R4 outcome {k}: {sorted(map(str, v))}" for k, v in outcome.items() if len(v) > 1]
    out += [f"R4 conditions {k}" for k, v in conditions.items() if len(v) > 1]
    return out


# --- synthetic repository builder ------------------------------------------------------------


def finding(inv, fid, test_id, quantity="burn_time", value=1.0, status="reported", **over):
    f = {
        "id": fid,
        "investigation_id": inv,
        "evidence_class": "measured",
        "statement": "SYNTHETIC TEST RECORD. Not NASA data.",
        "quantity": quantity,
        "value": value if status == "reported" else None,
        "unit": UNITS[quantity],
        "value_status": status,
        "uncertainty": None,
        "conditions": dict(CONDITIONS),
        "provenance": {
            "manifest_id": f"{inv}.findings",
            "locator": f"synthetic table, {test_id or 'no test'}, {quantity}",
            "sources": [dict(SOURCE)],
        },
    }
    if test_id is not None:
        f["test_id"] = test_id
        f["test_outcome"] = "Extinction"
    if status == "excluded":
        f["curation_notes"] = [
            {
                "kind": "exclusion",
                "note": "SYNTHETIC exclusion",
                "generated_by": "FlameGuard-SI",
                "flag_ref": {"manifest_id": f"{inv}.flags", "flag_id": "S001"},
                "source": {**SOURCE, "quote": "synthetic quote"},
            }
        ]
    for key, val in over.items():
        if key == "conditions":
            f["conditions"].update(val)
        else:
            f[key] = val
    return f


def _write(root: Path, rel: str, doc) -> str:
    data = (json.dumps(doc, indent=2) + "\n").encode("utf-8")
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)  # bytes: the registered sha256 must match on every platform
    return hashlib.sha256(data).hexdigest()


def build_repo(tmp_path: Path, files: dict[str, list[dict]]) -> Path:
    """A minimal valid repository: the branch's contract, its provenance tool, one findings
    file per investigation, an investigations file and a manifest registering them."""
    root = tmp_path / "repo"
    shutil.copytree(REPO / "contracts", root / "contracts")
    (root / "tools").mkdir(parents=True)
    shutil.copy2(REPO / "tools" / "check_data_provenance.py", root / "tools")
    entries = []
    invs = []
    for inv, items in files.items():
        rel = f"data/curated/findings/{inv}.json"
        entries.append(
            {
                "id": f"{inv}.findings",
                "path": rel,
                "evidence_class": "measured",
                "sha256": _write(root, rel, items),
                "description": "SYNTHETIC test findings. Not NASA data.",
                "sources": [dict(SOURCE)],
                "rights_status": "under_review",
            }
        )
        invs.append(
            {
                "id": inv,
                "name": f"SYNTHETIC investigation {inv}",
                "acronym": None,
                "platform": None,
                "objectives": [],
                "datasets": [f"{inv}.findings"],
                "sources": [dict(SOURCE)],
            }
        )
    rel = "data/curated/investigations.json"
    entries.append(
        {
            "id": "synthetic.investigations",
            "path": rel,
            "evidence_class": "measured",
            "sha256": _write(root, rel, invs),
            "description": "SYNTHETIC investigations. Not NASA data.",
            "sources": [dict(SOURCE)],
            "rights_status": "under_review",
        }
    )
    _write(root, "data/manifest.json", {"manifest_version": "0.2.0", "datasets": entries})
    return root


def status_of(result, entry_id):
    return next(e for e in result.report.entries if e.id == entry_id)


def consistent(inv="syn-a"):
    """Two tests x two quantities, internally consistent: the R1/R4 baseline."""
    return [
        finding(inv, f"{inv}.t1.bt", "T-1", "burn_time", 5.0),
        finding(inv, f"{inv}.t1.d0", "T-1", "initial_droplet_diameter", 2.0),
        finding(inv, f"{inv}.t2.bt", "T-2", "burn_time", 6.0),
        finding(inv, f"{inv}.t2.d0", "T-2", "initial_droplet_diameter", 2.1),
    ]


# --- guards: pass today and must keep passing ---------------------------------------------------


def test_harness_baseline_is_accepted(tmp_path):
    """If this fails, a rejection below is the harness's fault, not the invariant's."""
    items = consistent()
    assert identity_invariant_violations(items) == []
    r = load_evidence(build_repo(tmp_path, {"syn-a": items}))
    assert r.report.manifest_ok and [e.id for e in r.report.rejected] == []
    assert len(r.store.findings) == 4


def test_findings_without_test_identity_are_outside_r1(tmp_path):
    """R1 is about identified tests only. Two un-identified findings of one quantity stay valid."""
    items = [
        finding("syn-a", "syn-a.x1", None, "burn_time", 5.0),
        finding("syn-a", "syn-a.x2", None, "burn_time", 6.0),
    ]
    assert identity_invariant_violations(items) == []
    r = load_evidence(build_repo(tmp_path, {"syn-a": items}))
    assert [e.id for e in r.report.rejected] == []
    assert len(r.store.findings) == 2


@pytest.mark.parametrize(
    "items",
    [
        [finding("syn-a", "a.1", "T-1"), finding("syn-a", "a.2", "T-1", value=9.0)],
        [finding("syn-a", "a.1", "T-1"), finding("syn-a", "a.2", "T-1", status="not_reported")],
    ],
    ids=["two_reported", "reported_and_not_reported"],
)
def test_oracle_detects_r1_duplicates(items):
    assert any(v.startswith("R1 ") for v in identity_invariant_violations(items))


# --- R1: duplicate measured findings per (investigation, test_id, quantity) ----------------------


@R1
@pytest.mark.parametrize(
    "second",
    [
        {"value": 9.0},
        {"status": "not_reported"},
        {"status": "excluded"},
    ],
    ids=["two_reported", "reported_and_not_reported", "reported_and_excluded"],
)
def test_r1_duplicate_test_quantity_rejects_the_file(tmp_path, second):
    status = second.pop("status", "reported")
    items = consistent() + [
        finding("syn-a", "syn-a.t1.bt.dup", "T-1", "burn_time", status=status, **second)
    ]
    assert any(v.startswith("R1 ") for v in identity_invariant_violations(items))
    r = load_evidence(build_repo(tmp_path, {"syn-a": items}))
    entry = status_of(r, "syn-a.findings")
    assert entry.status is Status.REJECTED  # fail closed: the whole file, not one row
    assert len(r.store.findings) == 0
    text = " ".join(entry.reasons)
    assert "syn-a.t1.bt" in text and "syn-a.t1.bt.dup" in text and "T-1" in text


# --- R4: one outcome and one conditions object per test -------------------------------------


@R4
def test_r4_conflicting_outcomes_within_a_test_reject_the_file(tmp_path):
    items = consistent()
    items[1]["test_outcome"] = "Disruption"  # T-1: burn_time Extinction, diameter Disruption
    assert any(v.startswith("R4 outcome") for v in identity_invariant_violations(items))
    r = load_evidence(build_repo(tmp_path, {"syn-a": items}))
    entry = status_of(r, "syn-a.findings")
    assert entry.status is Status.REJECTED
    assert "T-1" in " ".join(entry.reasons)


@R4
@pytest.mark.parametrize(
    "change",
    [{"pressure_kpa": 202.6}, {"fuel_or_material": "other synthetic fuel"}, {"diluent": None}],
    ids=["value_differs", "text_differs", "null_versus_reported"],
)
def test_r4_conflicting_conditions_within_a_test_reject_the_file(tmp_path, change):
    items = consistent()
    items[1]["conditions"].update(change)
    assert any(v.startswith("R4 conditions") for v in identity_invariant_violations(items))
    r = load_evidence(build_repo(tmp_path, {"syn-a": items}))
    entry = status_of(r, "syn-a.findings")
    assert entry.status is Status.REJECTED
    assert "T-1" in " ".join(entry.reasons)


# --- rejection is isolated and reported -----------------------------------------------------------


@R1
def test_r1_rejection_is_isolated_and_reported(tmp_path):
    """Only the offending file is rejected; a valid investigation still loads; the report names
    the rejected entry, the rule and the findings, and the investigations file warns."""
    bad = consistent("syn-a") + [finding("syn-a", "syn-a.t2.bt.dup", "T-2", "burn_time", 7.0)]
    good = consistent("syn-b")
    r = load_evidence(build_repo(tmp_path, {"syn-a": bad, "syn-b": good}))
    assert r.report.manifest_ok
    assert [e.id for e in r.report.rejected] == ["syn-a.findings"]
    assert status_of(r, "syn-b.findings").status is Status.ACCEPTED
    assert sorted(r.store.findings) == sorted(f["id"] for f in good)
    reasons = " ".join(status_of(r, "syn-a.findings").reasons)
    assert "R1" in reasons and "syn-a.t2.bt.dup" in reasons
    assert any("syn-a.findings" in w for w in r.report.warnings)


def test_a_valid_investigation_loads_next_to_any_other(tmp_path):
    """The part of the isolation test that already holds today."""
    r = load_evidence(
        build_repo(tmp_path, {"syn-a": consistent("syn-a"), "syn-b": consistent("syn-b")})
    )
    assert [e.id for e in r.report.rejected] == []
    assert len(r.store.findings) == 8


# --- preservation of the staged FLEX Findings ----------------------------------------------


@pytest.mark.skipif(
    not STAGED_FLEX.is_file(),
    reason="staged FLEX Findings are not on this branch (they are in PR #31); "
    "run in a checkout that holds data/curated/findings/flex.json",
)
def test_staged_flex_findings_satisfy_r1_r4_and_still_load():
    items = json.loads(STAGED_FLEX.read_text(encoding="utf-8"))
    assert len(items) == 40
    assert identity_invariant_violations(items) == []
    r = load_evidence(REPO)
    assert [e.id for e in r.report.rejected] == []
    loaded = [f for f in r.store.findings.values() if f["investigation_id"] == "flex"]
    assert len(loaded) == 40
    assert {f["id"] for f in loaded} == {f["id"] for f in items}
    assert r.store.exclusion_dependent >= {"flex.flex-010.burning_rate_constant"}


def test_synthetic_records_never_touch_repository_data(tmp_path):
    build_repo(tmp_path, {"syn-a": consistent()})
    assert not list((REPO / "data").rglob("syn-a*"))
