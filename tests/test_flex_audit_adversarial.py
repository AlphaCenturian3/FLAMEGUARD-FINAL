"""Adversarial tests for the staged FLEX Findings (tools/audit_flex_findings.py).

A good audit is one that fails when the output is wrong. Each test takes the real staged output,
damages it in one specific way an error or an attacker could, and requires the audit to report
that exact failure code. CI has no NASA PDF, so the shared fixture feeds the audit source rows
rebuilt from the curated CSV and page texts rebuilt from the repository's recorded quotes (labelled
SYNTHETIC SOURCE below): this proves the audit logic, not the transcription. The tests marked
"pdf" run the audit against the real, checksum-verified PDF and skip with NOT VERIFIED without it.
"""

# ruff: noqa: E501  (long assertion messages and parametrised rows read better unwrapped)
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import shutil
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
vft = au.vft
FLEX10 = "flex.flex-010.burning_rate_constant"


def synthetic_rows():
    """SYNTHETIC SOURCE: Table IX tokens rebuilt from the curated CSV (en dash for blanks)."""
    out = {}
    with (ROOT / vft.CSV_PATH.relative_to(vft.ROOT)).open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            dashes = set(filter(None, r["source_dash_fields"].split(";")))
            row = {c: (vft.SOURCE_DASH if c in dashes else r[c]) for c in vft.TABLE_COLUMNS}
            row["flex_test"] = r["flex_test"].replace("-", "–")
            out[r["flex_test"]] = row
    return out


def synthetic_pages():
    """SYNTHETIC SOURCE: each printed page holds the quotes recorded for it."""
    text: dict[int, list[str]] = {}
    with (ROOT / vft.FLAGS_PATH.relative_to(vft.ROOT)).open(encoding="utf-8", newline="") as fh:
        for fl in csv.DictReader(fh):
            text.setdefault(int(fl["source_printed_page"]), []).append(fl["source_quote"])
    return lambda page: " ".join(text.get(page, []))


@pytest.fixture(scope="module")
def staged(tmp_path_factory):
    out = tmp_path_factory.mktemp("staged") / "out"
    dv.stage(out, ROOT)
    return out


@pytest.fixture(scope="module")
def rows():
    return synthetic_rows()


@pytest.fixture(scope="module")
def pages():
    return synthetic_pages()


def run(staged_dir: Path, rows, pages, mutate=None, mutate_investigations=None, tmp=None):
    """Audit a (possibly damaged) copy of the staged output and return the report."""
    work = Path(tmp) / "copy"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(staged_dir, work)
    path = work / "findings" / "flex.json"
    findings = json.loads(path.read_text(encoding="utf-8"))
    if mutate:
        result = mutate(findings)
        findings = result if isinstance(result, list) else findings
    text = json.dumps(findings)
    path.write_text(text, encoding="utf-8")
    if mutate_investigations:
        ipath = work / "investigations.json"
        inv = json.loads(ipath.read_text(encoding="utf-8"))
        result = mutate_investigations(inv)
        inv = result if isinstance(result, list) else inv
        inv_text = json.dumps(inv)
        ipath.write_text(inv_text, encoding="utf-8")
    return au.audit(work, ROOT, pages, rows)


def codes(report):
    return {f["code"] for f in report["failures"]}


def get(findings, fid):
    return next(f for f in findings if f["id"] == fid)


@pytest.fixture
def caught(staged, rows, pages, tmp_path):
    def check(mutate, expected, **kw):
        report = run(staged, rows, pages, mutate, tmp=tmp_path, **kw)
        assert not report["passed"], "the audit missed the damage"
        assert expected in codes(report), (expected, sorted(codes(report)))
        return report

    return check


# ---------------------------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------------------------


def test_the_undamaged_staged_output_passes_with_the_expected_counts(staged, rows, pages, tmp_path):
    report = run(staged, rows, pages, tmp=tmp_path)
    assert report["passed"], report["failures"][:3]
    s = report["summary"]
    assert s["findings"] == 40 and s["by_value_status"] == {
        "reported": 31,
        "not_reported": 8,
        "excluded": 1,
    }
    assert s["notes_checked"] == 96 and s["quotes_verified_in_pdf"] == 96
    assert report["status"] == "STAGING AUDIT. NOT AN APPROVAL. NOT EVIDENCE."
    assert "INTERNAL AUDIT ONLY" in report["handling"] and "S9" in report["handling"]


def test_every_finding_has_a_complete_machine_readable_acceptance_record(
    staged, rows, pages, tmp_path
):
    report = run(staged, rows, pages, tmp=tmp_path)
    keys = {
        "id",
        "test_id",
        "test_outcome",
        "quantity",
        "unit",
        "source_measurement",
        "value_status",
        "expected_value_status",
        "value",
        "conditions_match_source",
        "applicable_cautions_and_exclusions",
        "not_available_flags",
        "limitations_unresolved",
        "failures",
    }
    assert len(report["findings"]) == 40
    for rec in report["findings"]:
        assert keys <= set(rec), rec["id"]
        assert rec["failures"] == [] and rec["conditions_match_source"] is True
        assert rec["source_measurement"]["pdf_printed_page"] == 20
        assert rec["limitations_unresolved"], "every Finding lists what is still unresolved"
        for n in rec["applicable_cautions_and_exclusions"]:
            assert n["quote_verified_in_pdf"] and n["registered_source_title"]
    ex = next(r for r in report["findings"] if r["id"] == FLEX10)
    assert ex["value"] is None and ex["value_status"] == "excluded"
    assert any("printed number is withheld" in x for x in ex["limitations_unresolved"])
    json.dumps(report)  # strictly serialisable


# ---------------------------------------------------------------------------------------------
# F042 numeric leakage
# ---------------------------------------------------------------------------------------------


def test_leak_value_restored_on_the_excluded_finding(caught):
    caught(lambda fs: get(fs, FLEX10).update(value=0.37), "EXCLUDED_VALUE")


def test_leak_status_flipped_to_reported_with_the_number(caught):
    caught(lambda fs: get(fs, FLEX10).update(value=0.37, value_status="reported"), "STATUS")


@pytest.mark.parametrize("text", ["It reads 0.37.", "about .37 mm2/s", "K=0.37mm2/s", "0.370"])
def test_leak_number_in_the_statement(caught, text):
    caught(lambda fs: get(fs, FLEX10).update(statement=text), "LEAK")


def test_leak_original_audited_reason_restored_in_the_exclusion_note(caught, rows):
    original = dv.load_curated_notes()["F042"]["original_reason"]

    def mutate(fs):
        for n in get(fs, FLEX10)["curation_notes"]:
            if n["flag_ref"]["flag_id"] == "F042":
                n["note"] = original

    report = caught(mutate, "NOTE_TEXT")
    assert "LEAK" in codes(report)


def test_leak_number_in_another_findings_note_locator_or_conditions(caught):
    def in_locator(fs):
        get(fs, "flex.flex-009.burn_time")["provenance"]["locator"] += " (K was .37)"

    caught(in_locator, "LEAK")

    def in_conditions(fs):
        get(fs, "flex.flex-001.burn_time")["conditions"]["diluent"] = "N2 0.37"

    report = caught(in_conditions, "CONDITION")
    assert "LEAK" in codes(report)


def test_leak_number_in_a_caution_note_of_the_excluded_finding(caught):
    def mutate(fs):
        for n in get(fs, FLEX10)["curation_notes"]:
            if n["flag_ref"]["flag_id"] == "F041":
                n["note"] += " Value .37."

    caught(mutate, "LEAK")


# ---------------------------------------------------------------------------------------------
# Incorrect outcomes
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fid", "bad"),
    [
        ("flex.flex-004.burn_time", "Disruption"),
        ("flex.flex-001.visible_flame_extinction_diameter", "Extinction"),  # the tempting "fix"
        ("flex.flex-002.burn_time", None),
        ("flex.flex-003.burn_time", "Burnout"),
        ("flex.flex-007.burn_time", "Completion"),
    ],
)
def test_wrong_or_missing_outcome(caught, fid, bad):
    caught(lambda fs: get(fs, fid).update(test_outcome=bad), "OUTCOME")


# ---------------------------------------------------------------------------------------------
# Missing, wrong or misplaced sources
# ---------------------------------------------------------------------------------------------


def first_note(fs, fid="flex.flex-002.initial_droplet_diameter"):
    return get(fs, fid)["curation_notes"][0]


def test_a_note_is_removed(caught):
    caught(
        lambda fs: get(fs, "flex.flex-006.burn_time").update(
            curation_notes=get(fs, "flex.flex-006.burn_time")["curation_notes"][1:]
        ),
        "NOTE_SET",
    )


def test_a_note_source_title_is_not_registered(caught):
    caught(lambda fs: first_note(fs)["source"].update(title="Invented title"), "NOTE_SOURCE")


def test_a_note_source_quote_differs_from_its_flag(caught):
    caught(lambda fs: first_note(fs)["source"].update(quote="A different sentence."), "NOTE_SOURCE")


def test_a_note_source_page_is_wrong(caught):
    caught(lambda fs: first_note(fs)["source"].update(page="31"), "NOTE_SOURCE")


def test_a_caution_is_backed_by_the_table_ix_numeric_source(caught):
    def mutate(fs):
        first_note(fs)["source"] = copy.deepcopy(
            get(fs, "flex.flex-002.burn_time")["provenance"]["sources"][0]
        )

    report = caught(mutate, "NOTE_SOURCE")
    assert "SEPARATION" in codes(report)


def test_a_flag_quote_that_is_not_on_its_printed_page(staged, rows, tmp_path):
    empty = lambda page: "nothing on this page"  # noqa: E731
    report = run(staged, rows, empty, tmp=tmp_path)
    assert "NOTE_QUOTE" in codes(report) and not report["passed"]


def test_an_unreadable_page_is_a_failure_not_a_pass(staged, rows, tmp_path):
    def broken(page):
        raise IndexError(page)

    assert "NOTE_QUOTE" in codes(run(staged, rows, broken, tmp=tmp_path))


def test_numeric_provenance_is_removed_or_swapped(caught):
    caught(
        lambda fs: get(fs, "flex.flex-005.burn_time")["provenance"].update(sources=[]), "PROVENANCE"
    )

    def swap(fs):
        f = get(fs, "flex.flex-005.burn_time")
        f["provenance"]["sources"] = [copy.deepcopy(first_note(fs)["source"])]

    caught(swap, "PROVENANCE")
    caught(
        lambda fs: get(fs, "flex.flex-005.burn_time")["provenance"].update(
            manifest_id="other.entry"
        ),
        "PROVENANCE",
    )


# ---------------------------------------------------------------------------------------------
# Inconsistent identity and set membership
# ---------------------------------------------------------------------------------------------


def test_test_id_does_not_match_the_finding(caught):
    caught(lambda fs: get(fs, "flex.flex-004.burn_time").update(test_id="FLEX-005"), "IDENTITY")
    caught(lambda fs: get(fs, "flex.flex-004.burn_time").update(test_id=None), "IDENTITY")


def test_locator_names_another_test(caught):
    caught(
        lambda fs: get(fs, "flex.flex-004.burn_time")["provenance"].update(
            locator="Table IX, printed p. 20, FLEX-005, field burn_time_s"
        ),
        "PROVENANCE",
    )


def test_finding_set_is_not_exactly_the_forty(caught):
    caught(lambda fs: fs.pop(), "SET")
    caught(lambda fs: fs.append(copy.deepcopy(fs[0])), "SET")

    def dup(fs):
        fs[1]["id"] = fs[0]["id"]

    caught(dup, "SET")


def test_investigation_is_inconsistent(caught):
    caught(
        lambda fs: get(fs, "flex.flex-001.burn_time").update(investigation_id="other"),
        "INVESTIGATION",
    )
    caught(
        lambda fs: None,
        "INVESTIGATION",
        mutate_investigations=lambda inv: inv[0].update(datasets=["wrong"]),
    )


# ---------------------------------------------------------------------------------------------
# Values, units, conditions
# ---------------------------------------------------------------------------------------------


def test_a_measurement_is_altered_or_its_status_misrepresented(caught):
    caught(lambda fs: get(fs, "flex.flex-001.initial_droplet_diameter").update(value=1.70), "VALUE")
    caught(
        lambda fs: get(fs, "flex.flex-009.burn_time").update(value=0, value_status="reported"),
        "STATUS",
    )
    caught(
        lambda fs: get(fs, "flex.flex-001.burn_time").update(
            value_status="not_reported", value=None
        ),
        "STATUS",
    )


def test_a_unit_or_quantity_is_wrong(caught):
    caught(lambda fs: get(fs, "flex.flex-001.burning_rate_constant").update(unit="mm/s"), "UNIT")
    caught(
        lambda fs: get(fs, "flex.flex-001.burning_rate_constant").update(
            quantity="flame_spread_rate"
        ),
        "QUANTITY",
    )


@pytest.mark.parametrize(
    ("key", "bad"),
    [
        ("pressure_kpa", 101.0),
        ("fuel_or_material", "n-Heptane"),
        ("diluent", "N2 0.21"),
        ("sample_geometry", "free-floating droplet"),
        ("flow_configuration", "quiescent"),
        ("gravity_environment", "normal_gravity"),
        ("oxygen_mole_fraction", 0.2),
    ],
)
def test_a_condition_departs_from_the_printed_row(caught, key, bad):
    caught(
        lambda fs: get(fs, "flex.flex-007.burn_time")["conditions"].update({key: bad}), "CONDITION"
    )


def test_a_condition_key_is_dropped(caught):
    caught(lambda fs: get(fs, "flex.flex-007.burn_time")["conditions"].pop("diluent"), "CONDITION")


def test_nan_in_the_staged_file_is_refused(staged, rows, pages, tmp_path):
    work = tmp_path / "nan"
    shutil.copytree(staged, work)
    path = work / "findings" / "flex.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace('"value": 4.3', '"value": NaN', 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not valid JSON"):
        au.audit(work, ROOT, pages, rows)


# ---------------------------------------------------------------------------------------------
# Real PDF (local only)
# ---------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pdf_pages():
    if not vft.DEFAULT_PDF.is_file():
        pytest.skip("NOT VERIFIED: data/raw/NASA-TP-2015-216046_FLEX.pdf is not present")
    pymupdf = pytest.importorskip("pymupdf", reason="NOT VERIFIED: PyMuPDF is not installed")
    assert hashlib.sha256(vft.DEFAULT_PDF.read_bytes()).hexdigest() == vft.PDF_SHA256
    doc = pymupdf.open(vft.DEFAULT_PDF)
    return lambda printed: doc[printed + vft.PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()


def test_pdf_the_staged_findings_pass_the_audit_against_the_real_source(
    staged, pdf_pages, tmp_path
):
    rows = au.source_rows_from_pdf(pdf_pages)
    assert rows["FLEX-010"]["burning_rate_constant_mm2_per_s"] == ".37", (
        "the PDF prints the excluded value"
    )
    report = run(staged, rows, pdf_pages, tmp=tmp_path)
    assert report["passed"], report["failures"][:3]
    assert report["summary"]["quotes_verified_in_pdf"] == 96


def test_pdf_damage_is_caught_against_the_real_source_too(staged, pdf_pages, tmp_path):
    rows = au.source_rows_from_pdf(pdf_pages)
    report = run(
        staged,
        rows,
        pdf_pages,
        lambda fs: get(fs, "flex.flex-001.burn_time").update(value=4.4),
        tmp=tmp_path,
    )
    assert "VALUE" in codes(report)
    report = run(
        staged,
        rows,
        pdf_pages,
        lambda fs: get(fs, "flex.flex-004.burn_time").update(test_outcome="Disruption"),
        tmp=tmp_path,
    )
    assert "OUTCOME" in codes(report)
