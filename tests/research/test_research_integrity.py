"""Cross-cutting integrity checks for the Member 5 research package and content."""

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from flameguard.api.app import app

ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DOCS = ROOT / "docs" / "research" / "member5"
PACKAGE = ROOT / "backend" / "flameguard" / "research"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_research_package_never_imports_simulation_or_api_code():
    for path in PACKAGE.glob("*.py"):
        for name in _imports(path):
            assert "simulation" not in name, (path.name, name)
            assert not name.startswith("flameguard.api"), (path.name, name)


def test_research_content_has_no_nasa_misattribution_or_fixtures():
    for path in RESEARCH_DOCS.glob("*"):
        text = path.read_text(encoding="utf-8").lower()
        assert "according to nasa" not in text, path.name
        assert '"fixture": true' not in text, path.name


def test_register_imports_no_measurements_and_every_entry_is_cited(register, real_evidence):
    investigations = {i["id"] for i in register if i["record_type"] == "investigation"}
    assert investigations == {"bass-ii", "flex", "sofie", "saffire", "fm2"}
    assert {i["record_type"] for i in register} == {"investigation", "research_synthesis"}
    for inv in register:
        assert inv["member5"]["measured_records_imported"] == 0
        assert any(s["quote"] for s in inv["sources"]), inv["id"]
        assert all(s["url"].startswith("https://") for s in inv["sources"])
    assert {r["investigation_id"] for r in real_evidence} <= {i["id"] for i in register}


def test_dataset_dois_are_recorded_only_where_verified(register):
    by_id = {i["id"]: i["member5"] for i in register}
    assert by_id["bass-ii"]["dataset_doi"] == "10.60555/4qc4-de67"
    assert by_id["bass-ii"]["psi_id"] == "PSI-25"
    assert by_id["flex"]["dataset_doi"] == "10.60555/mbq8-0451"
    assert by_id["flex"]["psi_id"] == "PSI-69"
    for key in ("sofie", "saffire", "fm2", "partial-gravity-synthesis"):
        assert by_id[key]["dataset_doi"] is None, key


def test_saffire_findings_do_not_cite_other_flights_datasets(register, real_evidence):
    saffire = next(i for i in register if i["id"] == "saffire")
    other = {d["psi_id"] for d in saffire["member5"]["psi_datasets_other_flights"]}
    assert other == {"PSI-98", "PSI-99", "PSI-100"}
    for rec in real_evidence:
        if rec["investigation_id"] == "saffire":
            for src in rec["sources"]:
                assert "psi.nasa.gov" not in src["url"], rec["id"]


def test_synthesis_is_not_presented_as_a_nasa_finding(register, real_evidence):
    synth = next(i for i in register if i["record_type"] == "research_synthesis")
    assert "not a NASA finding" in synth["member5"]["verification"]
    rec = next(r for r in real_evidence if r["investigation_id"] == synth["id"])
    assert rec["source_claim_strength"] == "source_statement"
    assert any("not a NASA finding" in lim for lim in rec["limitations"])


def test_every_card_maps_to_the_kickoff(real_cards):
    refs = " ".join(c["kickoff_ref"] for c in real_cards)
    for ref in ("M5-I01", "M5-I02", "M5-I03", "M5-I04", "D1", "D2", "D3", "D4", "D5"):
        assert ref in refs, ref


def test_api_contract_is_unchanged_by_this_package():
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    resp = client.get("/api/rankings")
    assert resp.status_code == 501
    assert resp.json()["error"]["code"] == "not_implemented"
