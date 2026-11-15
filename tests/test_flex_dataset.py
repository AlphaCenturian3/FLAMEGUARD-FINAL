"""Data-integrity checks for the curated FLEX Table IX extract (owner: feat/nasa-data-tars).

These run in CI without the raw PDF. The cell-by-cell comparison with the PDF is
tools/verify_flex_table_ix.py, run locally; its parsing logic is tested here.
"""

import csv
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "verify_flex_table_ix", ROOT / "tools" / "verify_flex_table_ix.py"
)
vft = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vft)

NUMERIC = [
    "ambient_pressure_mmhg",
    "o2_mole_fraction",
    "n2_mole_fraction",
    "co2_mole_fraction",
    "he_mole_fraction",
    "initial_droplet_diameter_mm",
    "visible_flame_extinction_diameter_mm",
    "burning_rate_constant_mm2_per_s",
    "burn_time_s",
]


@pytest.fixture(scope="module")
def rows():
    return vft.load_csv()


@pytest.fixture(scope="module")
def entry():
    return vft.load_manifest_entry()


def test_header_and_row_count(rows):
    with vft.CSV_PATH.open(encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))
    assert header[:2] == vft.TABLE_COLUMNS[:2]
    assert set(vft.TABLE_COLUMNS) <= set(header)
    assert [r["flex_test"] for r in rows] == [f"FLEX-{i:03d}" for i in range(1, 11)]


def test_file_bytes_are_lf_utf8_without_bom():
    raw = vft.CSV_PATH.read_bytes()
    assert b"\r" not in raw
    assert not raw.startswith(b"\xef\xbb\xbf")


def test_missing_cells_are_empty_and_declared_never_zero(rows):
    for r in rows:
        declared = set(filter(None, r["source_dash_fields"].split(";")))
        assert declared <= set(vft.TABLE_COLUMNS), r["flex_test"]
        for col in vft.TABLE_COLUMNS:
            if col in declared:
                assert r[col] == "", f"{r['flex_test']}.{col} must stay empty"
            else:
                assert r[col] != "", f"{r['flex_test']}.{col} empty but not declared missing"


def test_numeric_cells_parse_and_are_physical(rows):
    for r in rows:
        for col in NUMERIC:
            if r[col] != "":
                assert float(r[col]) >= 0, (r["flex_test"], col)
        fractions = [r[c] for c in NUMERIC[1:5]]
        assert sum(float(x) for x in fractions) == pytest.approx(1.0, abs=0.011)


def test_outcomes_and_dates(rows):
    for r in rows:
        assert r["test_end"] in {"Extinction", "Disruption", "Completion"}
        assert r["fuel"] in {"Methanol", "Heptane"}
        printed = datetime.strptime(r["test_date_as_printed"], "%m/%d/%y").date()
        assert printed.isoformat() == r["test_date_iso"]
        assert (r["source_printed_page"], r["source_pdf_page"]) == ("20", "26")


def test_manifest_entry_is_measured_with_citation(entry):
    assert entry["evidence_class"] == "measured"
    assert entry["rights_status"] == "permitted_with_citation"
    assert entry["path"] == "data/curated/flex_tp2015216046_table_ix_001_010.csv"
    assert any(s["url"] == "https://ntrs.nasa.gov/citations/20150023456" for s in entry["sources"])
    assert all(s.get("quote") and s.get("page") for s in entry["sources"])
    assert vft.PDF_SHA256 in entry["description"]


def test_normalize_cell_is_typographic_only():
    assert vft.normalize_cell("–") == ""
    assert vft.normalize_cell(".21") == "0.21"
    assert vft.normalize_cell("0") == "0"
    assert vft.normalize_cell("FLEX–007") == "FLEX-007"
    assert vft.normalize_cell("2319.7") == "2319.7"


PRINTED = (
    "FLEX–004 30CAL02 3/31/09 17:16:18 Methanol 760 .21 .79 0 0 2.06 – .6 7.64 "
    "Extinction FLEX–005 30CAL03 3/31/09 19:00:48 Methanol 760 .21 .79 0 0 1.92 .81 .48 "
    "6.34 Extinction"
)


def test_compare_rows_accepts_faithful_transcription(rows):
    subset = [r for r in rows if r["flex_test"] in {"FLEX-004", "FLEX-005"}]
    parsed = vft.parse_table_rows(PRINTED, {"FLEX-004", "FLEX-005"})
    assert vft.compare_rows(subset, parsed) == []


@pytest.mark.parametrize(
    ("col", "bad"),
    [
        ("visible_flame_extinction_diameter_mm", "0"),  # dash turned into zero
        ("burning_rate_constant_mm2_per_s", "0.06"),  # digit slip
        ("test_end", "Disruption"),  # outcome swapped
    ],
)
def test_compare_rows_catches_mistranscription(rows, col, bad):
    row = dict(next(r for r in rows if r["flex_test"] == "FLEX-004"))
    row[col] = bad
    parsed = vft.parse_table_rows(PRINTED, {"FLEX-004"})
    assert vft.compare_rows([row], parsed)


def test_quote_check_flags_missing_quote():
    sources = [{"quote": "not in the text", "page": "20"}]
    assert vft.check_quotes(sources, lambda _p: "TABLE IX.—RESULTS")
    ok = [{"quote": "TABLE IX.—RESULTS", "page": "20"}]
    assert vft.check_quotes(ok, lambda _p: "TABLE  IX.—RESULTS\n") == []


@pytest.fixture(scope="module")
def flags():
    return vft.load_flags()


def test_flags_file_passes_structural_rules(flags, rows):
    assert vft.check_flags(flags, rows) == []


def test_flex_010_burning_rate_is_excluded_but_value_kept(flags, rows):
    row = next(r for r in rows if r["flex_test"] == "FLEX-010")
    assert row["burning_rate_constant_mm2_per_s"] == "0.37"  # printed value is not replaced
    excluded = [f for f in flags if f["ranking_use"] == "exclude"]
    assert [(f["flex_test"], f["field"]) for f in excluded] == [
        ("FLEX-010", "burning_rate_constant_mm2_per_s")
    ]


def test_every_row_carries_contamination_caveat(flags, rows):
    caveated = {f["flex_test"] for f in flags if f["flag"] == "contamination_caveat"}
    assert caveated == {r["flex_test"] for r in rows}


def test_check_flags_catches_unflagged_dash_and_dash_on_value(flags, rows):
    dropped = [
        f for f in flags if not (f["flex_test"] == "FLEX-004" and f["flag"] == "missing_dash")
    ]
    assert any("no missing_dash flag" in e for e in vft.check_flags(dropped, rows))
    bogus = dict(flags[0], flag="missing_dash", field="fuel", ranking_use="not_available")
    assert any("has a printed value" in e for e in vft.check_flags([*flags, bogus], rows))


def test_flags_entry_is_interpretation_of_measured(flags):
    e = vft.load_manifest_entry(dataset_id=vft.FLAGS_ID)
    assert e["evidence_class"] == "interpretation"
    assert e["derived_from"] == [vft.DATASET_ID]
    assert e["method"]


def test_flag_counts_and_stable_ids(flags):
    # Existing ids F001-F043 are never renumbered; new flags are appended.
    assert [f["flag_id"] for f in flags] == [f"F{i:03d}" for i in range(1, len(flags) + 1)]
    uses = [f["ranking_use"] for f in flags]
    assert (uses.count("exclude"), uses.count("not_available"), uses.count("caution")) == (1, 9, 35)


def test_flex_010_initial_diameter_has_imaging_caution(flags, rows):
    """Q3 finding S-2 (Member 5): saturated HiBMs image, Figure 14 caption."""
    hit = [
        f
        for f in flags
        if (f["flex_test"], f["field"], f["flag"])
        == ("FLEX-010", "initial_droplet_diameter_mm", "imaging_uncertainty")
    ]
    assert len(hit) == 1 and hit[0]["ranking_use"] == "caution"
    assert hit[0]["source_printed_page"] == "38"
    row = next(r for r in rows if r["flex_test"] == "FLEX-010")
    assert row["initial_droplet_diameter_mm"] == "3.86"  # printed value untouched


def test_flex_010_burn_time_derivation_unverified_not_rejected(flags, rows):
    """Q3 finding S-3: derivation unverified; the printed value is kept and not judged wrong."""
    hit = [f for f in flags if (f["flex_test"], f["field"]) == ("FLEX-010", "burn_time_s")]
    assert [f["flag"] for f in hit] == ["derivation_unverified"]
    assert hit[0]["ranking_use"] == "caution"  # not exclude
    assert "not judged incorrect" in hit[0]["reason"]
    row = next(r for r in rows if r["flex_test"] == "FLEX-010")
    assert row["burn_time_s"] == "13.6"


def test_contamination_reason_keeps_caution_and_adds_mitigating_assertion(flags):
    """Q3 suggestion S-5: quote the authors' p. 17 assertion; keep the limitation."""
    contam = [f for f in flags if f["flag"] == "contamination_caveat"]
    assert len(contam) == 10
    for f in contam:
        assert f["ranking_use"] == "caution"
        assert "unknown amount of conformal coating" in f["reason"]
        assert "minimally influenced by the contaminant" in f["reason"]
    embedded = vft.reason_quotes(contam)
    assert len(embedded) == 20 and {q["page"] for q in embedded} == {"17"}


def test_reason_quotes_parser_and_check():
    fl = [{"flag_id": "X", "reason": 'see p. 17: "alpha beta" and p. 38: "gamma"'}]
    assert vft.reason_quotes(fl) == [
        {"quote": "alpha beta", "page": "17", "flag_id": "X"},
        {"quote": "gamma", "page": "38", "flag_id": "X"},
    ]
    pages = {17: "xx alpha  beta yy", 38: "nothing"}
    errs = vft.check_quotes(vft.reason_quotes(fl), lambda p: pages[p])
    assert len(errs) == 1 and "gamma" in errs[0]


def test_manifest_is_valid_json_utf8():
    json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
