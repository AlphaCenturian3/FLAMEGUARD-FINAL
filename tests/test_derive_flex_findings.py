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
    """SYNTHETIC titles for the two section-text passages, only so a complete run can be counted."""
    gates = real_gates()
    for p in s10.passages(s10.load_flags()):
        if (
            p.page in (16, 17)
            and s10.coverage([p], s10.load_measured_sources())[p.key] == "page_only"
        ):
            gates["proposed_note_sources"][f"{p.page}|{s10.normalize_text(p.quote)}"] = {
                "title": "SYNTHETIC TITLE (test only)",
                "url": s10.REPORT_URL,
                "page": str(p.page),
                "quote": p.quote,
                "retrieved": "2026-11-14",
                "archive_id": s10.ARCHIVE_ID,
            }
    return gates


def csv_rows_text():
    return (ROOT / CSV_REL).read_text(encoding="utf-8")


def flags_text():
    return (ROOT / FLAGS_REL).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def real():
    return dv.derive(ROOT)


@pytest.fixture(scope="module")
def complete(tmp_path_factory):
    return dv.derive(make_root(tmp_path_factory.mktemp("complete"), gates=complete_gates()))


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


def test_the_real_run_stages_22_and_withholds_18_because_two_titles_need_a_person(real):
    assert len(real["findings"]) == 22
    assert len(real["withheld"]) == 18
    assert {w["reason"] for w in real["withheld"]} == {
        "a required note has no verifiable source passage"
    }
    assert sorted(p["page"] for p in real["note_sources"]["unproposable"]) == [16, 17]
    staged = {f["id"] for f in real["findings"]}
    assert not staged & {w["id"] for w in real["withheld"]}, (
        "no Finding is both emitted and withheld"
    )
    assert len(staged) + len(real["withheld"]) == 40


def test_a_withheld_finding_is_never_emitted_without_the_note_it_needs(real):
    flags_by_id = {f["flag_id"]: f for f in s10.load_flags()}
    for w in real["withheld"]:
        assert w["flags"], "a withheld Finding names the flags that block it"
        for fid in w["flags"]:
            page = int(flags_by_id[fid]["source_printed_page"])
            assert page in (16, 17)


def test_nothing_is_registrable_today(real):
    assert dv.registrable(real["gates"]) is False
    assert {g["status"] for g in real["gates"]["gates"]} == {"open"}
    assert {c["status"] for c in real["gates"]["conditions"].values()} == {"unapproved"}


def test_every_note_source_is_registered_or_a_labelled_proposal(real):
    counts = real["note_sources"]
    assert counts["registered"] > 0 and counts["proposed_unregistered"] > 0
    assert len(counts["proposed"]) == 12


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


def test_flex_010_burning_rate_is_excluded_and_the_derivation_never_states_its_number(
    complete, tmp_path
):
    f = by_id(complete["findings"])["flex.flex-010.burning_rate_constant"]
    assert f["value"] is None and f["value_status"] == "excluded"
    kinds = {n["flag_ref"]["flag_id"]: n["kind"] for n in f["curation_notes"]}
    assert kinds["F042"] == "exclusion" and kinds["F041"] == "caution"
    # everything the derivation itself writes, except the curator's note text (see the xfail below)
    root = make_root(tmp_path, gates=complete_gates())
    dv.stage(tmp_path / "out", root)
    own = {k: v for k, v in f.items() if k != "curation_notes"}
    assert not PRINTED_VALUE.search(json.dumps(own)), "the excluded value leaked into the Finding"
    assert not PRINTED_VALUE.search(
        json.dumps([n for n in f["curation_notes"] if n["flag_ref"]["flag_id"] != "F042"])
    )
    report = (tmp_path / "out" / "STAGING_REPORT.json").read_text(encoding="utf-8")
    assert not PRINTED_VALUE.search(report)
    others = [x for x in complete["findings"] if x["id"] != f["id"]]
    assert not PRINTED_VALUE.search(json.dumps(others)), "no other Finding states it either"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN CONFLICT, needs a decision: the reviewed F042 flag reason itself prints '.37'. The "
        "exclusion note copies the reason (S10), S9 then requires dependents and TARS answers to "
        "quote the exact exclusion note, and S9 also forbids stating the excluded value. The flags "
        "file is Member 3's; this derivation does not rewrite it."
    ),
)
def test_the_exclusion_note_text_does_not_state_the_excluded_value(complete):
    f = by_id(complete["findings"])["flex.flex-010.burning_rate_constant"]
    note = next(n for n in f["curation_notes"] if n["flag_ref"]["flag_id"] == "F042")
    assert not PRINTED_VALUE.search(note["note"])


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
    kinds = {"caution": "caution", "exclude": "exclusion"}
    for f in complete["findings"]:
        for n in f.get("curation_notes", []):
            fl = by_flag[n["flag_ref"]["flag_id"]]
            assert n["flag_ref"]["manifest_id"] == dv.FLAGS_ID
            assert fl["flex_test"] == f["test_id"]
            assert n["kind"] == kinds[fl["ranking_use"]] and n["generated_by"] == "FlameGuard-SI"
            assert n["note"] == fl["reason"]
            assert (
                n["source"]["quote"] == fl["source_quote"]
                and str(n["source"]["page"]) == fl["source_printed_page"]
            )


def test_every_note_quote_is_on_a_known_page_and_proposed_sources_come_only_from_the_gates_file(
    real,
):
    gate_quotes = {(s["page"], s["quote"]) for s in real["gates"]["proposed_note_sources"].values()}
    registered = {(str(s["page"]), s.get("quote")) for s in s10.load_measured_sources()}
    for f in real["findings"]:
        for n in f.get("curation_notes", []):
            src = n["source"]
            ok = (str(src["page"]), src["quote"]) in gate_quotes or any(
                p == str(src["page"])
                and q
                and s10.normalize_text(src["quote"]) in s10.normalize_text(q)
                for p, q in registered
            )
            assert ok, f"{f['id']}: {n['flag_ref']['flag_id']} rests on an unknown source"


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
    gates = complete_gates()
    for g in gates["gates"]:
        g["status"] = "closed"
    for c in gates["conditions"].values():
        c["status"] = "approved"
    report = dv.stage(tmp_path / "out", make_root(tmp_path, gates=gates))
    assert report["note_sources"]["proposed_unregistered"] > 0
    assert report["registrable"] is False, "unregistered note sources still block registration"


def test_removing_the_proposed_sources_withholds_more_never_invents(tmp_path):
    gates = real_gates()
    gates["proposed_note_sources"] = {}
    result = dv.derive(make_root(tmp_path, gates=gates))
    assert len(result["findings"]) < 22 and len(result["findings"]) + len(result["withheld"]) == 40
    for f in result["findings"]:
        for n in f.get("curation_notes", []):
            assert n["source"]["title"] != "" and n["source"]["page"]
            assert not n["source"]["title"].startswith("SYNTHETIC")


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
# The proposed sources match the PDF (local only)
# ---------------------------------------------------------------------------------------------


def test_pdf_the_gates_file_proposals_are_exactly_what_the_pdf_supports():
    if not s10.DEFAULT_PDF.is_file():
        pytest.skip("NOT VERIFIED: data/raw/NASA-TP-2015-216046_FLEX.pdf is not present")
    pymupdf = pytest.importorskip("pymupdf", reason="NOT VERIFIED: PyMuPDF is not installed")
    doc = pymupdf.open(s10.DEFAULT_PDF)

    def page_text(printed):
        return doc[printed + s10.PRINTED_TO_PDF_PAGE_OFFSET - 1].get_text()

    found = s10.passages(s10.load_flags())
    sources = s10.load_measured_sources()
    props, _ = s10.propose_sources(
        found, s10.coverage(found, sources), page_text, s10._numeric_retrieved(sources)
    )
    expected = {f"{p['page']}|{s10.normalize_text(p['quote'])}": p for p in props}
    assert real_gates()["proposed_note_sources"] == expected


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
        table = [s for s in entry["sources"] if str(s["page"]) == "20"][0]
        entry["sources"] = [s for s in entry["sources"] if s is not table]
        if edit == "duplicate":
            entry["sources"] += [table, copy.deepcopy(table)]
        write_json(root / "data/manifest.json", manifest)
        with pytest.raises(dv.DerivationError, match="exactly one numeric"):
            dv.derive(root)
