"""S10 source-passage validation for FLEX flags (tools/s10_sources.py).

Real-data tests run in CI without the PDF and pin the coverage as it stands on this branch.
The PDF tests run only where the report is available locally (data/raw/, not committed) and
SKIP with a "NOT VERIFIED" reason otherwise. Synthetic tests use clearly invented pages and
quotes and never touch the real data files.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("s10_sources", ROOT / "tools" / "s10_sources.py")
s10 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = s10  # dataclasses look the module up by name
_spec.loader.exec_module(s10)

SRC = "SYNTHETIC quote one."


def flag(fid="S1", test="FLEX-001", use="caution", page="40", quote=SRC, **extra):
    return {
        "flag_id": fid,
        "flex_test": test,
        "field": "*",
        "flag": "synthetic",
        "ranking_use": use,
        "reason": "SYNTHETIC reason",
        "source_printed_page": page,
        "source_quote": quote,
        **extra,
    }


def source(page="40", quote=SRC, retrieved="2026-01-01"):
    return {"title": "SYNTHETIC", "page": page, "quote": quote, "retrieved": retrieved}


def pages(mapping):
    def page_text_for(n):
        if n not in mapping:
            raise IndexError(f"no page {n}")
        return mapping[n]

    return page_text_for


# ---------------------------------------------------------------------------------------------
# The real data: every caution and exclusion flag, not a subset
# ---------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def flags():
    return s10.load_flags()


@pytest.fixture(scope="module")
def sources():
    return s10.load_measured_sources()


@pytest.fixture(scope="module")
def found(flags):
    return s10.passages(flags)


def test_the_flag_to_note_mapping_comes_from_the_contract():
    assert s10.note_kinds() == {"caution": "caution", "exclude": "exclusion"}


def test_all_caution_and_exclusion_flags_are_covered_and_not_available_ones_are_not(flags, found):
    needing = [f["flag_id"] for f in flags if f["ranking_use"] in ("caution", "exclude")]
    assert len(needing) == 36  # 35 caution + 1 exclude (F042)
    covered = sorted(fid for p in found for fid in p.flag_ids)
    assert covered == sorted(needing), "every flag that becomes a note has a passage, once"
    not_available = [f for f in flags if f["ranking_use"] == "not_available"]
    assert len(not_available) == 9
    assert {f["flag"] for f in not_available} == {"missing_dash"}
    assert not {f["flag_id"] for f in not_available} & set(covered), "S10(c): no note, no passage"


def test_distinct_passages_are_distinct_pages_and_quotes(found):
    assert len(found) == 17
    assert len({p.key for p in found}) == 17
    by_page = {}
    for p in found:
        by_page.setdefault(p.page, []).append(p)
    # different quotes on one page stay separate sources; the same quote on a page is one
    assert {pg: len(ps) for pg, ps in by_page.items() if len(ps) > 1} == {
        16: 2,
        17: 2,
        29: 2,
        34: 2,
        38: 3,
    }
    shared = next(p for p in found if p.page == 36)
    assert shared.flag_ids == ("F029", "F031"), "one quote on one page serves both flags"


def test_registration_coverage_as_it_stands_on_main(found, sources):
    """Pinned to the current manifest. When the registration decision (PR #13, Option A) lands
    this test must change with it; that is the point: the gap is measured, not assumed."""
    status = s10.coverage(found, sources)
    counts = {}
    for st in status.values():
        counts[st] = counts.get(st, 0) + 1
    assert counts == {"registered_quote": 3, "page_only": 5, "unregistered_page": 9}
    registered_pages = {int(s["page"]) for s in sources}
    for p in found:  # independent oracle: unregistered exactly when no Source is on its page
        assert (status[p.key] == "unregistered_page") == (p.page not in registered_pages)
    unregistered = sorted({p.page for p in found if status[p.key] == "unregistered_page"})
    assert unregistered == [29, 30, 31, 33, 34, 35, 36]


def test_caution_passages_are_separate_from_numeric_provenance(found, sources):
    assert s10.check_separation(found, sources) == []
    numeric, passage_sources = s10.split_sources(sources)
    assert [s["page"] for s in numeric] == ["20"]
    assert "TABLE IX" in numeric[0]["quote"]
    assert len(passage_sources) == len(sources) - 1
    assert all(p.page != s10.TABLE_IX_PAGE for p in found)
    assert not [s for s in numeric if s in passage_sources], "no Source plays both roles"


# ---------------------------------------------------------------------------------------------
# Fail closed: malformed flags and sources are errors, never skipped
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("bad", "fragment"),
    [
        (flag(use="maybe"), "unknown ranking_use"),
        (flag(use=""), "unknown ranking_use"),
        (flag(quote=""), "needs a verbatim source quote"),
        (flag(quote="   "), "needs a verbatim source quote"),
        (flag(page=""), "positive integer"),
        (flag(page="0"), "positive integer"),
        (flag(page="-3"), "positive integer"),
        (flag(page="12a"), "positive integer"),
        (flag(page="1.5"), "positive integer"),
        (flag(page="p. 29"), "positive integer"),
    ],
    ids=[
        "unknown-use",
        "empty-use",
        "blank-quote",
        "spaces-quote",
        "blank-page",
        "zero-page",
        "negative-page",
        "letters-page",
        "decimal-page",
        "prefixed-page",
    ],
)
def test_malformed_flags_raise(bad, fragment):
    with pytest.raises(s10.S10Error, match=fragment):
        s10.passages([bad])


def test_a_missing_field_is_an_error_not_a_skip():
    broken = flag()
    del broken["source_quote"]
    with pytest.raises(s10.S10Error):
        s10.passages([broken])
    nameless = flag()
    del nameless["ranking_use"]
    with pytest.raises(s10.S10Error, match="unknown ranking_use"):
        s10.passages([nameless])


def test_not_available_needs_no_passage_even_when_its_quote_is_blank():
    assert s10.passages([flag(use="not_available", quote="", page="")]) == []


def test_exclude_flags_are_passages_too():
    (p,) = s10.passages([flag(use="exclude")])
    assert p.page == 40 and p.flag_ids == ("S1",)


def test_a_source_with_an_unreadable_page_is_an_error():
    found = s10.passages([flag()])
    for bad in ("", "x", None, "0"):
        with pytest.raises(s10.S10Error, match="positive integer"):
            s10.coverage(found, [source(page=bad)])


def test_missing_measured_entry_is_an_error(tmp_path):
    manifest = tmp_path / "m.json"
    manifest.write_text('{"datasets": [{"id": "other", "sources": []}]}', encoding="utf-8")
    with pytest.raises(s10.S10Error, match="no entry"):
        s10.load_measured_sources(manifest)


def test_the_contract_mapping_must_be_unambiguous(tmp_path):
    schema = tmp_path / "common.json"
    schema.write_text(
        '{"a": {"x-flag-ranking-use": {"caution": "caution"}}, "b": {}}', encoding="utf-8"
    )
    assert s10.note_kinds(schema) == {"caution": "caution"}
    schema.write_text("{}", encoding="utf-8")
    with pytest.raises(s10.S10Error, match="exactly one"):
        s10.note_kinds(schema)


# ---------------------------------------------------------------------------------------------
# Registration coverage on synthetic data
# ---------------------------------------------------------------------------------------------


def test_coverage_classes():
    found = s10.passages(
        [
            flag("A", page="40", quote="exact quote here"),
            flag("B", page="41", quote="other words"),
            flag("C", page="42", quote="nothing registered"),
            flag("D", page="43", quote="source has no quote"),
        ]
    )
    srcs = [
        source("40", "context before exact quote here and after"),  # contains it
        source("41", "different words entirely"),  # same page, different quote
        source("43", None),  # page registered, no quote recorded
    ]
    status = s10.coverage(found, srcs)
    by_flag = {p.flag_ids[0]: status[p.key] for p in found}
    assert by_flag == {
        "A": "registered_quote",
        "B": "page_only",
        "C": "unregistered_page",
        "D": "page_only",
    }


def test_a_quote_on_the_wrong_page_is_not_registered():
    found = s10.passages([flag(page="40", quote="exact words")])
    assert s10.coverage(found, [source("41", "exact words")])[found[0].key] == "unregistered_page"


def test_coverage_tolerates_only_typographic_differences():
    found = s10.passages([flag(page="40", quote="a – b “q”")])
    assert s10.coverage(found, [source("40", 'a - b "q"')])[found[0].key] == "registered_quote"
    off = s10.passages([flag(page="40", quote="a - c")])
    assert s10.coverage(off, [source("40", "a - b")])[off[0].key] == "page_only"


# ---------------------------------------------------------------------------------------------
# Verification against document text (synthetic pages)
# ---------------------------------------------------------------------------------------------


def test_verbatim_quote_on_its_page_passes_and_an_altered_one_fails():
    found = s10.passages([flag(page="40", quote="The droplet stayed in view.")])
    assert s10.verify_passages(found, pages({40: "x The droplet   stayed in\nview. y"})) == []
    errors = s10.verify_passages(found, pages({40: "x The droplet stayed out of view. y"}))
    assert errors and "not found on the page" in errors[0]


def test_a_quote_found_only_on_another_page_fails():
    found = s10.passages([flag(page="40", quote="only here")])
    assert s10.verify_passages(found, pages({40: "nothing", 41: "only here"}))


def test_an_unreadable_page_is_unverifiable_not_a_pass():
    found = s10.passages([flag(page="99")])
    errors = s10.verify_passages(found, pages({40: SRC}))
    assert errors and "page unreadable" in errors[0]
    assert "page unreadable" in s10.check_caption_attribution(found, pages({}))[0]


def test_an_empty_page_text_never_verifies_a_quote():
    assert s10.verify_passages(s10.passages([flag()]), pages({40: ""}))


CAPTION = "Figure {n}.—Test FLEX–{t}"


def test_caption_names_the_flags_test():
    found = s10.passages([flag(test="FLEX-004", page="40")])
    ok = pages({40: CAPTION.format(n=8, t="004") + " body"})
    assert s10.check_caption_attribution(found, ok) == []
    bad = pages({40: CAPTION.format(n=8, t="005") + " body"})
    errors = s10.check_caption_attribution(found, bad)
    assert errors and "caption names FLEX-005" in errors[0]


def test_caption_matches_with_minus_or_hyphen_in_the_test_id():
    found = s10.passages([flag(test="FLEX-007", page="40")])
    for dash in ("–", "−", "-"):
        text = f"Figure 11.—Test FLEX{dash}007"
        assert s10.check_caption_attribution(found, pages({40: text})) == []


def test_two_different_captions_on_one_page_cannot_be_attributed():
    found = s10.passages([flag(test="FLEX-004", page="40")])
    text = CAPTION.format(n=8, t="004") + " ... " + CAPTION.format(n=9, t="005")
    errors = s10.check_caption_attribution(found, pages({40: text}))
    assert errors and "more than one distinct figure caption" in errors[0]


def test_a_report_wide_section_page_is_not_attributed_to_a_test():
    found = s10.passages([flag(test="FLEX-004", page="40")])
    assert s10.check_caption_attribution(found, pages({40: "Section text, no caption."})) == []


def test_every_test_citing_a_shared_page_must_match_its_caption():
    found = s10.passages(
        [flag("A", test="FLEX-004", page="40"), flag("B", test="FLEX-005", page="40")]
    )
    errors = s10.check_caption_attribution(
        found, pages({40: CAPTION.format(n=8, t="004") + " " + SRC})
    )
    assert len(errors) == 1
    assert "caption names FLEX-004" in errors[0] and "FLEX-005" in errors[0]


# ---------------------------------------------------------------------------------------------
# Separation of numeric provenance and caution passages
# ---------------------------------------------------------------------------------------------


def test_a_caution_on_the_table_page_is_rejected_as_a_caution_source():
    found = s10.passages([flag(page=str(s10.TABLE_IX_PAGE))])
    errors = s10.check_separation(found, [source(str(s10.TABLE_IX_PAGE), "TABLE IX")])
    assert errors and "must not be the Table IX numeric source" in errors[0]


def test_missing_numeric_source_is_reported():
    errors = s10.check_separation(s10.passages([flag()]), [source("40")])
    assert errors and "no registered numeric source" in errors[0]


# ---------------------------------------------------------------------------------------------
# Proposals: never invented
# ---------------------------------------------------------------------------------------------


def _propose(flags_, srcs, text, retrieved="2026-01-02"):
    found = s10.passages(flags_)
    return s10.propose_sources(found, s10.coverage(found, srcs), pages(text), retrieved)


def test_a_proposal_is_built_only_from_the_page_caption_and_the_flag_quote():
    props, unprop = _propose(
        [flag(test="FLEX-004", page="40", quote="verbatim words")],
        [],
        {40: CAPTION.format(n=8, t="004") + " verbatim words"},
    )
    assert unprop == []
    assert props == [
        {
            "title": "NASA/TP-2015-216046, Appendix B, Figure 8 caption (Test FLEX-004)",
            "url": s10.REPORT_URL,
            "page": "40",
            "quote": "verbatim words",
            "retrieved": "2026-01-02",
            "archive_id": s10.ARCHIVE_ID,
        }
    ]


def test_without_a_caption_nothing_is_proposed_and_a_person_is_asked():
    props, unprop = _propose([flag(page="40")], [], {40: "plain section text"})
    assert props == []
    assert unprop and "a person must supply the Source title" in unprop[0]


def test_registered_quotes_are_not_proposed_again():
    props, unprop = _propose([flag(page="40")], [source("40", SRC)], {40: "x"})
    assert (props, unprop) == ([], [])


def test_distinct_quotes_on_one_page_get_distinct_sources_and_one_quote_gets_one():
    text = {40: CAPTION.format(n=8, t="004")}
    two, _ = _propose(
        [flag("A", page="40", quote="first"), flag("B", page="40", quote="second")], [], text
    )
    assert [p["quote"] for p in two] == ["first", "second"]
    one, _ = _propose(
        [flag("A", page="40", quote="same"), flag("B", page="40", quote=" same ")], [], text
    )
    assert [p["quote"] for p in one] == ["same"]


def test_proposing_changes_no_registered_source():
    srcs = [source("20", "TABLE IX"), source("40", "other")]
    before = copy.deepcopy(srcs)
    _propose([flag(page="40", quote="new")], srcs, {40: CAPTION.format(n=8, t="004")})
    assert srcs == before


# ---------------------------------------------------------------------------------------------
# Real PDF (local only)
# ---------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def page_text():
    if not s10.DEFAULT_PDF.is_file():
        pytest.skip("NOT VERIFIED: data/raw/NASA-TP-2015-216046_FLEX.pdf is not present")
    pymupdf = pytest.importorskip("pymupdf", reason="NOT VERIFIED: PyMuPDF is not installed")
    digest = hashlib.sha256(s10.DEFAULT_PDF.read_bytes()).hexdigest()
    assert digest == s10._vft.PDF_SHA256, "the local PDF is not the transcribed source"
    doc = pymupdf.open(s10.DEFAULT_PDF)
    return lambda printed: doc[printed + s10.PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()


def test_pdf_every_passage_is_verbatim_on_its_page(found, page_text):
    assert s10.verify_passages(found, page_text) == []


def test_pdf_every_caption_names_the_flags_test(found, page_text):
    assert s10.check_caption_attribution(found, page_text) == []
    captioned = [p for p in found if s10.caption_of(page_text(p.page))]
    assert sorted({p.page for p in captioned}) == [29, 30, 31, 32, 33, 34, 35, 36, 38]


def test_pdf_the_proposal_covers_all_but_two_section_passages(found, sources, page_text):
    status = s10.coverage(found, sources)
    props, unprop = s10.propose_sources(found, status, page_text, "2026-11-14")
    assert len(props) == 12 and len(unprop) == 2
    assert {(p["page"], p["quote"]) for p in props} == {
        (str(p.page), p.quote) for p in found if status[p.key] != "registered_quote" and p.page > 17
    }
    assert sorted(u.split(" (")[0] for u in unprop) == ["p. 16", "p. 17"]
    for pr in props:  # nothing invented: the title's figure and test come from the page itself
        figure, test = s10.caption_of(page_text(int(pr["page"])))
        assert f"{figure} caption (Test {test})" in pr["title"]


def test_the_proposed_quote_is_the_flags_quote_byte_for_byte():
    """Normalisation is only for comparing; the recorded quote must never be rewritten."""
    verbatim = "a – b  “quoted”  end"
    props, _ = _propose(
        [flag(test="FLEX-004", page="40", quote=verbatim)],
        [],
        {40: CAPTION.format(n=8, t="004")},
    )
    assert props[0]["quote"] == verbatim
