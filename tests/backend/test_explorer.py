"""B2 evidence explorer endpoints.

All data is SYNTHETIC (tests/backend/conftest.py) and lives in temp folders. Every response is
validated against the real contract schemas, so the API cannot drift from the contract.
"""

import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import SOURCE, example, interpretation, investigation, measured
from flameguard import CONTRACT_VERSION
from flameguard.api.app import create_app
from flameguard.api.explorer import REJECTED_HEADER, EvidenceSource
from flameguard.data import load_evidence

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def client_for(scenario):
    def make(**kwargs):
        root = scenario.write()
        return TestClient(create_app(EvidenceSource(root)), **kwargs), root

    return make


def _error_ok(validator_for, response, status, code):
    assert response.status_code == status, response.text
    validator_for("error.schema.json").validate(response.json())
    assert response.json()["error"]["code"] == code


# --- Investigations ---


def test_list_investigations_matches_the_contract(client_for, validator_for):
    client, _ = client_for()
    r = client.get("/api/investigations")
    assert r.status_code == 200
    body = r.json()
    validator_for("investigation_list.schema.json").validate(body)
    assert body["contract_version"] == CONTRACT_VERSION
    assert [i["id"] for i in body["items"]] == ["inv-a"] and body["total"] == 1


def test_investigations_are_sorted_by_id(scenario, validator_for):
    scenario.investigations = [investigation(i, []) for i in ("inv-c", "inv-a", "inv-b")]
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    ids = [i["id"] for i in client.get("/api/investigations").json()["items"]]
    assert ids == ["inv-a", "inv-b", "inv-c"]


def test_get_one_investigation(client_for, validator_for):
    client, _ = client_for()
    r = client.get("/api/investigations/inv-a")
    assert r.status_code == 200
    validator_for("investigation.schema.json").validate(r.json())
    assert r.json()["id"] == "inv-a" and r.json()["sources"]  # provenance is served


def test_unknown_investigation_is_404(client_for, validator_for):
    client, _ = client_for()
    for bad in ("nope", "Bad%20Id", "inv-a%2F..", "INV-A"):
        _error_ok(validator_for, client.get(f"/api/investigations/{bad}"), 404, "not_found")


def test_investigation_endpoints_reject_query_parameters(client_for, validator_for):
    client, _ = client_for()
    _error_ok(validator_for, client.get("/api/investigations?x=1"), 400, "invalid_request")
    _error_ok(validator_for, client.get("/api/investigations/inv-a?x=1"), 400, "invalid_request")


# --- Findings: listing, evidence classes, provenance ---


def test_list_findings_matches_the_contract_and_keeps_every_class(client_for, validator_for):
    client, _ = client_for()
    body = client.get("/api/findings").json()
    validator_for("finding_list.schema.json").validate(body)
    assert [f["id"] for f in body["items"]] == ["e1", "ex1", "i1", "m1"]  # sorted by id
    assert body["total"] == len(body["items"])
    assert {f["evidence_class"] for f in body["items"]} == {"measured", "interpretation"}


def test_findings_carry_their_provenance_and_conditions(client_for):
    client, _ = client_for()
    m1 = next(f for f in client.get("/api/findings").json()["items"] if f["id"] == "m1")
    assert m1["provenance"]["manifest_id"] == "ds-a" and m1["provenance"]["sources"]
    assert m1["provenance"]["locator"] and "conditions" in m1


def test_filter_by_evidence_class(client_for, validator_for):
    client, _ = client_for()
    for cls, expected in (("measured", ["ex1", "m1"]), ("interpretation", ["e1", "i1"])):
        body = client.get(f"/api/findings?evidence_class={cls}").json()
        validator_for("finding_list.schema.json").validate(body)
        assert [f["id"] for f in body["items"]] == expected


def test_filter_by_investigation(scenario, validator_for):
    scenario.investigations.append(investigation("inv-b", ["ds-b"]))
    scenario.findings["inv-b"] = [measured("m2", "inv-b", "ds-b")]
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    only_b = client.get("/api/findings?investigation_id=inv-b").json()
    validator_for("finding_list.schema.json").validate(only_b)
    assert [f["id"] for f in only_b["items"]] == ["m2"]
    only_a = client.get("/api/findings?investigation_id=inv-a").json()
    assert [f["id"] for f in only_a["items"]] == ["e1", "ex1", "i1", "m1"]


def test_filter_by_quantity_and_combined_filters(client_for, validator_for):
    client, _ = client_for()
    body = client.get("/api/findings?quantity=flame_spread_rate").json()
    assert [f["id"] for f in body["items"]] == ["ex1", "m1"]
    combined = client.get(
        "/api/findings?quantity=flame_spread_rate&evidence_class=measured&investigation_id=inv-a"
    ).json()
    validator_for("finding_list.schema.json").validate(combined)
    assert [f["id"] for f in combined["items"]] == ["ex1", "m1"]


def test_a_valid_filter_with_no_matches_is_an_honest_empty_list(client_for, validator_for):
    client, _ = client_for()
    r = client.get("/api/findings?quantity=flame_temperature")  # in the vocabulary, none loaded
    assert r.status_code == 200
    validator_for("finding_list.schema.json").validate(r.json())
    assert r.json()["items"] == [] and r.json()["total"] == 0


# --- Findings: bad requests (400 invalid_request) ---


@pytest.mark.parametrize(
    "query",
    [
        "investigation_id=ghost",
        "evidence_class=simulation",
        "evidence_class=illustrative_simulation",
        "evidence_class=Measured",
        "evidence_class=",
        "quantity=made_up_quantity",
        "quantity=burning_rate",
        "color=red",  # unknown parameter name
        "evidence_class=measured&evidence_class=interpretation",  # repeated
        "investigation_id=inv-a&investigation_id=inv-a",
    ],
)
def test_bad_filters_are_400_with_a_contract_error(client_for, validator_for, query):
    client, _ = client_for()
    _error_ok(validator_for, client.get(f"/api/findings?{query}"), 400, "invalid_request")


def test_simulations_are_refused_as_evidence_with_a_clear_reason(client_for):
    client, _ = client_for()
    r = client.get("/api/findings?evidence_class=illustrative_simulation")
    assert r.status_code == 400 and "Simulations are not evidence" in r.json()["error"]["message"]


# --- Exclusion and missing-data handling ---


def test_excluded_findings_are_listed_as_excluded_with_a_null_value(client_for, validator_for):
    client, _ = client_for()
    ex1 = next(f for f in client.get("/api/findings").json()["items"] if f["id"] == "ex1")
    assert ex1["value_status"] == "excluded" and ex1["value"] is None
    assert any(
        n["kind"] == "exclusion" for n in ex1["curation_notes"]
    )  # the reason travels with it


def test_missing_values_are_reported_as_missing_never_filled(scenario, validator_for):
    missing = example("finding.measured_missing.example.json")
    missing.update(id="miss1", investigation_id="inv-a", statement="SYNTHETIC missing value")
    missing["provenance"] = {
        "manifest_id": "ds-a",
        "locator": "SYNTHETIC miss1",
        "sources": [SOURCE],
    }
    scenario.findings["inv-a"].append(missing)
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    body = client.get("/api/findings?quantity=flame_spread_rate").json()
    validator_for("finding_list.schema.json").validate(body)
    row = next(f for f in body["items"] if f["id"] == "miss1")
    assert row["value_status"] == "not_reported" and row["value"] is None


def test_exclusion_dependent_interpretations_are_listed_as_interpretations(client_for):
    """S9: allowed only to explain the exclusion, and carrying no value of their own."""
    client, _ = client_for()
    e1 = next(
        f
        for f in client.get("/api/findings?evidence_class=interpretation").json()["items"]
        if f["id"] == "e1"
    )
    assert e1["value"] is None and e1["quantity"] is None and "relevant_environments" not in e1


# --- Fail closed: rejected data, unreadable manifest ---


def test_a_rejected_file_is_never_served_and_the_omission_is_visible(scenario, caplog):
    scenario.tamper["ds-notes"] = "0" * 64  # provenance fails: the interpretations file is rejected
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    with caplog.at_level(logging.WARNING, logger="flameguard.api.explorer"):
        r = client.get("/api/findings")
    ids = [f["id"] for f in r.json()["items"]]
    assert ids == ["ex1", "m1"] and {"i1", "e1"}.isdisjoint(ids)
    assert r.headers[REJECTED_HEADER] == "1"
    assert any("ds-notes" in rec.message and "rejected" in rec.message for rec in caplog.records)


def test_no_rejection_header_when_everything_loaded(client_for):
    client, _ = client_for()
    assert REJECTED_HEADER not in client.get("/api/findings").headers


def test_unreadable_manifest_is_503_for_every_explorer_endpoint(scenario, validator_for):
    scenario.raw["data/manifest.json"] = '{"manifest_version": "0.2.0", "datasets": [], "x": NaN}'
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    for path in ("/api/investigations", "/api/investigations/inv-a", "/api/findings"):
        _error_ok(validator_for, client.get(path), 503, "unavailable")
    assert client.get("/api/health").status_code == 200  # the service itself is up


def test_a_loader_crash_becomes_a_clean_503_not_a_500(scenario, validator_for, monkeypatch):
    source = EvidenceSource(scenario.write())
    monkeypatch.setattr(source, "load", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    client = TestClient(create_app(source), raise_server_exceptions=False)
    _error_ok(validator_for, client.get("/api/findings"), 503, "unavailable")


def test_unreadable_vocabulary_is_503_only_when_a_quantity_filter_is_used(scenario, validator_for):
    root = scenario.write()
    (root / "contracts" / "vocabulary.json").unlink()
    client = TestClient(create_app(EvidenceSource(root)))
    assert client.get("/api/findings").status_code == 200
    _error_ok(
        validator_for, client.get("/api/findings?quantity=flame_spread_rate"), 503, "unavailable"
    )


# --- Isolation: simulations and fixtures are never evidence ---


def test_simulation_entries_and_their_content_are_never_served(scenario):
    finding_like = measured("sim-m1", "inv-a", "ds-a")
    scenario.extra_entries.append(
        {
            "id": "sim",
            "path": "data/simulated/run.json",
            "evidence_class": "illustrative_simulation",
            "text": json.dumps([finding_like]),
            "model": "m",
            "model_version": "0",
            "label": "Fluid and thermal transport model. No combustion chemistry.",
        }
    )
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    assert "sim-m1" not in {f["id"] for f in client.get("/api/findings").json()["items"]}


def test_fixture_flagged_data_is_never_served(scenario):
    scenario.findings["inv-a"][0]["fixture"] = True  # the loader rejects the whole file
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    body = client.get("/api/findings").json()
    assert all("fixture" not in f for f in body["items"]) and "m1" not in {
        f["id"] for f in body["items"]
    }


def test_the_real_repository_is_served_honestly_whatever_is_registered():
    """With the data registered on this branch (possibly none) the API serves exactly what the
    loader accepts: no fixtures, no contract examples, nothing invented."""
    client = TestClient(create_app(EvidenceSource(REPO)))
    expected = load_evidence(REPO).store
    findings = client.get("/api/findings").json()
    assert {f["id"] for f in findings["items"]} == set(expected.findings)
    assert [i["id"] for i in client.get("/api/investigations").json()["items"]] == sorted(
        i["id"] for i in expected.investigations
    )
    assert all(not f["id"].startswith("fixture-") for f in findings["items"])


# --- The rest of the contract is unchanged ---


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/compare?quantity=flame_spread_rate"),
        ("GET", "/api/rankings?context=spacecraft"),
        ("POST", "/api/assistant/ask"),
        ("GET", "/api/simulations/x"),
    ],
)
def test_unfinished_endpoints_stay_501(client_for, validator_for, method, path):
    client, _ = client_for()
    _error_ok(validator_for, client.request(method, path), 501, "not_implemented")


def test_framework_errors_are_contract_errors_too(client_for, validator_for):
    client, _ = client_for()
    _error_ok(validator_for, client.get("/api/does-not-exist"), 404, "not_found")
    _error_ok(validator_for, client.post("/api/findings"), 405, "invalid_request")


def test_apps_do_not_share_evidence(scenario, tmp_path):
    """Two applications over different repositories must not see each other's data."""
    from conftest import Scenario

    other = Scenario(tmp_path / "other")
    other.investigations = [investigation("inv-z", [])]
    other.findings = {}
    other.interps = {}
    a = TestClient(create_app(EvidenceSource(scenario.write())))
    z = TestClient(create_app(EvidenceSource(other.write())))
    assert [i["id"] for i in a.get("/api/investigations").json()["items"]] == ["inv-a"]
    assert [i["id"] for i in z.get("/api/investigations").json()["items"]] == ["inv-z"]


def test_responses_do_not_alias_the_loaded_store(client_for):
    client, _ = client_for()
    first = client.get("/api/findings").json()
    first["items"][0]["statement"] = "TAMPERED"
    assert client.get("/api/findings").json()["items"][0]["statement"] != "TAMPERED"


def test_evidence_is_loaded_once_and_refresh_reloads(scenario, monkeypatch):
    calls = []
    import flameguard.api.explorer as explorer

    real = explorer.load_evidence
    monkeypatch.setattr(explorer, "load_evidence", lambda root: calls.append(1) or real(root))
    source = EvidenceSource(scenario.write())
    client = TestClient(create_app(source))
    client.get("/api/findings")
    client.get("/api/investigations")
    assert len(calls) == 1
    source.refresh()
    assert len(calls) == 2


def test_explorer_imports_no_simulation_research_preview_or_tools_code():
    import re

    text = (REPO / "backend" / "flameguard" / "api" / "explorer.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+\S*(simulat|research|preview|tools)", text, re.M)
    app_text = (REPO / "backend" / "flameguard" / "api" / "app.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+\S*(simulat|research|preview|tools)", app_text, re.M)


def test_interpretation_helper_still_builds_a_valid_interpretation():
    """Guards the shared builders this file relies on."""
    assert interpretation("i9", "inv-a", ["m1"])["evidence_class"] == "interpretation"
