"""Independent-style audit of the 40 staged FLEX Findings against the NASA PDF.

    python tools/audit_flex_findings.py --staged /tmp/flex-staging --pdf data/raw/NASA-TP-2015-216046_FLEX.pdf --out report.json

This is a CHECK, not an approval. It re-reads the source of truth itself and does not import
the derivation (tools/derive_flex_findings.py):

- the source measurements, test identifiers, fuels, pressures, mole fractions and `Test end`
  outcomes come from the printed Table IX tokens in the PDF text (page 20), not from the curated CSV;
- the applicable quality flags are re-selected from the flags CSV by this file's own rule, and each
  flag's page and quotation must be verbatim in the PDF text;
- every number, status, unit, condition, note, source and provenance field of every staged Finding
  is compared with what the source and the contract require.

It writes a machine-readable acceptance report with one record per Finding. The report is marked
"STAGING AUDIT. NOT AN APPROVAL.": it can find defects, never grant the independent scientific
review (Q3), the F042 note review or any other open gate. Nothing is registered or modified.
Exit code 1 means at least one assertion failed.

Failure codes (each is exercised by an adversarial test): SET, ID, QUANTITY, UNIT, BOUND, STATUS,
VALUE, EXCLUDED_VALUE, LEAK, CONDITION, IDENTITY, OUTCOME, NOTE_SET, NOTE_KIND, NOTE_TEXT,
NOTE_SOURCE, NOTE_QUOTE, SEPARATION, PROVENANCE, INVESTIGATION.
"""

# ruff: noqa: E501  (long assertion messages and parametrised rows read better unwrapped)
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tool(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


vft = _tool("verify_flex_table_ix")  # the existing Table IX row parser and its constants

FINDINGS_ID = "nasa-tp-2015-216046.flex.findings"
FLAGS_ID = "nasa-tp-2015-216046.table-ix.flex-001-010.flags"
TABLE_IX_PAGE = 20
KPA_PER_MMHG = Decimal("133.322387415") / Decimal(1000)  # 1 mmHg = 133.322387415 Pa, by definition
# quantity -> (Table IX column, vocabulary key). Defined here, independently of the derivation.
QUANTITIES = {
    "initial_droplet_diameter": "initial_droplet_diameter_mm",
    "visible_flame_extinction_diameter": "visible_flame_extinction_diameter_mm",
    "burning_rate_constant": "burning_rate_constant_mm2_per_s",
    "burn_time": "burn_time_s",
}
NOTE_USES = {"caution": "caution", "exclude": "exclusion"}  # contract x-flag-ranking-use
_PROSE_NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?!\d|\.\d)")
TEST_IDS = [f"FLEX-{n:03d}" for n in range(1, 11)]


def numbers_in(text: str) -> set[Decimal]:
    out = set()
    for token in _PROSE_NUMBER.findall(text):
        try:
            out.add(Decimal(token))
        except InvalidOperation:
            pass
    return out


def strings_of(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in strings_of(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in strings_of(v)]
    return []


def _strict(path: Path):
    def refuse(constant):
        raise ValueError(f"{path}: {constant} is not valid JSON")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=refuse)


def diluent_expected(tokens: dict[str, str]) -> str | None:
    parts = []
    for symbol, column in (
        ("CO2", "co2_mole_fraction"),
        ("He", "he_mole_fraction"),
        ("N2", "n2_mole_fraction"),
    ):
        norm = vft.normalize_cell(tokens[column])
        if Decimal(norm) != 0:
            parts.append(f"{symbol} {norm}")  # leading-zero typography only, as in the CSV
    return "; ".join(parts) or None


def source_rows_from_pdf(page_text_for) -> dict[str, dict[str, str]]:
    """{test: {column: printed token}} straight from the PDF text of Table IX."""
    rows = vft.parse_table_rows(page_text_for(TABLE_IX_PAGE), set(TEST_IDS))
    out = {}
    for test, tokens in rows.items():
        if len(tokens) != len(vft.TABLE_COLUMNS):
            raise ValueError(f"{test}: Table IX row not found intact in the PDF text")
        out[test] = dict(zip(vft.TABLE_COLUMNS, tokens, strict=True))
    return out


def audit(staged: Path, root: Path, page_text_for, source_rows: dict[str, dict[str, str]]) -> dict:
    failures: list[dict] = []

    def fail(code: str, where: str, message: str, record: dict | None = None) -> None:
        item = {"code": code, "where": where, "message": message}
        failures.append(item)
        if record is not None:
            record["failures"].append(item)

    findings = _strict(staged / "findings" / "flex.json")
    investigations = _strict(staged / "investigations.json")
    manifest = _strict(root / "data" / "manifest.json")
    vocabulary = _strict(root / "contracts" / "vocabulary.json")["quantities"]
    outcomes_doc = _strict(root / "contracts" / "outcomes.json")
    outcomes = outcomes_doc["outcomes"] if outcomes_doc.get("status") == "CONFIRMED" else []
    measured_entry = next(
        d for d in manifest["datasets"] if d["id"] == "nasa-tp-2015-216046.table-ix.flex-001-010"
    )
    registered = measured_entry["sources"]
    numeric_sources = [s for s in registered if str(s["page"]) == str(TABLE_IX_PAGE)]
    with (root / vft.FLAGS_PATH.relative_to(vft.ROOT)).open(encoding="utf-8", newline="") as fh:
        flags = list(csv.DictReader(fh))
    curated_path = root / "tools" / "flex_curated_notes.json"
    curated = _strict(curated_path).get("notes", {}) if curated_path.is_file() else {}
    gates_path = root / "tools" / "flex_derivation_gates.json"
    gates = _strict(gates_path) if gates_path.is_file() else {"gates": []}
    open_gates = [g["id"] for g in gates["gates"] if g["status"] != "closed"]

    expected_ids = [f"flex.{t.lower()}.{q}" for t in TEST_IDS for q in QUANTITIES]
    if not isinstance(findings, list) or not all(isinstance(f, dict) for f in findings):
        fail("SET", "findings", "findings.json must be an array of objects")
        findings = (
            [f for f in findings if isinstance(f, dict)] if isinstance(findings, list) else []
        )
    by_id = {f.get("id"): f for f in findings}
    if sorted(by_id) != sorted(expected_ids) or len(findings) != len(expected_ids):
        fail(
            "SET", "findings", f"expected exactly the 40 ids {expected_ids[0]}..{expected_ids[-1]}"
        )

    excluded_printed: dict[str, str] = {}
    records = []
    for test in TEST_IDS:
        row = source_rows[test]
        for quantity, column in QUANTITIES.items():
            fid = f"flex.{test.lower()}.{quantity}"
            f = by_id.get(fid)
            rec = {"id": fid, "failures": []}
            records.append(rec)
            if f is None:
                fail("SET", fid, "Finding is missing", rec)
                continue
            printed = row[column]
            is_dash = printed == vft.SOURCE_DASH
            applicable = [
                fl
                for fl in flags
                if fl["flex_test"] == test and fl["field"] in (column, "*", "test_end")
            ]
            dash_flagged = any(
                fl["field"] == column and fl["ranking_use"] == "not_available" for fl in applicable
            )
            has_exclude = any(fl["ranking_use"] == "exclude" for fl in applicable)
            expected_status = (
                "not_reported" if is_dash else ("excluded" if has_exclude else "reported")
            )
            if is_dash and not dash_flagged:
                fail("STATUS", fid, "a printed dash has no not_available flag", rec)
            if expected_status == "excluded":
                excluded_printed[fid] = vft.normalize_cell(printed)

            # --- quantity, unit, bound, status, value -------------------------------------
            if f.get("quantity") != quantity:
                fail("QUANTITY", fid, f"quantity {f.get('quantity')!r} != {quantity!r}", rec)
            vocab = vocabulary.get(quantity, {})
            if f.get("unit") != vocab.get("unit"):
                fail(
                    "UNIT", fid, f"unit {f.get('unit')!r} != vocabulary {vocab.get('unit')!r}", rec
                )
            if f.get("value_status") != expected_status:
                fail("STATUS", fid, f"status {f.get('value_status')!r} != {expected_status!r}", rec)
            value = f.get("value")
            if expected_status == "reported":
                try:
                    same = (
                        value is not None
                        and not isinstance(value, bool)
                        and Decimal(str(value)) == Decimal(vft.normalize_cell(printed))
                    )
                except InvalidOperation:
                    same = False
                if not same:
                    fail("VALUE", fid, f"value {value!r} != printed {printed!r}", rec)
                elif value < vocab.get("minimum", 0):
                    fail("BOUND", fid, f"value {value!r} below the vocabulary minimum", rec)
            elif value is not None:
                code = "EXCLUDED_VALUE" if expected_status == "excluded" else "VALUE"
                fail(
                    code,
                    fid,
                    f"a {expected_status} Finding must have a null value, got {value!r}",
                    rec,
                )
            if f.get("id") != fid:
                fail("ID", fid, "id mismatch", rec)

            # --- conditions ---------------------------------------------------------------------
            c = f.get("conditions", {})
            want = {
                "gravity_environment": "microgravity",
                "oxygen_mole_fraction": float(Decimal(vft.normalize_cell(row["o2_mole_fraction"]))),
                "pressure_kpa": float(Decimal(row["ambient_pressure_mmhg"]) * KPA_PER_MMHG),
                "flow_velocity_mm_s": None,
                "flow_configuration": None,
                "diluent": diluent_expected(row),
                "fuel_or_material": row["fuel"].strip(),
                "sample_geometry": None,
            }
            if set(c) != set(want):
                fail("CONDITION", fid, f"condition keys {sorted(c)} != {sorted(want)}", rec)
            for key, expected in want.items():
                if c.get(key) != expected:
                    fail("CONDITION", fid, f"{key}: {c.get(key)!r} != {expected!r}", rec)

            # --- test identity and outcome ----------------------------------------------------
            printed_id = vft.normalize_cell(row["flex_test"])
            printed_outcome = row["test_end"]
            if f.get("test_id") != printed_id or printed_id != test:
                fail(
                    "IDENTITY", fid, f"test_id {f.get('test_id')!r} != printed {printed_id!r}", rec
                )
            if f.get("test_outcome") != printed_outcome or printed_outcome not in outcomes:
                fail(
                    "OUTCOME",
                    fid,
                    f"test_outcome {f.get('test_outcome')!r} != printed {printed_outcome!r}",
                    rec,
                )

            # --- notes ------------------------------------------------------------------------------
            want_notes = {fl["flag_id"]: fl for fl in applicable if fl["ranking_use"] in NOTE_USES}
            notes = f.get("curation_notes", [])
            got = {n.get("flag_ref", {}).get("flag_id"): n for n in notes}
            if sorted(got) != sorted(want_notes) or len(notes) != len(want_notes):
                fail(
                    "NOTE_SET",
                    fid,
                    f"notes {sorted(got)} != applicable flags {sorted(want_notes)}",
                    rec,
                )
            note_records = []
            for flag_id, fl in sorted(want_notes.items()):
                n = got.get(flag_id)
                nrec = {
                    "flag_id": flag_id,
                    "ranking_use": fl["ranking_use"],
                    "kind": NOTE_USES[fl["ranking_use"]],
                    "printed_page": int(fl["source_printed_page"]),
                    "quote": fl["source_quote"],
                    "quote_verified_in_pdf": False,
                    "registered_source_title": None,
                }
                note_records.append(nrec)
                page = int(fl["source_printed_page"])
                try:
                    verbatim = vft.normalize_text(fl["source_quote"]) in vft.normalize_text(
                        page_text_for(page)
                    )
                except Exception as exc:  # noqa: BLE001 - an unreadable page is a failure
                    verbatim = False
                    fail("NOTE_QUOTE", fid, f"{flag_id}: page {page} unreadable: {exc}", rec)
                nrec["quote_verified_in_pdf"] = verbatim
                if not verbatim:
                    fail(
                        "NOTE_QUOTE",
                        fid,
                        f"{flag_id}: quote not verbatim on printed page {page}",
                        rec,
                    )
                if n is None:
                    continue
                if (
                    n.get("kind") != NOTE_USES[fl["ranking_use"]]
                    or n.get("generated_by") != "FlameGuard-SI"
                ):
                    fail("NOTE_KIND", fid, f"{flag_id}: kind/generated_by wrong", rec)
                if n.get("flag_ref", {}).get("manifest_id") != FLAGS_ID:
                    fail("NOTE_KIND", fid, f"{flag_id}: flag_ref manifest_id wrong", rec)
                reason = fl["reason"]
                override = curated.get(flag_id)
                if override is not None:
                    if (
                        hashlib.sha256(reason.encode()).hexdigest()
                        != override["original_reason_sha256"]
                    ):
                        fail(
                            "NOTE_TEXT",
                            fid,
                            f"{flag_id}: curated note is stale against the audited reason",
                            rec,
                        )
                    allowed = override["note"]
                else:
                    allowed = reason
                if n.get("note") != allowed:
                    fail(
                        "NOTE_TEXT",
                        fid,
                        f"{flag_id}: note text is neither the audited reason nor its curated replacement",
                        rec,
                    )
                src = n.get("source", {})
                if (
                    src.get("quote") != fl["source_quote"]
                    or str(src.get("page")) != fl["source_printed_page"]
                ):
                    fail(
                        "NOTE_SOURCE",
                        fid,
                        f"{flag_id}: note source page/quote differ from the flag",
                        rec,
                    )
                match = [
                    r
                    for r in registered
                    if str(r["page"]) == str(src.get("page"))
                    and r.get("quote")
                    and vft.normalize_text(src.get("quote", "")) in vft.normalize_text(r["quote"])
                    and r["title"] == src.get("title")
                ]
                if not match:
                    fail("NOTE_SOURCE", fid, f"{flag_id}: not backed by a registered Source", rec)
                else:
                    nrec["registered_source_title"] = match[0]["title"]
                if str(src.get("page")) == str(TABLE_IX_PAGE) or src in numeric_sources:
                    fail(
                        "SEPARATION",
                        fid,
                        f"{flag_id}: a caution passage is the Table IX numeric source",
                        rec,
                    )

            # --- provenance ---------------------------------------------------------------------------
            prov = f.get("provenance", {})
            if prov.get("manifest_id") != FINDINGS_ID or prov.get("sources") != numeric_sources:
                fail(
                    "PROVENANCE",
                    fid,
                    "manifest_id or numeric sources differ from the registered Table IX Source",
                    rec,
                )
            loc = prov.get("locator", "")
            if not all(
                part in loc
                for part in (test, column, "printed p. 20", f"{row['ambient_pressure_mmhg']} mmHg")
            ):
                fail(
                    "PROVENANCE",
                    fid,
                    "locator does not name test, field, page and printed pressure",
                    rec,
                )

            # --- limitations that remain open for this Finding -----------------------------------------
            limitations = []
            if quantity == "visible_flame_extinction_diameter":
                limitations.append(
                    "A.1 (printed p.19): values may be extrapolated; Table IX does not mark which."
                )
                if is_dash:
                    limitations.append(
                        "A dash has two meanings in A.1 (no extinction, or not listed); it is not a confirmed no-extinction event."
                    )
            if quantity == "burning_rate_constant":
                limitations.append(
                    "An average K from a linear fit (A.1); the source does not define start and end points (Member 5, PR #12)."
                )
            if quantity == "burn_time":
                limitations.append(
                    "Source defines neither 'Burn time' nor 'Test end' (Member 5, PR #12 review)."
                )
            if test == "FLEX-001":
                limitations.append(
                    "Printed Disruption with a reported extinction diameter (F005); the outcome is not inferred from the value."
                )
            limitations.append(
                "All coated-needle contamination cautions of this report apply (flag family contamination_caveat)."
            )
            if expected_status == "excluded":
                limitations.append(
                    "Excluded by FlameGuard-SI pending reconciliation with PSI data; the printed number is withheld."
                )
            if expected_status == "not_reported":
                limitations.append("The source prints a dash: no value exists to compare.")
            limitations.append(
                "Conditions diluent, fuel_or_material, sample_geometry and pressure serialization are provisional project-owner decisions (G7), not independent scientific verification."
            )
            limitations.append(f"Open gates for registration: {', '.join(open_gates) or 'none'}.")

            rec.update(
                {
                    "test_id": f.get("test_id"),
                    "test_outcome": f.get("test_outcome"),
                    "quantity": f.get("quantity"),
                    "unit": f.get("unit"),
                    "source_measurement": {
                        "printed_token": printed,
                        "pdf_printed_page": TABLE_IX_PAGE,
                        "column": column,
                        "is_dash": is_dash,
                    },
                    "value_status": f.get("value_status"),
                    "expected_value_status": expected_status,
                    "value": f.get("value") if expected_status != "excluded" else None,
                    "conditions_match_source": not any(
                        x["code"] == "CONDITION" for x in rec["failures"]
                    ),
                    "applicable_cautions_and_exclusions": note_records,
                    "not_available_flags": sorted(
                        fl["flag_id"] for fl in applicable if fl["ranking_use"] == "not_available"
                    ),
                    "limitations_unresolved": limitations,
                }
            )

    # --- cross-Finding leakage of an excluded printed value ----------------------------------------
    for fid, printed in excluded_printed.items():
        target = Decimal(printed)
        for f in findings:
            texts = strings_of({k: v for k, v in f.items() if k != "value"})
            if any(target in numbers_in(t) for t in texts):
                fail("LEAK", f.get("id", "?"), f"states the excluded printed value of {fid}")

    # --- investigation ---------------------------------------------------------------------------------
    inv_ok = (
        len(investigations) == 1
        and investigations[0].get("id") == "flex"
        and investigations[0].get("datasets") == [FINDINGS_ID]
        and investigations[0].get("sources") == numeric_sources
        and {f.get("investigation_id") for f in findings} == {"flex"}
    )
    if not inv_ok:
        fail(
            "INVESTIGATION",
            "investigations.json",
            "id, datasets, sources or investigation_id mismatch",
        )

    by_status: dict[str, int] = {}
    for f in findings:
        by_status[f.get("value_status", "?")] = by_status.get(f.get("value_status", "?"), 0) + 1
    return {
        "report_version": "1",
        "status": "STAGING AUDIT. NOT AN APPROVAL. NOT EVIDENCE.",
        "passed": not failures,
        "handling": "INTERNAL AUDIT ONLY. source_measurement.printed_token is the number printed in the source, including for excluded measurements, so the auditor can check the exclusion. Never serve, display or quote this report downstream (S9).",
        "summary": {
            "findings": len(findings),
            "by_value_status": by_status,
            "failures": len(failures),
            "notes_checked": sum(
                len(r.get("applicable_cautions_and_exclusions", [])) for r in records
            ),
            "quotes_verified_in_pdf": sum(
                n["quote_verified_in_pdf"]
                for r in records
                for n in r.get("applicable_cautions_and_exclusions", [])
            ),
            "open_gates": open_gates,
        },
        "failures": failures,
        "findings": records,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--staged", type=Path, required=True)
    ap.add_argument("--pdf", type=Path, default=vft.DEFAULT_PDF)
    ap.add_argument("--out", type=Path, help="write the JSON acceptance report here")
    args = ap.parse_args(argv)
    try:
        import pymupdf
    except ImportError:
        print("PyMuPDF is required (install it in a scratch venv). NOT AUDITED.")
        return 2
    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf}. NOT AUDITED.")
        return 2
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != vft.PDF_SHA256:
        print("PDF sha256 differs from the transcribed source. NOT AUDITED.")
        return 2
    doc = pymupdf.open(args.pdf)

    def page_text(printed: int) -> str:
        return doc[printed + vft.PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()

    report = audit(args.staged, ROOT, page_text, source_rows_from_pdf(page_text))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8", newline="\n")
    s = report["summary"]
    print(
        f"{report['status']}  findings={s['findings']} {s['by_value_status']}  notes={s['notes_checked']} "
        f"quotes_verified={s['quotes_verified_in_pdf']}  failures={s['failures']}"
    )
    for item in report["failures"]:
        print(f"  FAIL {item['code']} {item['where']}: {item['message']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
