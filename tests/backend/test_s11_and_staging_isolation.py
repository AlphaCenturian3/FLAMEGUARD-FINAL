"""S11 (test identity is all-or-nothing) in the B1 loader, and isolation of staged FLEX output.

All data is SYNTHETIC and lives in temp folders. The FLEX derivation (a separate branch) writes
a staging folder that is not registered in data/manifest.json; these tests show that nothing
outside the manifest can reach the live API, and that the planned endpoints (compare, rankings,
assistant) stay HTTP 501 whatever files exist on disk.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from conftest import investigation, measured
from flameguard.api.app import create_app
from flameguard.api.explorer import REJECTED_HEADER, EvidenceSource
from flameguard.data import load_evidence

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "comparability_oracle", REPO / "tests" / "test_comparability_outcome.py"
)
oracle = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = oracle
_spec.loader.exec_module(oracle)

OUTCOME = "Extinction"  # a CONFIRMED value in contracts/outcomes.json


def finding(fid, inv="inv-a", test_id=None, outcome=None, **extra):
    extra.setdefault("test_id", test_id)
    extra.setdefault("test_outcome", outcome)
    return measured(fid, inv, "ds-a" if inv == "inv-a" else "ds-b", **extra)


def only(scenario, *findings, inv="inv-a"):
    scenario.findings = {inv: list(findings)}
    scenario.interps = {}
    return scenario


def load(scenario):
    return load_evidence(scenario.write())


def rejection(result, entry_id="ds-a"):
    entry = next(e for e in result.report.entries if e.id == entry_id)
    return entry.status.value, " | ".join(entry.reasons)


# ---------------------------------------------------------------------------------------------
# S11
# ---------------------------------------------------------------------------------------------


def test_a_fully_identified_investigation_loads(scenario):
    only(scenario, finding("m1", test_id="T-1", outcome=OUTCOME), finding("m2", test_id="T-2"))
    result = load(scenario)
    assert rejection(result)[0] == "accepted" and set(result.store.findings) == {"m1", "m2"}


def test_one_unidentified_finding_rejects_the_whole_file(scenario):
    only(scenario, finding("m1", test_id="T-1", outcome=OUTCOME), finding("m2"))
    result = load(scenario)
    status, reasons = rejection(result)
    assert status == "rejected"
    assert "S11: m2: no test_id, but other findings of this investigation have one" in reasons
    assert "S11: m1" not in reasons and not result.store.findings, "nothing partial is served"


def test_an_outcome_without_a_test_id_is_rejected(scenario):
    only(scenario, finding("m1", outcome=OUTCOME))
    status, reasons = rejection(load(scenario))
    assert status == "rejected" and "S11: m1: has a test_outcome but no test_id" in reasons


def test_a_null_test_id_is_not_an_identity(scenario):
    only(scenario, finding("m1", test_id="T-1"), finding("m2", test_id=None, outcome=OUTCOME))
    status, reasons = rejection(load(scenario))
    assert status == "rejected" and "m2" in reasons


def test_no_identity_anywhere_is_still_valid_a_documented_limit(scenario):
    only(scenario, finding("m1"), finding("m2"))
    assert rejection(load(scenario))[0] == "accepted"


def test_a_rejected_investigation_does_not_affect_another(scenario):
    scenario.investigations = [investigation("inv-a", ["ds-a"]), investigation("inv-b", ["ds-b"])]
    scenario.findings = {
        "inv-a": [finding("a1", test_id="T-1"), finding("a2")],
        "inv-b": [finding("b1", inv="inv-b", test_id="T-1")],
    }
    scenario.interps = {}
    result = load(scenario)
    assert rejection(result, "ds-a")[0] == "rejected" and rejection(result, "ds-b")[0] == "accepted"
    assert set(result.store.findings) == {"b1"}


def test_the_loader_agrees_with_the_contract_oracle_on_every_identity_pattern(tmp_path, scenario):
    states = [(False, False), (True, False), (True, True), (False, True)]  # (has id, has outcome)
    for n, combo in enumerate(itertools.product(states, repeat=3)):
        items = []
        for i, (has_id, has_outcome) in enumerate(combo):
            items.append(
                finding(
                    f"m{i}",
                    test_id=f"T-{i}" if has_id else None,
                    outcome=OUTCOME if has_outcome else None,
                )
            )
        scenario.root = tmp_path / str(n)
        scenario.findings = {"inv-a": items}
        scenario.interps = {}
        result = load_evidence(scenario.write())
        violations = oracle.identity_violations(items)
        assert (rejection(result)[0] == "rejected") == bool(violations), (combo, violations)


def test_s11_rejection_is_visible_through_the_api(scenario):
    only(scenario, finding("m1", test_id="T-1"), finding("m2"))
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    r = client.get("/api/findings")
    assert r.status_code == 200 and r.json()["items"] == []
    assert r.headers[REJECTED_HEADER] == "1", "the omission is flagged, never silent"


# ---------------------------------------------------------------------------------------------
# Staged FLEX output cannot enter the live API
# ---------------------------------------------------------------------------------------------

STAGED = [
    "staging/findings/flex.json",  # where the derivation tool is told to write
    "staging/investigations.json",
    "data/staging/findings/flex.json",
    "data/curated/findings/flex.json",  # the future registered path, but not registered
    "data/curated/investigations.flex.json",
    "data/curated/interpretations/flex-notes.json",
]


def staged_lookalike():
    doc = measured("flex.flex-010.burn_time", "flex", "nasa-tp-2015-216046.flex.findings")
    doc["statement"] = "SYNTHETIC staged lookalike. Not NASA data."
    doc.update(test_id="FLEX-010", test_outcome=OUTCOME)
    return [doc]


def scatter(root: Path) -> None:
    for rel in STAGED:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(staged_lookalike())
        path.write_text(text, encoding="utf-8")
    (root / "staging" / "STAGING_REPORT.json").write_text(
        '{"registrable": false}', encoding="utf-8"
    )


def test_unregistered_staged_files_never_reach_the_store_or_the_api(scenario):
    only(scenario, finding("m1", test_id="T-1"))
    root = scenario.write()
    scatter(root)
    result = load_evidence(root)
    assert set(result.store.findings) == {"m1"}
    assert not [i for i in result.store.investigations if i["id"] == "flex"]
    client = TestClient(create_app(EvidenceSource(root)))
    ids = [f["id"] for f in client.get("/api/findings").json()["items"]]
    assert ids == ["m1"]
    assert client.get("/api/investigations/flex").status_code == 404
    assert client.get("/api/findings?investigation_id=flex").status_code == 400
    assert REJECTED_HEADER not in client.get("/api/findings").headers


def test_with_nothing_registered_the_api_stays_honestly_empty_whatever_is_staged(scenario):
    only(scenario)
    scenario.investigations = []
    root = scenario.write()
    scatter(root)
    client = TestClient(create_app(EvidenceSource(root)))
    for path in ("/api/investigations", "/api/findings"):
        body = client.get(path).json()
        assert body["items"] == [] and body["total"] == 0


def registered_ids(kind):
    """Ids inside the Findings/investigation files that the shipped manifest registers."""
    manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))
    ids = set()
    for entry in manifest["datasets"]:
        path = entry["path"]
        is_inv = path == "data/curated/investigations.json"
        is_finding = path.startswith(("data/curated/findings/", "data/curated/interpretations/"))
        if (kind == "investigations" and is_inv) or (kind == "findings" and is_finding):
            ids |= {item["id"] for item in json.loads((REPO / path).read_text(encoding="utf-8"))}
    return ids


def test_the_real_repository_serves_exactly_what_its_manifest_registers():
    """Registered evidence is served, and nothing else: not staged files, not source CSVs.

    Before the FLEX registration this set is empty (the API is honestly empty); once the derived
    files are registered it is the 40 Findings and their investigation. Either way an unregistered
    or staged file can never appear.
    """
    client = TestClient(create_app(EvidenceSource(REPO)))
    findings = client.get("/api/findings").json()
    investigations = client.get("/api/investigations").json()
    assert {f["id"] for f in findings["items"]} == registered_ids("findings")
    assert {i["id"] for i in investigations["items"]} == registered_ids("investigations")
    assert findings["total"] == len(findings["items"])
    assert not [f for f in findings["items"] if f.get("fixture")], "no fixture is ever served"


def test_compare_rankings_and_the_assistant_stay_501_with_staged_files_present(scenario):
    only(scenario, finding("m1", test_id="T-1"))
    root = scenario.write()
    scatter(root)
    client = TestClient(create_app(EvidenceSource(root)))
    for method, path in (
        ("get", "/api/compare?quantity=burn_time"),
        ("get", "/api/rankings?context=spacecraft"),
        ("post", "/api/assistant/ask"),
        ("get", "/api/simulations/flex.flex-010.burn_time"),
    ):
        r = getattr(client, method)(path)
        assert r.status_code == 501, path
        assert r.json()["error"]["code"] == "not_implemented"
        assert "flex" not in r.text.lower().replace("not implemented", "")


def test_a_registered_file_in_the_staging_folder_is_still_checked_like_any_evidence(scenario):
    """Registering a staged file is the only way in, and then every rule applies (here S11)."""
    only(scenario, finding("m1", test_id="T-1"))
    scenario.extra_entries = []
    root = scenario.write()
    bad = [finding("s1", test_id="T-9"), finding("s2")]
    path = root / "data/curated/findings/inv-a.json"
    bad_text = json.dumps(bad)
    path.write_text(bad_text, encoding="utf-8")
    manifest_path = root / "data/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for e in manifest["datasets"]:
        if e["path"].endswith("inv-a.json"):
            e["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_text = json.dumps(manifest)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    result = load_evidence(root)
    assert "S11" in rejection(result)[1] and not result.store.findings


# ---------------------------------------------------------------------------------------------
# Adversarial: attempts to get staged files in through the manifest
# ---------------------------------------------------------------------------------------------


def register(scenario, entry_id, rel, evidence_class, **fields):
    text = json.dumps(staged_lookalike())
    scenario.extra_entries.append(
        {"id": entry_id, "path": rel, "evidence_class": evidence_class, "text": text, **fields}
    )


def served_ids(scenario):
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    return [f["id"] for f in client.get("/api/findings").json()["items"]], client


def test_registering_a_staged_file_outside_data_curated_makes_the_whole_manifest_unservable(
    scenario,
):
    """Fail closed: the manifest schema refuses the path, so nothing at all is served (503)."""
    only(scenario, finding("m1", test_id="T-1"))
    register(
        scenario,
        "ds-staged",
        "staging/findings/flex.json",
        "measured",
        sources=[
            {"title": "SYNTHETIC", "url": "https://example.invalid/s", "retrieved": "2026-11-14"}
        ],
        rights_status="under_review",
    )
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    for path in ("/api/findings", "/api/investigations"):
        r = client.get(path)
        assert r.status_code == 503 and r.json()["error"]["code"] == "unavailable"
        assert "flex.flex-010" not in r.text


def test_a_staged_file_under_an_unrecognised_curated_path_is_rejected_not_served(scenario):
    only(scenario, finding("m1", test_id="T-1"))
    register(
        scenario,
        "ds-staged",
        "data/curated/staging/flex.json",
        "measured",
        sources=[
            {"title": "SYNTHETIC", "url": "https://example.invalid/s", "retrieved": "2026-11-14"}
        ],
        rights_status="under_review",
    )
    ids, client = served_ids(scenario)
    assert ids == ["m1"]
    status, reasons = rejection(load_evidence(scenario.root), "ds-staged")
    assert status == "rejected" and "not a recognized evidence document" in reasons
    assert client.get("/api/findings").headers[REJECTED_HEADER] == "1"


def test_a_staged_file_registered_as_a_simulation_is_never_opened_or_served(scenario):
    only(scenario, finding("m1", test_id="T-1"))
    register(
        scenario,
        "ds-sim",
        "data/simulated/flex.json",
        "illustrative_simulation",
        model="SYNTHETIC",
        model_version="0",
        label="Fluid and thermal transport model. No combustion chemistry.",
    )
    ids, _ = served_ids(scenario)
    assert ids == ["m1"]
    status, reasons = rejection(load_evidence(scenario.root), "ds-sim")
    assert status == "skipped" and "never evidence" in reasons


def test_a_staged_file_registered_as_an_interpretation_of_nothing_is_rejected(scenario):
    only(scenario, finding("m1", test_id="T-1"))
    register(
        scenario,
        "ds-fake",
        "data/curated/interpretations/flex.json",
        "interpretation",
        derived_from=["ds-a"],
        method="SYNTHETIC",
    )
    ids, _ = served_ids(scenario)
    assert "flex.flex-010.burn_time" not in ids, (
        "a measured staged finding cannot pose as an interpretation"
    )
    status, reasons = rejection(load_evidence(scenario.root), "ds-fake")
    assert status == "rejected" and "evidence_class must be interpretation" in reasons


def test_a_staged_investigation_cannot_be_reached_by_id_filter_or_path_tricks(scenario):
    only(scenario, finding("m1", test_id="T-1"))
    root = scenario.write()
    scatter(root)
    client = TestClient(create_app(EvidenceSource(root)))
    for path in (
        "/api/investigations/flex",
        "/api/investigations/..%2Fstaging%2Finvestigations",
        "/api/investigations/flex%2Fflex",
        "/api/findings?investigation_id=flex",
        "/api/findings?investigation_id=flex&evidence_class=measured",
        "/api/findings?evidence_class=measured&quantity=burn_time",
    ):
        r = client.get(path)
        text = r.text.lower()
        assert "flex.flex-010" not in text and "synthetic staged" not in text, path
        assert r.status_code in (200, 400, 404), path
    assert client.get("/api/findings?quantity=burn_time").json()["items"] == []
