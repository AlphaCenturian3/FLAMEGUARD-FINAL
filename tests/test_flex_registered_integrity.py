"""Integrity of the derived FLEX files once they are registered (and a guard while they are not).

Two states, one file:
- NOT REGISTERED (today on main): there must be no derived file and no derived manifest entry, and
  never half of them. Everything else here is skipped with a clear reason.
- REGISTERED (the registration PR): the files must match the manifest hashes, be byte-identical to a
  fresh run of tools/derive_flex_findings.py, pass the contract schemas, S1/S4, S9, S11 and the
  provenance checker, keep the excluded number out of the data, pass the audit, and **every gate in
  tools/flex_derivation_gates.json must be closed and every condition decision approved**. The last
  test is a deliberate red light: registration with an open scientific gate cannot have a green CI.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
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
prov = _load("check_data_provenance", "tools/check_data_provenance.py")
excl = _load("exclusion_oracle", "tests/test_exclusion_dependency.py")
cmpo = _load("comparability_oracle", "tests/test_comparability_outcome.py")
adv = _load("audit_adversarial_helpers", "tests/test_flex_audit_adversarial.py")

FINDINGS_REL = "data/curated/findings/flex.json"
INVESTIGATIONS_REL = "data/curated/investigations.json"
FINDINGS_FILE, INVESTIGATIONS_FILE = ROOT / FINDINGS_REL, ROOT / INVESTIGATIONS_REL
DERIVED_IDS = {dv.FINDINGS_ID, dv.INVESTIGATIONS_ID}
PRINTED = re.compile(r"(?<![\d.])0?\.37(?!\d)")

MANIFEST = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
ENTRIES = {e["id"]: e for e in MANIFEST["datasets"]}
REGISTERED = (
    FINDINGS_FILE.is_file() or INVESTIGATIONS_FILE.is_file() or bool(DERIVED_IDS & set(ENTRIES))
)
needs_registration = pytest.mark.skipif(
    not REGISTERED, reason="NOT REGISTERED: no derived FLEX file or manifest entry exists"
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------
# While not registered
# ---------------------------------------------------------------------------------------------


@pytest.mark.skipif(REGISTERED, reason="registered state: see the tests below")
def test_nothing_derived_is_registered_and_the_source_entries_are_unchanged():
    assert not FINDINGS_FILE.exists() and not INVESTIGATIONS_FILE.exists()
    assert [e["id"] for e in MANIFEST["datasets"]] == [dv.CSV_ID, dv.FLAGS_ID]


# ---------------------------------------------------------------------------------------------
# Once registered
# ---------------------------------------------------------------------------------------------


@needs_registration
def test_registration_is_all_or_nothing_and_only_these_paths():
    assert FINDINGS_FILE.is_file() and INVESTIGATIONS_FILE.is_file()
    assert DERIVED_IDS <= set(ENTRIES), "both manifest entries must exist"
    assert ENTRIES[dv.FINDINGS_ID]["path"] == FINDINGS_REL
    assert ENTRIES[dv.INVESTIGATIONS_ID]["path"] == INVESTIGATIONS_REL
    assert [e["id"] for e in MANIFEST["datasets"][:2]] == [dv.CSV_ID, dv.FLAGS_ID]
    assert {e["id"] for e in MANIFEST["datasets"]} == {dv.CSV_ID, dv.FLAGS_ID} | DERIVED_IDS
    curated = {
        p.relative_to(ROOT).as_posix() for p in (ROOT / "data/curated").rglob("*") if p.is_file()
    }
    allowed = {
        ENTRIES[dv.CSV_ID]["path"],
        ENTRIES[dv.FLAGS_ID]["path"],
        FINDINGS_REL,
        INVESTIGATIONS_REL,
    }
    assert curated - {"data/curated/.gitkeep"} == allowed, (
        "only the two sources and the two derived files"
    )


@needs_registration
def test_sha256_and_entry_fields_match_the_files_and_the_table_ix_source():
    csv_entry = ENTRIES[dv.CSV_ID]
    numeric = [s for s in csv_entry["sources"] if str(s["page"]) == "20"]
    assert len(numeric) == 1
    for entry_id, rel in (
        (dv.FINDINGS_ID, FINDINGS_REL),
        (dv.INVESTIGATIONS_ID, INVESTIGATIONS_REL),
    ):
        e = ENTRIES[entry_id]
        assert e["sha256"] == dv.sha256_file(ROOT / rel), entry_id
        assert e["evidence_class"] == "measured"
        assert e["sources"] == numeric, (
            "numeric provenance only; caution passages stay on the notes"
        )
        assert e["rights_status"] == csv_entry["rights_status"]
        assert "tools/derive_flex_findings.py" in e["description"]
    # the originals are untouched: their registered hashes still match their bytes
    for entry_id in (dv.CSV_ID, dv.FLAGS_ID):
        assert ENTRIES[entry_id]["sha256"] == dv.sha256_file(ROOT / ENTRIES[entry_id]["path"])


@needs_registration
def test_the_registered_files_are_byte_identical_to_a_fresh_derivation():
    fresh = dv.derive(ROOT)
    assert fresh["withheld"] == []
    assert FINDINGS_FILE.read_text(encoding="utf-8") == dv.dumps(fresh["findings"])
    assert INVESTIGATIONS_FILE.read_text(encoding="utf-8") == dv.dumps([fresh["investigation"]])


@needs_registration
def test_the_provenance_checker_accepts_the_manifest():
    assert prov.check_manifest(MANIFEST, ROOT) == []


@needs_registration
def test_schema_s1_s4_and_exactly_40_findings_in_one_investigation(validator_for):
    findings, investigations = load(FINDINGS_FILE), load(INVESTIGATIONS_FILE)
    fv, iv = validator_for("finding.schema.json"), validator_for("investigation.schema.json")
    assert len(findings) == 40 and len(investigations) == 1
    for f in findings:
        assert not list(fv.iter_errors(f)), f["id"]
        assert f["provenance"]["manifest_id"] == dv.FINDINGS_ID  # S1
        assert f["investigation_id"] == investigations[0]["id"] == "flex"  # S2
    assert not list(iv.iter_errors(investigations[0]))
    assert investigations[0]["datasets"] == [dv.FINDINGS_ID]  # S4
    assert len({f["id"] for f in findings}) == 40
    assert sum(f["value_status"] == "excluded" for f in findings) == 1


@needs_registration
def test_s9_s11_and_the_excluded_number_stay_safe_in_the_registered_data():
    findings = load(FINDINGS_FILE)
    assert excl.exclusion_dependent_ids(findings) == {"flex.flex-010.burning_rate_constant"}
    assert cmpo.identity_violations(findings) == []
    text = FINDINGS_FILE.read_text(encoding="utf-8") + INVESTIGATIONS_FILE.read_text(
        encoding="utf-8"
    )
    assert not PRINTED.search(text), "the excluded printed value is in the registered data"
    f = next(x for x in findings if x["id"] == "flex.flex-010.burning_rate_constant")
    assert f["value"] is None and f["value_status"] == "excluded"
    assert [n["kind"] for n in f["curation_notes"]] == ["caution", "exclusion"]


@needs_registration
def test_the_complete_40_finding_audit_passes_on_the_registered_files(tmp_path):
    staged = tmp_path / "staged"
    (staged / "findings").mkdir(parents=True)
    (staged / "findings" / "flex.json").write_bytes(FINDINGS_FILE.read_bytes())
    (staged / "investigations.json").write_bytes(INVESTIGATIONS_FILE.read_bytes())
    report = au.audit(staged, ROOT, adv.synthetic_pages(), adv.synthetic_rows())
    assert report["passed"], report["failures"][:3]
    assert report["summary"]["findings"] == 40 and report["summary"]["notes_checked"] == 96


@needs_registration
def test_pdf_the_audit_passes_against_the_real_source_on_the_registered_files(tmp_path):
    if not au.vft.DEFAULT_PDF.is_file():
        pytest.skip("NOT VERIFIED: data/raw/NASA-TP-2015-216046_FLEX.pdf is not present")
    pymupdf = pytest.importorskip("pymupdf", reason="NOT VERIFIED: PyMuPDF is not installed")
    doc = pymupdf.open(au.vft.DEFAULT_PDF)

    def page_text(printed):
        return doc[printed + au.vft.PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()

    staged = tmp_path / "staged"
    (staged / "findings").mkdir(parents=True)
    (staged / "findings" / "flex.json").write_bytes(FINDINGS_FILE.read_bytes())
    (staged / "investigations.json").write_bytes(INVESTIGATIONS_FILE.read_bytes())
    report = au.audit(staged, ROOT, page_text, au.source_rows_from_pdf(page_text))
    assert report["passed"], report["failures"][:3]
    assert report["summary"]["quotes_verified_in_pdf"] == 96


@needs_registration
def test_registration_requires_every_gate_closed_and_every_condition_approved():
    """The deliberate red light: an open scientific gate means this must not be registered."""
    gates = load(ROOT / "tools" / "flex_derivation_gates.json")
    open_gates = [g["id"] for g in gates["gates"] if g["status"] != "closed"]
    unapproved = [k for k, c in gates["conditions"].items() if c["status"] != "approved"]
    assert not open_gates and not unapproved, (
        f"registration is not allowed yet: open gates {open_gates}, "
        f"condition decisions not independently approved {unapproved}"
    )
