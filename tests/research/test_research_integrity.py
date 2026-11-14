"""Cross-cutting integrity checks for the Member 5 research package and content."""

import ast
import json
from pathlib import Path

from fastapi.testclient import TestClient

from flameguard.api.app import app

ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DOCS = ROOT / "docs" / "research" / "member5"
PACKAGE = ROOT / "research"
CONTRACT_EXAMPLES = ROOT / "contracts" / "examples"
FIXTURE_FLAGS = ROOT / "tests" / "fixtures" / "research" / "quality_flags.json"
FIXTURE_SOURCE = ROOT / "tests" / "fixtures" / "research" / "quality_flag_source.txt"
FLAG_TO_NOTE_KIND = {"caution": "caution", "exclude": "exclusion"}


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
    assert not (ROOT / "backend" / "flameguard" / "research").exists()
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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _s10_violations(findings, flags_doc, registry, source_text):
    """Independent S10 check over explicit fixtures; it does not certify NASA evidence."""
    manifest_id = flags_doc["manifest_id"]
    manifest_entry = registry.get(manifest_id)
    errors = []
    if not manifest_entry or manifest_entry.get("evidence_class") != "interpretation":
        return [f"quality flags {manifest_id} are not registered as interpretation"]

    flags = {flag["id"]: flag for flag in flags_doc["records"]}
    for finding in findings:
        locator = finding["provenance"]["locator"]
        for note in finding.get("curation_notes", []):
            ref = note.get("flag_ref", {})
            flag = flags.get(ref.get("flag_id"))
            if ref.get("manifest_id") != manifest_id or flag is None:
                errors.append(f"{finding['id']}: unresolved flag_ref")
                continue
            expected_kind = FLAG_TO_NOTE_KIND.get(flag["ranking_use"])
            if expected_kind != note.get("kind"):
                errors.append(f"{finding['id']}: note kind does not match ranking_use")
            if flag["locator"] not in locator:
                errors.append(f"{finding['id']}: flag row does not match locator")
            if flag["field"] not in (finding.get("quantity"), "*"):
                errors.append(f"{finding['id']}: flag field does not match finding")
            quote = flag["source"]["quote"]
            if quote not in source_text:
                errors.append(f"{flag['id']}: quote is absent from the registered fixture source")
            if note.get("source", {}).get("quote") != quote:
                errors.append(f"{finding['id']}: note quote differs from flag quote")
            if note.get("source", {}).get("page") != flag["source"]["page"]:
                errors.append(f"{finding['id']}: note page differs from flag page")

    for flag in flags_doc["records"]:
        matches = [
            finding
            for finding in findings
            if flag["locator"] in finding["provenance"]["locator"]
            and flag["field"] in (finding.get("quantity"), "*")
        ]
        if not matches:
            errors.append(f"{flag['id']}: no emitted finding matches its row and field")
            continue
        for finding in matches:
            notes = finding.get("curation_notes", [])
            references = [
                note
                for note in notes
                if note.get("flag_ref") == {"manifest_id": manifest_id, "flag_id": flag["id"]}
            ]
            if flag["ranking_use"] in FLAG_TO_NOTE_KIND:
                expected_kind = FLAG_TO_NOTE_KIND[flag["ranking_use"]]
                if not any(note.get("kind") == expected_kind for note in references):
                    errors.append(f"{finding['id']}: missing {expected_kind} note for {flag['id']}")
            elif flag["ranking_use"] == "not_available":
                if finding["value_status"] != "not_reported" or references:
                    errors.append(
                        f"{finding['id']}: not_available must be not_reported without a note"
                    )
            if flag["ranking_use"] == "exclude" and finding["value_status"] != "excluded":
                errors.append(f"{finding['id']}: exclude flag did not make value excluded")
    return errors


def test_s10_flag_mapping_coverage_and_source_quotes_are_independently_traceable():
    flags = _read_json(FIXTURE_FLAGS)
    findings = [
        _read_json(CONTRACT_EXAMPLES / "finding.measured_caution.example.json"),
        _read_json(CONTRACT_EXAMPLES / "finding.measured_excluded.example.json"),
        _read_json(CONTRACT_EXAMPLES / "finding.measured_missing.example.json"),
    ]
    registry = {
        flags["manifest_id"]: {
            "evidence_class": "interpretation",
            "fixture": True,
            "path": str(FIXTURE_FLAGS.relative_to(ROOT)),
        }
    }
    source_text = FIXTURE_SOURCE.read_text(encoding="utf-8")
    assert _s10_violations(findings, flags, registry, source_text) == []


def test_s10_rejects_unresolved_flags_uncovered_rows_and_unverified_quotes():
    flags = _read_json(FIXTURE_FLAGS)
    finding = _read_json(CONTRACT_EXAMPLES / "finding.measured_caution.example.json")
    registry = {flags["manifest_id"]: {"evidence_class": "interpretation", "fixture": True}}
    source_text = FIXTURE_SOURCE.read_text(encoding="utf-8")

    finding["curation_notes"][0]["flag_ref"]["flag_id"] = "missing"
    assert any(
        "unresolved flag_ref" in error
        for error in _s10_violations([finding], flags, registry, source_text)
    )

    finding = _read_json(CONTRACT_EXAMPLES / "finding.measured_caution.example.json")
    finding["curation_notes"] = []
    assert any(
        "missing caution note" in error
        for error in _s10_violations([finding], flags, registry, source_text)
    )

    finding = _read_json(CONTRACT_EXAMPLES / "finding.measured_caution.example.json")
    flags["records"][0]["source"]["quote"] = "Invented fixture quote."
    errors = _s10_violations([finding], flags, registry, source_text)
    assert any("note quote differs" in error for error in errors)
    assert any("quote is absent" in error for error in errors)
