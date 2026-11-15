"""FLEX derivation scaffold (tools/derive_flex_findings.py): staging only, fail closed.

Real-data tests run the derivation on the registered FLEX files in this checkout. Tests that need
a different input copy the repository's data into a temporary folder and rewrite the manifest hash
so that only the intended defect is under test. Synthetic source titles (see `complete_gates`)
exist only in those temporary copies and are labelled SYNTHETIC; the real gates file is never
altered.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from decimal import Decimal
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
s10 = dv.s10
oracle = _load("comparability_oracle", "tests/test_comparability_outcome.py")

CSV_REL = "data/curated/flex_tp2015216046_table_ix_001_010.csv"
FLAGS_REL = "data/curated/interpretations/quality/flex_tp2015216046_table_ix_001_010.flags.csv"


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------


def write_json(path: Path, obj) -> None:
    text = json.dumps(obj)
    path.write_text(text, encoding="utf-8")


def make_root(tmp_path: Path, *, csv_text=None, flags_text=None, gates=None, outcomes=None) -> Path:
    """A throwaway copy of the files the derivation reads. Manifest hashes follow the edits."""
    root = tmp_path / "repo"
    for rel in (
        CSV_REL,
        FLAGS_REL,
        "data/manifest.json",
        "contracts/outcomes.json",
        "contracts/vocabulary.json",
        "tools/flex_derivation_gates.json",
        "tools/flex_curated_notes.json",
    ):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, root / rel)
    shutil.copytree(ROOT / "contracts" / "schemas", root / "contracts" / "schemas")
    if csv_text is not None:
        (root / CSV_REL).write_text(csv_text, encoding="utf-8", newline="")
    if flags_text is not None:
        (root / FLAGS_REL).write_text(flags_text, encoding="utf-8", newline="")
    if gates is not None:
        write_json((root / "tools/flex_derivation_gates.json"), gates)
    if outcomes is not None:
        write_json((root / "contracts/outcomes.json"), outcomes)
    manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["datasets"]:
        entry["sha256"] = hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest()
    write_json((root / "data/manifest.json"), manifest)
    return root


def real_gates():
    return json.loads((ROOT / "tools/flex_derivation_gates.json").read_text(encoding="utf-8"))


def complete_gates():
    return real_gates()


def drop_note_sources(root: Path) -> None:
    """Keep only the Table IX numeric Source (as if S10 registration had not happened)."""
    path = root / "data/manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entry = manifest["datasets"][0]
    entry["sources"] = [x for x in entry["sources"] if str(x["page"]) == "20"]
    write_json(path, manifest)


def synthetic_proposals():
    """SYNTHETIC unregistered Sources for every passage, only to exercise the proposal path."""
    out = {}
    for p in s10.passages(s10.load_flags()):
        out[f"{p.page}|{s10.normalize_text(p.quote)}"] = {
            "title": "SYNTHETIC TITLE (test only)",
            "url": s10.REPORT_URL,
            "page": str(p.page),
            "quote": p.quote,
            "retrieved": "2026-11-14",
            "archive_id": s10.ARCHIVE_ID,
        }
    return out


def csv_rows_text():
    return (ROOT / CSV_REL).read_text(encoding="utf-8")


def flags_text():
    return (ROOT / FLAGS_REL).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def real():
    return dv.derive(ROOT)


@pytest.fixture(scope="module")
def complete(real):
    return real


@pytest.fixture(scope="module")
def rows():
    return {r["flex_test"]: r for r in dv.read_rows(ROOT / CSV_REL)}


@pytest.fixture(scope="module")
def flags():
    return s10.load_flags()


def by_id(findings):
    return {f["id"]: f for f in findings}


# ---------------------------------------------------------------------------------------------
# What the current gates allow
# ---------------------------------------------------------------------------------------------


def test_the_real_run_stages_all_40_findings_and_withholds_none(real):
    assert len(real["findings"]) == 40 and real["withheld"] == []
    assert real["note_sources"]["unproposable"] == []
    assert len({f["id"] for f in real["findings"]}) == 40


def test_without_registered_note_sources_findings_are_withheld_never_weakened(tmp_path):
    """Fail closed: a Finding whose caution has no registered passage is withheld."""
    root = make_root(tmp_path)
    drop_note_sources(root)
    result = dv.derive(root)
    assert result["findings"] == [] and len(result["withheld"]) == 40
    assert all(w["flags"] and w["reason"].startswith("a required note") for w in result["withheld"])
    assert result["note_sources"]["registered"] == 0
    assert result["note_sources"]["proposed_unregistered"] == 0


def test_nothing_is_registrable_today(real):
    assert dv.registrable(real["gates"]) is False
    by_status = {g["id"]: g["status"] for g in real["gates"]["gates"]}
    assert by_status["S10-TITLES"] == "closed" and by_status["PR12"] == "open"
    open_ids = {k for k, v in by_status.items() if v == "open"}
    assert {"PR12", "PR17", "S10-REGISTRATION", "Q3", "B1-S11", "F042-NOTE"} <= open_ids
    assert by_status["G7"] == "closed" and "F042-NOTE" in open_ids
    decisions = real["gates"]["conditions"]
    assert {c["status"] for c in decisions.values()} == {"owner_provisional"}
    assert all(
        "not an independent scientific approval" in c["decided_by"] for c in decisions.values()
    )


def test_every_note_source_is_registered_after_s10_registration(real):
    counts = real["note_sources"]
    assert counts["registered"] == 96 and counts["proposed_unregistered"] == 0
    assert counts["proposed"] == [] and counts["unproposable"] == []


# ---------------------------------------------------------------------------------------------
# The complete derivation (synthetic titles in a temp copy): counts, values, notes
# ---------------------------------------------------------------------------------------------


def test_complete_derivation_has_40_findings_31_reported_8_not_reported_1_excluded(complete):
    findings = complete["findings"]
    assert len(findings) == 40 and complete["withheld"] == []
    assert dv.count_status(findings) == {"reported": 31, "not_reported": 8, "excluded": 1}
    ids = [f["id"] for f in findings]
    assert ids == sorted(set(ids), key=ids.index), "ids are unique"
    assert (
        ids[0] == "flex.flex-001.initial_droplet_diameter" and ids[-1] == "flex.flex-010.burn_time"
    )
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9_.-]*", i) for i in ids)


def test_values_equal_the_exact_source_cells_and_zero_stays_zero(complete, rows):
    for f in complete["findings"]:
        test = f["test_id"]
        field = next(c for c, q, _ in dv.QUANTITIES if q == f["quantity"])
        cell = rows[test][field]
        if f["value_status"] == "reported":
            assert Decimal(str(f["value"])) == Decimal(cell), f["id"]
            assert not isinstance(f["value"], str)
            assert isinstance(f["value"], int) == bool(re.fullmatch(r"-?\d+", cell))
        else:
            assert f["value"] is None


def test_number_parsing_is_strict_and_exact():
    assert dv.number("0", "x") == 0 and isinstance(dv.number("0", "x"), int)
    assert dv.number("0.37", "x") == 0.37 and dv.number("5", "x") == 5
    for bad in ("", "-", "abc", "NaN", "Infinity", "1e999999"):
        with pytest.raises(dv.DerivationError):
            dv.number(bad, "x")
    with pytest.raises(dv.DerivationError, match="not exactly representable"):
        dv.number("0.1000000000000000055511151231257827", "x")


def test_units_come_from_the_vocabulary_and_burning_rate_is_mm2_per_s(complete):
    units = {f["quantity"]: f["unit"] for f in complete["findings"]}
    assert units == {
        "initial_droplet_diameter": "mm",
        "visible_flame_extinction_diameter": "mm",
        "burning_rate_constant": "mm2/s",
        "burn_time": "s",
    }


def test_pressure_uses_the_exact_mmhg_factor_not_the_torr_approximation(complete, rows):
    assert dv.KPA_PER_MMHG == Decimal("0.133322387415")
    for f in complete["findings"]:
        mmhg = Decimal(rows[f["test_id"]]["ambient_pressure_mmhg"])
        assert f["conditions"]["pressure_kpa"] == float(mmhg * Decimal("0.133322387415"))
        assert f["conditions"]["pressure_kpa"] != float(mmhg * Decimal("0.133322368421"))


def test_conditions_have_every_key_and_unknowns_are_null(complete, rows):
    keys = {
        "gravity_environment",
        "oxygen_mole_fraction",
        "pressure_kpa",
        "flow_velocity_mm_s",
        "flow_configuration",
        "diluent",
        "fuel_or_material",
        "sample_geometry",
    }
    for f in complete["findings"]:
        c = f["conditions"]
        assert set(c) == keys
        assert c["gravity_environment"] == "microgravity"
        assert c["flow_velocity_mm_s"] is None and c["flow_configuration"] is None
        assert c["sample_geometry"] is None, "unapproved: never guessed"
        assert c["oxygen_mole_fraction"] == float(rows[f["test_id"]]["o2_mole_fraction"])
    f10 = next(f for f in complete["findings"] if f["id"] == "flex.flex-010.burn_time")
    assert f10["conditions"]["diluent"] == "CO2 0.7; N2 0.09", (
        "the printed mixture, not a single N2"
    )
    assert {f["conditions"]["fuel_or_material"] for f in complete["findings"]} == {
        "Methanol",
        "Heptane",
    }


def test_flex_001_keeps_its_printed_disruption_and_its_extinction_diameter(complete):
    f = by_id(complete["findings"])["flex.flex-001.visible_flame_extinction_diameter"]
    assert (
        f["test_outcome"] == "Disruption" and f["value"] == 0.89 and f["value_status"] == "reported"
    )
    assert not [
        x
        for x in complete["findings"]
        if x["test_id"] == "FLEX-001" and x["test_outcome"] != "Disruption"
    ]
    assert "F005" in {n["flag_ref"]["flag_id"] for n in f["curation_notes"]}, (
        "the ambiguity is carried"
    )
    assert "xtinction" not in f["statement"].replace("extinction diameter", "")


PRINTED_VALUE = re.compile(r"(?<![\d.])0?\.37(?!\d)")
CURATED_F042 = (
    "Table IX reports a burning-rate constant for FLEX-010, but Figure 14 states that no "
    "burning-rate constant is reported. The disputed measurement is excluded from quantitative "
    "use pending reconciliation with PSI data."
)


def test_flex_010_diameter_and_burn_time_keep_their_values_with_separate_cautions(complete):
    fs = by_id(complete["findings"])
    d = fs["flex.flex-010.initial_droplet_diameter"]
    t = fs["flex.flex-010.burn_time"]
    assert d["value_status"] == "reported" and t["value_status"] == "reported"
    assert t["value"] == 13.6
    assert "F044" in {n["flag_ref"]["flag_id"] for n in d["curation_notes"]}
    assert "F045" not in {n["flag_ref"]["flag_id"] for n in d["curation_notes"]}
    assert "F045" in {n["flag_ref"]["flag_id"] for n in t["curation_notes"]}
    assert "F044" not in {n["flag_ref"]["flag_id"] for n in t["curation_notes"]}
    assert "incorrect" not in t["statement"].lower()


def test_row_wide_and_outcome_flags_reach_every_finding_of_the_test_and_field_flags_only_theirs(
    complete, flags
):
    for f in complete["findings"]:
        got = {n["flag_ref"]["flag_id"] for n in f.get("curation_notes", [])}
        field = next(c for c, q, _ in dv.QUANTITIES if q == f["quantity"])
        want = {
            fl["flag_id"]
            for fl in flags
            if fl["flex_test"] == f["test_id"]
            and fl["ranking_use"] != "not_available"
            and fl["field"] in (field, "*", "test_end")
        }
        assert got == want, f["id"]


def test_dashes_become_not_reported_and_never_a_note(complete, flags):
    not_available = {fl["flag_id"] for fl in flags if fl["ranking_use"] == "not_available"}
    for f in complete["findings"]:
        assert not {n["flag_ref"]["flag_id"] for n in f.get("curation_notes", [])} & not_available
    nr = [f for f in complete["findings"] if f["value_status"] == "not_reported"]
    assert len(nr) == 8
    assert sum(1 for f in nr if f["test_id"] == "FLEX-009") == 4
    assert not [f for f in complete["findings"] if f["quantity"] is None]
    assert not any("test_time" in f["id"] for f in complete["findings"]), (
        "metadata never becomes a Finding"
    )


def test_notes_resolve_to_their_flag_with_matching_kind_page_and_quote(complete, flags):
    by_flag = {fl["flag_id"]: fl for fl in flags}
    curated = dv.load_curated_notes()
    kinds = {"caution": "caution", "exclude": "exclusion"}
    for f in complete["findings"]:
        for n in f.get("curation_notes", []):
            fl = by_flag[n["flag_ref"]["flag_id"]]
            assert n["flag_ref"]["manifest_id"] == dv.FLAGS_ID
            assert fl["flex_test"] == f["test_id"]
            assert n["kind"] == kinds[fl["ranking_use"]] and n["generated_by"] == "FlameGuard-SI"
            expected = curated[fl["flag_id"]]["note"] if fl["flag_id"] in curated else fl["reason"]
            assert n["note"] == expected
            assert n["source"]["quote"] == fl["source_quote"]
            assert str(n["source"]["page"]) == fl["source_printed_page"]


def test_every_note_rests_on_a_registered_source_with_its_own_quote(real):
    registered = s10.load_measured_sources()
    for f in real["findings"]:
        for n in f.get("curation_notes", []):
            src = n["source"]
            assert any(
                str(r["page"]) == str(src["page"])
                and r.get("quote")
                and s10.normalize_text(src["quote"]) in s10.normalize_text(r["quote"])
                and r["title"] == src["title"]
                for r in registered
            ), f"{f['id']}: {n['flag_ref']['flag_id']} rests on an unregistered source"


def test_numeric_provenance_and_caution_sources_are_never_mixed(real):
    numeric, _ = s10.split_sources(s10.load_measured_sources())
    for f in real["findings"]:
        assert f["provenance"]["sources"] == numeric
        for n in f.get("curation_notes", []):
            assert int(n["source"]["page"]) != s10.TABLE_IX_PAGE
            assert n["source"] not in numeric
    assert real["investigation"]["sources"] == numeric


def test_test_identity_and_outcome_are_complete_and_pass_the_contract_oracle(complete):
    outcomes = {"Extinction", "Disruption", "Completion"}
    for f in complete["findings"]:
        assert re.fullmatch(r"FLEX-\d{3}", f["test_id"]) and f["test_outcome"] in outcomes
    assert oracle.identity_violations(complete["findings"]) == []


def test_findings_and_investigation_satisfy_the_schemas_and_s1_to_s4(complete, validator_for):
    finding_v, inv_v = (
        validator_for("finding.schema.json"),
        validator_for("investigation.schema.json"),
    )
    for f in complete["findings"]:
        errors = list(finding_v.iter_errors(f))
        assert not errors, (f["id"], errors[0].message)
    assert not list(inv_v.iter_errors(complete["investigation"]))
    assert {f["provenance"]["manifest_id"] for f in complete["findings"]} == {dv.FINDINGS_ID}
    assert complete["investigation"]["datasets"] == [dv.FINDINGS_ID]
    assert all(
        f["evidence_class"] == "measured" and "derived_from" not in f["provenance"]
        for f in complete["findings"]
    )
    assert {f["investigation_id"] for f in complete["findings"]} == {
        complete["investigation"]["id"]
    }


def test_locators_point_at_the_exact_cell_without_stating_the_value(complete):
    f = by_id(complete["findings"])["flex.flex-010.burning_rate_constant"]
    assert "FLEX-010" in f["provenance"]["locator"] and "CSV line 11" in f["provenance"]["locator"]
    assert "printed p. 20 (PDF p. 26)" in f["provenance"]["locator"]
    assert not re.search(r"\d*\.\d+", f["statement"]), f["statement"]  # no decimal value


# ---------------------------------------------------------------------------------------------
# Staging: isolation, determinism, honesty
# ---------------------------------------------------------------------------------------------


def snapshot(*folders):
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in folders
        for p in sorted((ROOT / folder).rglob("*"))
        if p.is_file() and "raw" not in p.parts
    }


def test_staging_changes_nothing_in_the_repository_and_registers_nothing(tmp_path):
    before = snapshot("data", "contracts", "tools")
    report = dv.stage(tmp_path / "out")
    assert snapshot("data", "contracts", "tools") == before
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    assert [d["id"] for d in manifest["datasets"]] == [dv.CSV_ID, dv.FLAGS_ID]
    assert report["registrable"] is False and report["status"].startswith("STAGING ONLY")
    assert (tmp_path / "out" / "NOT_REGISTERED.txt").is_file()
    assert {e["id"] for e in report["proposed_manifest_entries_not_applied"]} == {
        dv.FINDINGS_ID,
        dv.INVESTIGATIONS_ID,
    }


@pytest.mark.parametrize(
    "inside",
    ["data", "data/curated", "data/curated/findings", "contracts", "tools", "backend", "frontend"],
)
def test_staging_refuses_to_write_inside_the_repository(inside):
    with pytest.raises(dv.DerivationError, match="must not be inside"):
        dv.stage(ROOT / inside / "flex-staging")


def test_staging_refuses_a_non_empty_folder(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "x").write_text("x", encoding="utf-8")
    with pytest.raises(dv.DerivationError, match="not empty"):
        dv.stage(tmp_path / "out")


def test_the_derivation_is_byte_identical_and_ids_are_stable(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    dv.stage(a)
    dv.stage(b)
    for rel in ("investigations.json", "findings/flex.json", "STAGING_REPORT.json"):
        assert (a / rel).read_bytes() == (b / rel).read_bytes()
        assert b"\r" not in (a / rel).read_bytes()
    report = json.loads((a / "STAGING_REPORT.json").read_text(encoding="utf-8"))
    assert (
        report["outputs_sha256"]["findings/flex.json"]
        == hashlib.sha256((a / "findings/flex.json").read_bytes()).hexdigest()
    )


def test_the_staged_json_is_strict_json_with_no_nan(tmp_path):
    dv.stage(tmp_path / "out")
    for rel in ("investigations.json", "findings/flex.json"):
        json.loads(
            (tmp_path / "out" / rel).read_text(encoding="utf-8"),
            parse_constant=lambda c: pytest.fail(c),
        )


def test_registrable_needs_every_gate_closed_and_every_decision_approved():
    gates = real_gates()
    for g in gates["gates"]:
        g["status"] = "closed"
    for c in gates["conditions"].values():
        c["status"] = "approved"
    assert dv.registrable(gates) is True
    for i in range(len(gates["gates"])):
        g2 = copy.deepcopy(gates)
        g2["gates"][i]["status"] = "open"
        assert dv.registrable(g2) is False, gates["gates"][i]["id"]
    for k in gates["conditions"]:
        g3 = copy.deepcopy(gates)
        g3["conditions"][k]["status"] = "proposed"
        assert dv.registrable(g3) is False, k


def test_closed_gates_alone_do_not_make_proposed_sources_registered(tmp_path):
    gates = real_gates()
    gates["proposed_note_sources"] = synthetic_proposals()
    for g in gates["gates"]:
        g["status"] = "closed"
    for c in gates["conditions"].values():
        c["status"] = "approved"
    root = make_root(tmp_path, gates=gates)
    drop_note_sources(root)
    report = dv.stage(tmp_path / "out", root)
    assert report["note_sources"]["proposed_unregistered"] > 0
    assert report["registrable"] is False, "unregistered note sources still block registration"
    clean = dv.stage(tmp_path / "clean", make_root(tmp_path / "c", gates=gates))
    assert clean["registrable"] is True, "all closed, approved, registered: the only way to True"


def test_a_note_never_takes_an_unknown_source_title(tmp_path):
    root = make_root(tmp_path)
    drop_note_sources(root)
    result = dv.derive(root)
    for f in result["findings"]:
        for n in f.get("curation_notes", []):
            assert n["source"]["title"] and not n["source"]["title"].startswith("SYNTHETIC")
    assert not result["findings"]


# ---------------------------------------------------------------------------------------------
# Fail closed on bad inputs
# ---------------------------------------------------------------------------------------------


def edit_csv(text, test, column, new):
    lines = text.splitlines()
    head = lines[0].split(",")
    i = head.index(column)
    for n, line in enumerate(lines):
        cells = line.split(",")
        if cells[0] == test:
            cells[i] = new
            lines[n] = ",".join(cells)
    return "\n".join(lines) + "\n"


def drop_flag(text, flag_id):
    return "".join(
        line for line in text.splitlines(keepends=True) if not line.startswith(flag_id + ",")
    )


def test_a_hash_that_differs_from_the_manifest_is_refused(tmp_path):
    root = make_root(tmp_path)
    (root / CSV_REL).write_text(
        csv_rows_text().replace("1.69", "1.70"), encoding="utf-8", newline=""
    )
    with pytest.raises(dv.DerivationError, match="sha256 differs"):
        dv.derive(root)
    root2 = make_root(tmp_path / "b")
    extra = flags_text() + "\n"
    (root2 / FLAGS_REL).write_text(extra, encoding="utf-8", newline="")
    with pytest.raises(dv.DerivationError, match="sha256 differs"):
        dv.derive(root2)


def test_missing_manifest_entry_or_wrong_class_is_refused(tmp_path):
    root = make_root(tmp_path)
    manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
    manifest["datasets"] = manifest["datasets"][:1]
    write_json((root / "data/manifest.json"), manifest)
    with pytest.raises(dv.DerivationError, match="exactly one entry"):
        dv.derive(root)
    root2 = make_root(tmp_path / "b")
    manifest = json.loads((root2 / "data/manifest.json").read_text(encoding="utf-8"))
    manifest["datasets"][0]["evidence_class"] = "interpretation"
    write_json((root2 / "data/manifest.json"), manifest)
    with pytest.raises(dv.DerivationError, match="evidence_class"):
        dv.derive(root2)


def test_crlf_and_non_utf8_inputs_are_refused(tmp_path):
    with pytest.raises(dv.DerivationError, match="CR"):
        dv.derive(make_root(tmp_path, csv_text=csv_rows_text().replace("\n", "\r\n")))
    root = make_root(tmp_path / "b")
    (root / CSV_REL).write_bytes(b"\xff\xfe bad")
    manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
    for e in manifest["datasets"]:
        e["sha256"] = hashlib.sha256((root / e["path"]).read_bytes()).hexdigest()
    write_json((root / "data/manifest.json"), manifest)
    with pytest.raises(dv.DerivationError, match="UTF-8"):
        dv.derive(root)


def test_exactly_ten_known_tests_are_required(tmp_path):
    text = csv_rows_text()
    short = "\n".join(line for line in text.splitlines() if not line.startswith("FLEX-010")) + "\n"
    with pytest.raises(dv.DerivationError, match="expected exactly"):
        dv.derive(make_root(tmp_path, csv_text=short))
    dup = text + text.splitlines()[1] + "\n"
    with pytest.raises(dv.DerivationError, match="expected exactly"):
        dv.derive(make_root(tmp_path / "b", csv_text=dup))


def test_unexpected_columns_are_refused(tmp_path):
    text = csv_rows_text().replace("test_end,", "test_end,extra,", 1)
    with pytest.raises(dv.DerivationError, match="unexpected CSV columns"):
        dv.derive(make_root(tmp_path, csv_text=text))


def test_a_blank_cell_without_a_not_available_flag_is_refused(tmp_path):
    text = edit_csv(csv_rows_text(), "FLEX-002", "burn_time_s", "")
    with pytest.raises(dv.DerivationError, match="blank cell and source_dash_fields disagree"):
        dv.derive(make_root(tmp_path, csv_text=text))


def test_a_declared_dash_without_its_flag_is_refused(tmp_path):
    with pytest.raises(dv.DerivationError, match="needs its not_available flag"):
        dv.derive(make_root(tmp_path, flags_text=drop_flag(flags_text(), "F036")))


def test_a_not_available_flag_on_a_value_is_refused(tmp_path):
    text = flags_text().replace(
        "F024,FLEX-007,burning_rate_constant_mm2_per_s,imaging_uncertainty,caution",
        "F024,FLEX-007,burning_rate_constant_mm2_per_s,missing_dash,not_available",
    )
    with pytest.raises(dv.DerivationError, match="needs its not_available flag, and only a dash"):
        dv.derive(make_root(tmp_path, flags_text=text))


def test_an_unreadable_number_is_refused(tmp_path):
    text = edit_csv(
        csv_rows_text(), "FLEX-003", "burn_time_s", "4,5"
    )  # decimal comma splits the cell
    with pytest.raises(dv.DerivationError):
        dv.derive(make_root(tmp_path, csv_text=text))
    text = edit_csv(csv_rows_text(), "FLEX-003", "burn_time_s", "NaN")
    with pytest.raises(dv.DerivationError, match="not finite"):
        dv.derive(make_root(tmp_path / "b", csv_text=text))


def test_an_unconfirmed_or_unknown_outcome_is_refused(tmp_path):
    text = edit_csv(csv_rows_text(), "FLEX-004", "test_end", "Burnout")
    with pytest.raises(dv.DerivationError, match="not in outcomes.json"):
        dv.derive(make_root(tmp_path, csv_text=text))
    outcomes = json.loads((ROOT / "contracts/outcomes.json").read_text(encoding="utf-8"))
    outcomes["status"] = "UNCONFIRMED"
    with pytest.raises(dv.DerivationError, match="not CONFIRMED"):
        dv.derive(make_root(tmp_path / "b", outcomes=outcomes))


def test_bad_flags_are_refused(tmp_path):
    base = flags_text()
    cases = {
        "duplicate id": (base + base.splitlines()[1] + "\n", "duplicate flag ids"),
        "unknown test": (base.replace("F002,FLEX-001", "F002,FLEX-099"), "unknown test"),
        "field maps to nothing": (
            base.replace("F002,FLEX-001,initial_droplet_diameter_mm", "F002,FLEX-001,not_a_field"),
            "maps to nothing",
        ),
        "blank quote on a caution": (
            re.sub(r"(F006,[^\n]*?),30,[^\n]*", r"\1,30,", base),
            "verbatim source quote",
        ),
        "unknown ranking_use": (
            base.replace(
                "F006,FLEX-002,*,calibration_test,caution", "F006,FLEX-002,*,calibration_test,maybe"
            ),
            "unknown ranking_use",
        ),
        "non-integer page": (
            base.replace(
                ",30,Because this was a calibration run\n",
                ",xx,Because this was a calibration run\n",
                1,
            ),
            "positive integer",
        ),
    }
    for i, (_name, (text, fragment)) in enumerate(cases.items()):
        with pytest.raises((dv.DerivationError, s10.S10Error), match=fragment):
            dv.derive(make_root(tmp_path / str(i), flags_text=text))


def test_a_metadata_flag_other_than_a_dash_is_refused(tmp_path):
    text = flags_text().replace(
        "F039,FLEX-009,test_time_gmt,missing_dash,not_available",
        "F039,FLEX-009,test_time_gmt,imaging_uncertainty,caution",
    )
    with pytest.raises(dv.DerivationError, match="only a dash may be flagged on metadata"):
        dv.derive(make_root(tmp_path, flags_text=text))


def test_the_gates_file_must_decide_exactly_the_three_conditions(tmp_path):
    gates = real_gates()
    del gates["conditions"]["sample_geometry"]
    with pytest.raises(dv.DerivationError, match="exactly diluent"):
        dv.derive(make_root(tmp_path, gates=gates))


def test_the_command_line_refuses_and_exits_nonzero_inside_data(capsys):
    assert dv.main(["--stage", str(ROOT / "data" / "x")]) == 1
    assert "derivation refused" in capsys.readouterr().out


# ---------------------------------------------------------------------------------------------
# Decision 1: the number-free curated F042 exclusion note (S9)
# ---------------------------------------------------------------------------------------------

ex = _load("exclusion_oracle", "tests/test_exclusion_dependency.py")
FLEX10 = "flex.flex-010.burning_rate_constant"
PRINTED_VALUES = {FLEX10: "0.37"}


def f042(findings):
    f = by_id(findings)[FLEX10]
    return f, next(n for n in f["curation_notes"] if n["flag_ref"]["flag_id"] == "F042")


def explanation(note: str, fid="flex.explain-flex-010", parents=None):
    doc = copy.deepcopy(ex.INTERP)
    doc.update(id=fid, investigation_id="flex", statement="SYNTHETIC explanation of an exclusion.")
    doc["provenance"] = {**doc["provenance"], "derived_from": parents or [FLEX10]}
    doc.pop("relevant_environments", None)
    doc.update(quantity=None, value=None, unit=None, value_status="not_applicable")
    doc["limitations"] = [f"Explains why a value was excluded: {note}"]
    return doc


def test_the_original_printed_value_stays_in_the_raw_source_and_the_audited_flag(rows, flags):
    assert rows["FLEX-010"]["burning_rate_constant_mm2_per_s"] == "0.37"
    f42_row = next(f for f in flags if f["flag_id"] == "F042")
    assert ".37" in f42_row["reason"], "the audited reason is untouched"
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["datasets"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    # the derivation accepts these registered bytes, so it read them unchanged
    assert dv.derive(ROOT)["inputs"][dv.CSV_ID] == manifest["datasets"][0]["sha256"]


def test_the_derived_finding_is_excluded_with_a_null_value(complete):
    f, _ = f042(complete["findings"])
    assert f["value"] is None and f["value_status"] == "excluded"
    assert "0.37" not in json.dumps({k: v for k, v in f.items() if k != "curation_notes"})


def test_the_curated_note_is_exactly_the_reviewed_text_and_number_free(complete):
    _, note = f042(complete["findings"])
    assert note["kind"] == "exclusion" and note["note"] == CURATED_F042
    assert Decimal("0.37") not in dv.numbers_in(note["note"])
    assert not PRINTED_VALUE.search(note["note"])
    assert dv.load_curated_notes()["F042"]["note"] == CURATED_F042


def test_nothing_the_derivation_writes_states_the_excluded_number(complete, tmp_path):
    dv.stage(tmp_path / "out", make_root(tmp_path))
    text = "".join(
        p.read_text(encoding="utf-8") for p in (tmp_path / "out").rglob("*") if p.is_file()
    )
    assert not PRINTED_VALUE.search(text), (
        "the excluded printed value leaked into the staging output"
    )
    assert not PRINTED_VALUE.search(json.dumps(complete["findings"]))


def test_the_curated_note_stays_traceable_to_f042_its_audited_reason_and_its_quotation(
    complete, flags, tmp_path
):
    _, note = f042(complete["findings"])
    f042_row = next(f for f in flags if f["flag_id"] == "F042")
    assert note["flag_ref"] == {"manifest_id": dv.FLAGS_ID, "flag_id": "F042"}
    assert note["source"]["quote"] == f042_row["source_quote"]
    assert str(note["source"]["page"]) == f042_row["source_printed_page"] == "38"
    entry = dv.load_curated_notes()["F042"]
    assert entry["original_reason"] == f042_row["reason"]
    assert (
        entry["original_reason_sha256"] == hashlib.sha256(f042_row["reason"].encode()).hexdigest()
    )
    report = dv.stage(tmp_path / "out", make_root(tmp_path))
    applied = report["curated_notes_applied"]
    assert [a["flag_id"] for a in applied] == ["F042"]
    assert applied[0]["original_reason_sha256"] == entry["original_reason_sha256"]
    assert applied[0]["curated_note_sha256"] == hashlib.sha256(CURATED_F042.encode()).hexdigest()


def test_a_changed_audited_reason_makes_the_curated_note_stale_and_is_refused(tmp_path):
    text = flags_text().replace("Table IX prints .37 but", "Table IX prints .38 but")
    assert text != flags_text()
    with pytest.raises(dv.DerivationError, match="audited reason changed"):
        dv.derive(make_root(tmp_path, flags_text=text))


def test_without_a_curated_note_an_exclusion_that_states_the_value_is_refused(tmp_path):
    root = make_root(tmp_path)
    write_json(root / "tools/flex_curated_notes.json", {"notes": {}})
    with pytest.raises(dv.DerivationError, match="states the excluded value"):
        dv.derive(root)


def test_interpretations_and_answers_can_quote_the_exact_curated_note_under_s9(complete):
    finding, note = f042(complete["findings"])
    interp = explanation(note["note"])
    chain = [finding, interp, explanation(note["note"], "flex.explain-2", [interp["id"]])]
    answer = ex._answer(f"The value was excluded. {note['note']}", [], [interp["id"]])
    assert ex.exclusion_violations(chain, answer=answer, printed_values=PRINTED_VALUES) == []


def test_s9_still_catches_the_original_reason_or_the_number_in_downstream_text(complete):
    finding, note = f042(complete["findings"])
    original = dv.load_curated_notes()["F042"]["original_reason"]
    bad = explanation(note["note"])
    bad["limitations"].append(original)  # the audited reason states .37
    assert any(
        "states printed value" in v
        for v in ex.exclusion_violations([finding, bad], printed_values=PRINTED_VALUES)
    )
    interp = explanation(note["note"])
    answer = ex._answer(f"{note['note']} It was 0.37.", [], [interp["id"]])
    violations = ex.exclusion_violations(
        [finding, interp], answer=answer, printed_values=PRINTED_VALUES
    )
    assert any("states printed value" in v for v in violations)


def test_an_interpretation_must_still_quote_the_exact_curated_note(complete):
    finding, _ = f042(complete["findings"])
    vague = explanation("An excluded value.")
    assert any(
        "do not quote the exclusion note" in v
        for v in ex.exclusion_violations([finding, vague], printed_values=PRINTED_VALUES)
    )


def test_no_ranking_comparison_or_answer_may_use_the_excluded_measurement(complete):
    finding, note = f042(complete["findings"])
    ranking = copy.deepcopy(ex._load("ranking.example.json"))
    ranking["items"][0]["criterion_scores"][0]["inputs"] = [
        {"finding_id": FLEX10, "evidence_class": "measured"}
    ]
    assert any(
        "ranking input" in v
        for v in ex.exclusion_violations([finding], ranking=ranking, printed_values=PRINTED_VALUES)
    )
    comparison = copy.deepcopy(ex._load("comparison.example.json"))
    comparison["comparable"] = True
    comparison["rows"][0]["finding_id"] = FLEX10
    assert any(
        "comparable row" in v
        for v in ex.exclusion_violations(
            [finding], comparison=comparison, printed_values=PRINTED_VALUES
        )
    )
    answer = ex._answer("FLEX-010 shows a clear burning rate.", [], [FLEX10])
    answer["citations"][0]["evidence_class"] = "measured"
    assert any(
        "does not give its exclusion reason" in v
        for v in ex.exclusion_violations([finding], answer=answer, printed_values=PRINTED_VALUES)
    )


def test_the_derivation_produces_no_ranking_comparison_or_answer_documents(tmp_path):
    dv.stage(tmp_path / "out", make_root(tmp_path))
    names = sorted(
        str(p.relative_to(tmp_path / "out")) for p in (tmp_path / "out").rglob("*") if p.is_file()
    )
    assert names == [
        "NOT_REGISTERED.txt",
        "STAGING_REPORT.json",
        "findings/flex.json",
        "investigations.json",
    ]


# ---------------------------------------------------------------------------------------------
# Decision 3: provisional G7 representation (project-owner decision, not scientific approval)
# ---------------------------------------------------------------------------------------------


def row_with(rows, **changes):
    row = dict(rows["FLEX-001"])
    row.update(changes)
    return row


def test_diluent_is_the_printed_nonzero_fractions_with_species_in_a_fixed_order(rows):
    assert dv.diluent_text(rows["FLEX-001"]) == "N2 0.79"
    assert dv.diluent_text(rows["FLEX-010"]) == "CO2 0.7; N2 0.09"
    mixed = row_with(
        rows, n2_mole_fraction="0.10", co2_mole_fraction="0.5", he_mole_fraction="0.19"
    )
    assert dv.diluent_text(mixed) == "CO2 0.5; He 0.19; N2 0.10", (
        "alphabetical, fractions as printed"
    )
    assert dv.diluent_text(row_with(rows, o2_mole_fraction="1", n2_mole_fraction="0")) is None


def test_diluent_order_does_not_depend_on_column_order(rows):
    row = row_with(rows, n2_mole_fraction="0.3", co2_mole_fraction="0.4", he_mole_fraction="0.09")
    shuffled = dict(reversed(list(row.items())))
    assert dv.diluent_text(row) == dv.diluent_text(shuffled) == "CO2 0.4; He 0.09; N2 0.3"


def test_different_mixtures_never_collide_and_swapped_species_stay_distinct(rows):
    grid = ["0", "0.1", "0.2"]
    seen = {}
    for n2 in grid:
        for co2 in grid:
            for he in grid:
                text = dv.diluent_text(
                    row_with(rows, n2_mole_fraction=n2, co2_mole_fraction=co2, he_mole_fraction=he)
                )
                key = (Decimal(n2), Decimal(co2), Decimal(he))
                assert seen.setdefault(text, key) == key, f"{text!r} is ambiguous"
    a = dv.diluent_text(row_with(rows, n2_mole_fraction="0.5", co2_mole_fraction="0"))
    b = dv.diluent_text(row_with(rows, n2_mole_fraction="0", co2_mole_fraction="0.5"))
    assert a != b and "N2" in a and "CO2" in b


def test_printed_spelling_of_a_fraction_is_never_reformatted(rows):
    assert dv.diluent_text(row_with(rows, n2_mole_fraction="0.70")) == "N2 0.70"
    assert dv.diluent_text(row_with(rows, n2_mole_fraction="0.7")) == "N2 0.7"


def test_mole_fractions_must_be_in_range_and_add_up(rows):
    for column, bad in (
        ("n2_mole_fraction", "0.5"),
        ("co2_mole_fraction", "-0.1"),
        ("he_mole_fraction", "1.2"),
    ):
        with pytest.raises(dv.DerivationError):
            dv.check_composition(row_with(rows, **{column: bad}))
    dv.check_composition(rows["FLEX-010"])  # 0.21 + 0.09 + 0.7 = 1.00
    dv.check_composition(row_with(rows, n2_mole_fraction="0.80"))  # within two-decimal rounding
    with pytest.raises(dv.DerivationError, match="add up"):
        dv.check_composition(row_with(rows, n2_mole_fraction="0.85"))


def test_the_fuel_name_is_preserved_exactly_and_a_missing_fuel_is_refused(rows):
    gates = real_gates()
    for fuel in ("Methanol", "Heptane", "heptane", "n-Heptane"):
        assert dv.conditions(row_with(rows, fuel=fuel), gates)["fuel_or_material"] == fuel
    assert dv.conditions(row_with(rows, fuel=" Heptane "), gates)["fuel_or_material"] == "Heptane"
    with pytest.raises(dv.DerivationError, match="fuel name is missing"):
        dv.conditions(row_with(rows, fuel="  "), gates)
    assert len({"Methanol", "methanol", "METHANOL"}) == 3, "case differences are not merged"


def test_sample_geometry_is_null_unless_a_source_supports_it(complete):
    assert {f["conditions"]["sample_geometry"] for f in complete["findings"]} == {None}
    assert real_gates()["conditions"]["sample_geometry"]["use"] == "null"


def test_pressure_is_exact_never_rounded_and_the_printed_mmhg_is_kept(complete, rows):
    for f in complete["findings"]:
        mmhg = rows[f["test_id"]]["ambient_pressure_mmhg"]
        exact = Decimal(mmhg) * dv.KPA_PER_MMHG
        assert Decimal(repr(f["conditions"]["pressure_kpa"])) == exact, "no rounding in the data"
        assert f"ambient pressure as printed: {mmhg} mmHg" in f["provenance"]["locator"]
    f = by_id(complete["findings"])["flex.flex-001.initial_droplet_diameter"]
    assert f["conditions"]["pressure_kpa"] == float(Decimal("757.7") * Decimal("0.133322387415"))
    assert len(repr(f["conditions"]["pressure_kpa"]).split(".")[1]) > 6, (
        "full precision, not display rounding"
    )


def test_g7_decisions_are_recorded_as_owner_decisions_not_approvals():
    gates = real_gates()
    for name, c in gates["conditions"].items():
        assert c["status"] == "owner_provisional", name
        assert "not an independent scientific approval" in c["decided_by"]
    assert "not an independent scientific approval" in gates["pressure"]["decided_by"]
    assert dv.registrable(gates) is False


def test_a_dash_that_is_also_excluded_is_refused(tmp_path):
    extra = (
        "F046,FLEX-009,burn_time_s,disputed_value,exclude,SYNTHETIC contradiction,37,"
        "No Image Processing and Storage Unit (IPSU) data were downlinked for this test.\n"
    )
    with pytest.raises(dv.DerivationError, match="a dash cannot also be excluded"):
        dv.derive(make_root(tmp_path, flags_text=flags_text() + extra))


def test_exactly_one_numeric_table_source_is_required(tmp_path):
    for n, edit in enumerate(("drop", "duplicate")):
        root = make_root(tmp_path / str(n))
        manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
        entry = manifest["datasets"][0]
        table = next(s for s in entry["sources"] if str(s["page"]) == "20")
        entry["sources"] = [s for s in entry["sources"] if s is not table]
        if edit == "duplicate":
            entry["sources"] += [table, copy.deepcopy(table)]
        write_json(root / "data/manifest.json", manifest)
        with pytest.raises(dv.DerivationError, match="exactly one numeric"):
            dv.derive(root)


def test_an_out_of_range_fraction_is_refused_even_when_the_total_is_one(rows):
    cases = [
        {"co2_mole_fraction": "-0.1", "n2_mole_fraction": "0.89"},  # sums to 1.00
        {"he_mole_fraction": "1.05", "n2_mole_fraction": "-0.26"},  # sums to 1.00
    ]
    for change in cases:
        with pytest.raises(dv.DerivationError, match="outside 0..1"):
            dv.check_composition(row_with(rows, **change))
