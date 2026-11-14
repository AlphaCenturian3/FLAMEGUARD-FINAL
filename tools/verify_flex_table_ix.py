"""Cross-check the curated FLEX Table IX extract against the original NASA PDF.

Source: NASA/TP-2015-216046 (NTRS 20150023456), Appendix A, Table IX.

The raw PDF is not committed (master spec section 2.4). Download it locally first:

    https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf
    -> data/raw/NASA-TP-2015-216046_FLEX.pdf

Then run, from the repository root, with PyMuPDF available (it is a local
verification tool, not a project dependency):

    python tools/verify_flex_table_ix.py [--pdf PATH]

Checks:
  1. The PDF's SHA-256 matches the file that was transcribed.
  2. Every curated CSV cell equals the PDF text layer for the same Table IX cell
     (after the normalizations documented in data/docs/flex_table_ix.md).
  3. Every quote in the manifest entry appears verbatim on the cited printed page.

Exit code 0 means all checks passed. The PDF text layer was also checked by eye
against a 250-dpi render of the page; this tool does not replace that review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "nasa-tp-2015-216046.table-ix.flex-001-010"
CSV_PATH = ROOT / "data/curated/flex_tp2015216046_table_ix_001_010.csv"
FLAGS_PATH = ROOT / "data/curated/flex_tp2015216046_table_ix_001_010.flags.csv"
FLAGS_ID = "nasa-tp-2015-216046.table-ix.flex-001-010.flags"
DEFAULT_PDF = ROOT / "data/raw/NASA-TP-2015-216046_FLEX.pdf"
FLAG_TYPES = {
    "disputed_value",
    "missing_dash",
    "possibly_extrapolated",
    "imaging_uncertainty",
    "outcome_ambiguous",
    "contamination_caveat",
    "disruption_possibly_contaminant",
    "calibration_test",
}
RANKING_USE = {"exclude", "caution", "not_available"}
PDF_SHA256 = "b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d"
PRINTED_TO_PDF_PAGE_OFFSET = 6  # printed page 20 is PDF page 26 in this report
TABLE_IX_PRINTED_PAGE = 20

# Table IX column order as printed, mapped to curated CSV columns.
TABLE_COLUMNS = [
    "flex_test",
    "flex_identifier",
    "test_date_as_printed",
    "test_time_gmt",
    "fuel",
    "ambient_pressure_mmhg",
    "o2_mole_fraction",
    "n2_mole_fraction",
    "co2_mole_fraction",
    "he_mole_fraction",
    "initial_droplet_diameter_mm",
    "visible_flame_extinction_diameter_mm",
    "burning_rate_constant_mm2_per_s",
    "burn_time_s",
    "test_end",
]
SOURCE_DASH = "–"  # en dash, printed in Table IX for "no value"
_FLEX_ID = re.compile(r"^FLEX[–−-](\d{3})$")
_DASHES = str.maketrans({"–": "-", "—": "-", "−": "-", "‐": "-"})
_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def normalize_cell(token: str) -> str:
    """Map one printed Table IX token to its curated CSV form.

    Only typographic changes: the en-dash "no value" mark becomes an empty cell,
    a bare leading decimal point gets a leading zero (".21" -> "0.21"), and the
    en dash in test IDs becomes an ASCII hyphen. No digits are added or removed.
    """
    if token == SOURCE_DASH:
        return ""
    if m := _FLEX_ID.match(token):
        return f"FLEX-{m.group(1)}"
    if re.fullmatch(r"\.\d+", token):
        return "0" + token
    return token


def parse_table_rows(page_text: str, wanted: set[str]) -> dict[str, list[str]]:
    """Extract Table IX rows (as printed tokens) keyed by normalized FLEX test ID."""
    tokens = page_text.split()
    rows: dict[str, list[str]] = {}
    for i, tok in enumerate(tokens):
        if _FLEX_ID.match(tok):
            test_id = normalize_cell(tok)
            if test_id in wanted:
                rows[test_id] = tokens[i : i + len(TABLE_COLUMNS)]
    return rows


def compare_rows(csv_rows: list[dict[str, str]], pdf_rows: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    for row in csv_rows:
        tid = row["flex_test"]
        printed = pdf_rows.get(tid)
        if printed is None or len(printed) != len(TABLE_COLUMNS):
            errors.append(f"{tid}: row not found intact in PDF text")
            continue
        dashes = []
        for col, tok in zip(TABLE_COLUMNS, printed, strict=True):
            if normalize_cell(tok) != row[col]:
                errors.append(f"{tid}.{col}: csv={row[col]!r} pdf={tok!r}")
            if tok == SOURCE_DASH:
                dashes.append(col)
        if ";".join(dashes) != row["source_dash_fields"]:
            errors.append(f"{tid}: source_dash_fields={row['source_dash_fields']!r}, pdf={dashes}")
    return errors


def normalize_text(text: str) -> str:
    return " ".join(text.translate(_DASHES).translate(_QUOTES).split())


def check_quotes(sources: list[dict], page_text_for) -> list[str]:
    """page_text_for(printed_page:int) -> str. Returns violations."""
    errors = []
    for s in sources:
        quote, page = s.get("quote"), s.get("page")
        if not quote:
            continue
        if normalize_text(quote) not in normalize_text(page_text_for(int(page))):
            errors.append(f"quote not found on printed page {page}: {quote[:60]!r}")
    return errors


def check_flags(flags: list[dict[str, str]], rows: list[dict[str, str]]) -> list[str]:
    """Structural rules for the flags file (no PDF needed)."""
    errors: list[str] = []
    by_id = {r["flex_test"]: r for r in rows}
    dash_cells = {
        (r["flex_test"], f) for r in rows for f in filter(None, r["source_dash_fields"].split(";"))
    }
    flagged_dashes = set()
    for fl in flags:
        fid, tid, field = fl["flag_id"], fl["flex_test"], fl["field"]
        if tid not in by_id:
            errors.append(f"{fid}: unknown test {tid}")
            continue
        if field != "*" and field not in TABLE_COLUMNS:
            errors.append(f"{fid}: unknown field {field}")
        if fl["flag"] not in FLAG_TYPES:
            errors.append(f"{fid}: unknown flag {fl['flag']}")
        if fl["ranking_use"] not in RANKING_USE:
            errors.append(f"{fid}: unknown ranking_use {fl['ranking_use']}")
        if not (fl["source_quote"] and fl["source_printed_page"] and fl["reason"]):
            errors.append(f"{fid}: needs reason, page and quote")
        if fl["flag"] == "missing_dash":
            flagged_dashes.add((tid, field))
            if (tid, field) not in dash_cells:
                errors.append(f"{fid}: missing_dash on a cell that has a printed value")
            if fl["ranking_use"] != "not_available":
                errors.append(f"{fid}: missing_dash must be not_available")
    for cell in sorted(dash_cells - flagged_dashes):
        errors.append(f"{cell[0]}.{cell[1]}: printed dash has no missing_dash flag")
    if not any(
        fl["flex_test"] == "FLEX-010"
        and fl["field"] == "burning_rate_constant_mm2_per_s"
        and fl["flag"] == "disputed_value"
        and fl["ranking_use"] == "exclude"
        for fl in flags
    ):
        errors.append("FLEX-010 burning rate must be flagged disputed_value / exclude")
    return errors


def load_flags(path: Path = FLAGS_PATH) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_csv(path: Path = CSV_PATH) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_manifest_entry(root: Path = ROOT, dataset_id: str = DATASET_ID) -> dict:
    manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
    return next(d for d in manifest["datasets"] if d["id"] == dataset_id)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    args = ap.parse_args(argv)

    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf} (download it first; see module docstring)")
        return 2
    try:
        import pymupdf
    except ImportError:
        print("PyMuPDF is required for this local check: pip install pymupdf")
        return 2

    errors: list[str] = []
    digest = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    if digest != PDF_SHA256:
        errors.append(f"PDF sha256 {digest} != transcribed source {PDF_SHA256}")

    doc = pymupdf.open(args.pdf)

    def page_text(printed: int) -> str:
        return doc[printed + PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()

    csv_rows = load_csv()
    pdf_rows = parse_table_rows(
        page_text(TABLE_IX_PRINTED_PAGE), {r["flex_test"] for r in csv_rows}
    )
    errors += compare_rows(csv_rows, pdf_rows)
    errors += check_quotes(load_manifest_entry().get("sources", []), page_text)
    flags = load_flags()
    errors += check_flags(flags, csv_rows)
    errors += [
        f"flag {e}"
        for e in check_quotes(
            [{"quote": f["source_quote"], "page": f["source_printed_page"]} for f in flags],
            page_text,
        )
    ]

    if errors:
        print("FLEX Table IX verification FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    cells = len(csv_rows) * len(TABLE_COLUMNS)
    print(
        f"FLEX Table IX verification passed: {len(csv_rows)} rows, {cells} cells match the PDF; "
        f"PDF sha256 matches; manifest quotes found verbatim; "
        f"{len(flags)} flags valid with verbatim quotes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
