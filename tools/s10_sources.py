"""S10 source-passage validation for FLEX quality flags (contract rule S10, parts a-d).

Every flag whose `ranking_use` produces a curation note (`caution` -> caution note, `exclude` ->
exclusion note; the mapping is read from contracts/schemas/common.schema.json) needs a
**source passage**: the printed page and the verbatim quote that the flag row records. This
module answers, for all of them and not just a subset of pages:

  1. Is each passage well formed? (page is a positive integer, quote is non-empty)
  2. Is it registered, i.e. does the measured manifest entry carry a Source on that page whose
     quote contains the flag's quote? (`registered_quote`, else `page_only` or `unregistered_page`)
  3. Is the quote verbatim on that printed page of the source document? (needs the PDF)
  4. On a figure-caption page, does the caption name the test the flag is about?
  5. What exact Source entries would close the registration gap? (`propose_sources`; a proposal
     only, never written anywhere)

Fail closed, never invent:
- an unknown `ranking_use`, a blank page or quote, or a Source with an unreadable page raises
  `S10Error`; nothing is skipped silently;
- a page that cannot be read, or a quote not found on it, is an error, not a pass;
- a Source title is proposed only when the page's own figure caption supplies it; otherwise the
  passage is reported as `unproposable` and a person must supply the title;
- `not_available` flags produce no note (S10c) and are not passages.

Separation of provenance (design rule for the derivation tool): **numeric provenance** is the
Source of the Table IX table itself (`TABLE_IX_PAGE`); a **caution passage** supports a
FlameGuard-SI note and is never the numeric source of a value. `split_sources` and
`check_separation` enforce that the two roles never share a Source.

Usage: python tools/s10_sources.py [--pdf PATH] [--propose]   (PyMuPDF is needed for --pdf)
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS_PATH = (
    ROOT / "data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv"
)
MANIFEST_PATH = ROOT / "data/manifest.json"
COMMON_SCHEMA = ROOT / "contracts/schemas/common.schema.json"
MEASURED_ID = "nasa-tp-2015-216046.table-ix.flex-001-010"
DEFAULT_PDF = ROOT / "data/raw/NASA-TP-2015-216046_FLEX.pdf"
REPORT_URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf"
ARCHIVE_ID = "NTRS 20150023456"
REPORT_TITLE = "NASA/TP-2015-216046"
TABLE_IX_PAGE = 20  # printed page of Table IX: the numeric provenance of every measured value
PRINTED_TO_PDF_PAGE_OFFSET = 6

_spec = importlib.util.spec_from_file_location("_vft", ROOT / "tools" / "verify_flex_table_ix.py")
_vft = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vft)
normalize_text = _vft.normalize_text  # one definition of "verbatim up to dashes and quote marks"

_CAPTION = re.compile(r"Figure\s+(\d+)\s*\.\s*[—–−-]\s*Test\s+(FLEX[–−-]\d{3})")


class S10Error(ValueError):
    """The flags or manifest cannot be validated; never swallowed, never treated as a pass."""


@dataclass(frozen=True)
class Passage:
    """One distinct (printed page, quote) that supports at least one caution or exclusion note."""

    page: int
    quote: str  # as recorded in the flags file, verbatim
    flag_ids: tuple[str, ...] = field(default=())
    tests: tuple[str, ...] = field(default=())

    @property
    def key(self) -> tuple[int, str]:
        return self.page, normalize_text(self.quote)


def note_kinds(schema_path: Path = COMMON_SCHEMA) -> dict[str, str]:
    """ranking_use -> curation note kind, from the contract's `x-flag-ranking-use`."""
    found: list[dict[str, str]] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "x-flag-ranking-use" in node:
                found.append(node["x-flag-ranking-use"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(json.loads(schema_path.read_text(encoding="utf-8")))
    if len(found) != 1:
        raise S10Error(
            f"expected exactly one x-flag-ranking-use in {schema_path}, found {len(found)}"
        )
    kind_to_use = found[0]  # {"caution": "caution", "exclusion": "exclude"}
    return {use: kind for kind, use in kind_to_use.items()}


def load_flags(path: Path = FLAGS_PATH) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_measured_sources(manifest_path: Path = MANIFEST_PATH) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("datasets", []):
        if entry.get("id") == MEASURED_ID:
            return list(entry.get("sources", []))
    raise S10Error(f"manifest has no entry {MEASURED_ID!r}")


def _page(raw: object, where: str) -> int:
    text = str(raw).strip()
    if not re.fullmatch(r"[1-9]\d*", text):
        raise S10Error(f"{where}: page must be a positive integer, got {raw!r}")
    return int(text)


def note_flags(flags: list[dict[str, str]], kinds: dict[str, str] | None = None) -> list[dict]:
    """The flags that become curation notes. Anything unrecognised is an error, never skipped."""
    kinds = note_kinds() if kinds is None else kinds
    out = []
    for fl in flags:
        fid = fl.get("flag_id") or "<no flag_id>"
        use = fl.get("ranking_use")
        if use == "not_available":
            continue  # S10(c): produces no note, so no passage
        if use not in kinds:
            raise S10Error(f"{fid}: unknown ranking_use {use!r}")
        _page(fl.get("source_printed_page"), fid)
        if not (fl.get("source_quote") or "").strip():
            raise S10Error(f"{fid}: a {use} flag needs a verbatim source quote")
        out.append(fl)
    return out


def passages(flags: list[dict[str, str]], kinds: dict[str, str] | None = None) -> list[Passage]:
    """Distinct (page, quote) pairs behind all caution and exclusion flags, in page order."""
    groups: dict[tuple[int, str], dict] = {}
    for fl in note_flags(flags, kinds):
        page = _page(fl["source_printed_page"], fl["flag_id"])
        key = (page, normalize_text(fl["source_quote"]))
        g = groups.setdefault(key, {"quote": fl["source_quote"], "flags": [], "tests": set()})
        g["flags"].append(fl["flag_id"])
        g["tests"].add(fl["flex_test"])
    return [
        Passage(page, g["quote"], tuple(sorted(g["flags"])), tuple(sorted(g["tests"])))
        for (page, _), g in sorted(groups.items())
    ]


# --- registration coverage -------------------------------------------------------------------


def coverage(found: list[Passage], sources: list[dict]) -> dict[tuple[int, str], str]:
    """passage key -> registered_quote | page_only | unregistered_page.

    registered_quote: a Source on the same page whose quote contains the flag's quote.
    page_only: a Source exists on that page but does not carry this quote.
    """
    registered: list[tuple[int, str]] = []
    for i, s in enumerate(sources):
        page = _page(s.get("page"), f"sources[{i}]")
        registered.append((page, normalize_text(s["quote"]) if s.get("quote") else ""))
    out = {}
    for p in found:
        same_page = [q for page, q in registered if page == p.page]
        nq = normalize_text(p.quote)
        if any(nq in q for q in same_page if q):
            out[p.key] = "registered_quote"
        elif same_page:
            out[p.key] = "page_only"
        else:
            out[p.key] = "unregistered_page"
    return out


# --- verification against the source document ------------------------------------------------


def verify_passages(found: list[Passage], page_text_for) -> list[str]:
    """`page_text_for(printed_page) -> str`. Every passage must be verbatim on its printed page."""
    errors = []
    for p in found:
        try:
            text = page_text_for(p.page)
        except Exception as exc:  # noqa: BLE001 - an unreadable page is unverifiable, not a pass
            errors.append(f"p. {p.page} ({', '.join(p.flag_ids)}): page unreadable: {exc}")
            continue
        if normalize_text(p.quote) not in normalize_text(text):
            errors.append(
                f"p. {p.page} ({', '.join(p.flag_ids)}): quote not found on the page: "
                f"{p.quote[:60]!r}"
            )
    return errors


def caption_of(page_text: str) -> tuple[str, str] | None:
    """(figure label, test id) if the page carries exactly one 'Figure N.-Test FLEX-NNN' caption."""
    found = {(f"Figure {n}", re.sub(r"[–−]", "-", t)) for n, t in _CAPTION.findall(page_text)}
    return found.pop() if len(found) == 1 else None


def check_caption_attribution(found: list[Passage], page_text_for) -> list[str]:
    """On a page with a figure caption, every flag citing it must be about that caption's test.

    A page with several, or ambiguous, captions is unverifiable and is reported, not trusted.
    Section pages without any caption are report-wide and are not attributed to a test.
    """
    errors = []
    for p in found:
        try:
            text = page_text_for(p.page)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"p. {p.page}: page unreadable: {exc}")
            continue
        raw = _CAPTION.findall(text)
        if not raw:
            continue
        caption = caption_of(text)
        if caption is None:
            errors.append(f"p. {p.page}: more than one distinct figure caption; cannot attribute")
        elif any(t != caption[1] for t in p.tests):
            errors.append(
                f"p. {p.page} ({', '.join(p.flag_ids)}): caption names {caption[1]} but the "
                f"flags are about {', '.join(p.tests)}"
            )
    return errors


# --- separation of numeric provenance and caution passages ------------------------------------


def split_sources(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    """(numeric provenance sources, caution/definition passage sources)."""
    numeric = [s for s in sources if _page(s.get("page"), "source") == TABLE_IX_PAGE]
    return numeric, [s for s in sources if s not in numeric]


def check_separation(found: list[Passage], sources: list[dict]) -> list[str]:
    errors = []
    numeric, _ = split_sources(sources)
    if not numeric:
        errors.append(f"no registered numeric source on Table IX page {TABLE_IX_PAGE}")
    for p in found:
        if p.page == TABLE_IX_PAGE:
            errors.append(
                f"{', '.join(p.flag_ids)}: a caution/exclusion passage must not be the Table IX "
                f"numeric source (p. {TABLE_IX_PAGE})"
            )
    return errors


# --- proposal (never registered) ---------------------------------------------------------------


def propose_sources(
    found: list[Passage], status: dict[tuple[int, str], str], page_text_for, retrieved: str
) -> tuple[list[dict], list[str]]:
    """Source entries that would give every unregistered passage its own registered Source.

    Returns (proposals, unproposable). A title comes only from the page's own figure caption.
    The quote is the flag's, verbatim. Nothing is written anywhere.
    """
    proposals, unproposable = [], []
    for p in found:
        if status[p.key] == "registered_quote":
            continue
        caption = caption_of(page_text_for(p.page))
        if caption is None:
            unproposable.append(
                f"p. {p.page} ({', '.join(p.flag_ids)}): no single figure caption on the page; "
                "a person must supply the Source title"
            )
            continue
        figure, test = caption
        proposals.append(
            {
                "title": f"{REPORT_TITLE}, Appendix B, {figure} caption (Test {test})",
                "url": REPORT_URL,
                "page": str(p.page),
                "quote": p.quote,
                "retrieved": retrieved,
                "archive_id": ARCHIVE_ID,
            }
        )
    return proposals, unproposable


# --- command line -----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    ap.add_argument("--propose", action="store_true", help="print the proposed Source entries")
    args = ap.parse_args(argv)

    flags, sources = load_flags(), load_measured_sources()
    found = passages(flags)
    status = coverage(found, sources)
    errors = check_separation(found, sources)
    counts: dict[str, int] = {}
    for st in status.values():
        counts[st] = counts.get(st, 0) + 1
    print(f"{len(note_flags(flags))} caution/exclusion flags -> {len(found)} passages; {counts}")
    for p in found:
        print(f"  {status[p.key]:<18} p.{p.page:<3} {','.join(p.flag_ids)}  {p.quote[:56]!r}")

    page_text = None
    if args.pdf.is_file():
        try:
            import pymupdf
        except ImportError:
            print("PyMuPDF missing: install it in a scratch venv. NOT VERIFIED against the PDF.")
        else:
            digest = __import__("hashlib").sha256(args.pdf.read_bytes()).hexdigest()
            if digest != _vft.PDF_SHA256:
                errors.append(f"PDF sha256 {digest} != transcribed source {_vft.PDF_SHA256}")
            doc = pymupdf.open(args.pdf)

            def page_text(printed: int) -> str:
                return doc[printed + PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()

            errors += verify_passages(found, page_text)
            errors += check_caption_attribution(found, page_text)
    else:
        print(
            f"PDF not found at {args.pdf}: structure checked, quotes NOT VERIFIED against the PDF."
        )

    if args.propose:
        if page_text is None:
            errors.append("--propose needs the PDF (titles come from its figure captions)")
        else:
            retrieved = _numeric_retrieved(sources)
            proposals, unproposable = propose_sources(found, status, page_text, retrieved)
            print(json.dumps(proposals, indent=2, ensure_ascii=False))
            errors += unproposable
    if errors:
        print("S10 source validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        "S10 source validation passed" + ("" if page_text else " (structure only; PDF not checked)")
    )
    return 0


def _numeric_retrieved(sources: list[dict]) -> str:
    numeric, _ = split_sources(sources)
    return numeric[0]["retrieved"]


if __name__ == "__main__":
    sys.exit(main())
