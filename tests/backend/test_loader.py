"""B1 evidence loader: each rule is tested by breaking exactly that rule in a synthetic repository.

All data is SYNTHETIC (see conftest.py). Every rejection must be fail-closed: nothing from a
rejected file may reach the store, even when the file also holds valid findings.
"""

import json
from pathlib import Path

import pytest

from conftest import (
    REASON,
    SOURCE,
    explanation,
    interpretation,
    investigation,
    measured,
)
from flameguard.data import Role, Status, load_evidence

REPO = Path(__file__).resolve().parents[2]
SIM_LABEL = "Fluid and thermal transport model. No combustion chemistry."


def load(scenario):
    return load_evidence(scenario.write())


def reasons(result, entry_id):
    return " | ".join(result.report.entry(entry_id).reasons)


def assert_clean(result):
    assert result.report.manifest_ok
    assert [e.id for e in result.report.rejected] == []


# --- Happy path and the report ---


def test_valid_repository_loads_everything(scenario):
    r = load(scenario)
    assert_clean(r)
    assert {e.id: e.status for e in r.report.entries} == {
        "ds-inv": Status.ACCEPTED,
        "ds-a": Status.ACCEPTED,
        "ds-notes": Status.ACCEPTED,
    }
    assert [i["id"] for i in r.store.investigations] == ["inv-a"]
    assert set(r.store.findings) == {"m1", "ex1", "i1", "e1"}
    assert r.report.entry("ds-a").loaded == 2 and r.report.entry("ds-a").role is Role.FINDINGS
    assert r.report.warnings == ()


def test_excluded_and_exclusion_dependent_ids_are_exposed(scenario):
    r = load(scenario)
    assert r.store.excluded == {"ex1"}
    assert r.store.exclusion_dependent == {"ex1", "e1"}  # i1 depends only on the reported m1


def test_store_is_read_only(scenario):
    r = load(scenario)
    with pytest.raises(TypeError):
        r.store.findings["x"] = {}
    with pytest.raises(AttributeError):
        r.report.manifest_ok = False


def test_report_is_deterministic(scenario):
    a = load_evidence(scenario.write())
    assert a == load_evidence(scenario.root)


def test_real_repository_without_data_loads_nothing():
    r = load_evidence(REPO)
    assert r.report.manifest_ok and r.report.entries == ()
    assert r.store.investigations == () and len(r.store.findings) == 0


# --- 1. Manifest: strict JSON and schema; failure loads nothing ---


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_manifest_rejects_nan_and_infinity(scenario, bad):
    scenario.raw["data/manifest.json"] = (
        f'{{"manifest_version": "0.2.0", "datasets": [], "x": {bad}}}'
    )
    r = load(scenario)
    assert not r.report.manifest_ok and "non-standard JSON number" in r.report.manifest_errors[0]
    assert len(r.store.findings) == 0 and r.report.entries == ()


def test_manifest_missing_loads_nothing(scenario):
    root = scenario.write()
    (root / "data" / "manifest.json").unlink()
    r = load_evidence(root)
    assert not r.report.manifest_ok and len(r.store.findings) == 0


def test_manifest_schema_violation_loads_nothing(scenario):
    scenario.raw["data/manifest.json"] = json.dumps(
        {"manifest_version": "0.2.0", "datasets": [{"id": "x"}]}
    )
    r = load(scenario)
    assert not r.report.manifest_ok and r.report.manifest_errors[0].startswith("schema: manifest")
    assert len(r.store.findings) == 0


def test_missing_provenance_checker_fails_closed(scenario):
    root = scenario.write()
    (root / "tools" / "check_data_provenance.py").unlink()
    r = load_evidence(root)
    assert (
        not r.report.manifest_ok and "provenance checker not found" in r.report.manifest_errors[0]
    )


# --- 2. Provenance (the tools/ checker is the only implementation) ---


def test_sha256_mismatch_rejects_only_that_entry(scenario):
    scenario.tamper["ds-notes"] = "0" * 64
    r = load(scenario)
    assert r.report.entry("ds-notes").status is Status.REJECTED
    assert "sha256 mismatch" in reasons(r, "ds-notes")
    assert r.report.entry("ds-a").status is Status.ACCEPTED
    assert {"i1", "e1"}.isdisjoint(r.store.findings) and "m1" in r.store.findings


def test_nan_in_a_registered_findings_file_is_rejected(scenario):
    scenario.raw["data/curated/findings/inv-a.json"] = '[{"value": NaN}]'
    r = load(scenario)
    assert "non-standard JSON number" in reasons(r, "ds-a")
    assert {"m1", "ex1"}.isdisjoint(r.store.findings)


def test_missing_file_is_rejected(scenario):
    root = scenario.write()
    (root / "data/curated/interpretations/notes.json").unlink()
    r = load_evidence(root)
    assert "file not found" in reasons(r, "ds-notes")


def test_measured_entry_without_sources_fails_the_manifest_closed(scenario):
    scenario.extra_entries.append(
        {
            "id": "ds-bad",
            "path": "data/curated/findings/inv-z.json",
            "evidence_class": "measured",
            "text": "[]",
            "rights_status": "under_review",
        }
    )
    r = load(scenario)
    assert not r.report.manifest_ok and "schema: manifest" in r.report.manifest_errors[0]
    assert len(r.store.findings) == 0 and r.report.entries == ()


def test_loader_parses_strictly_even_if_the_provenance_layer_is_bypassed(scenario):
    """Defence in depth: the loader's own parse rejects NaN when the checker approves everything."""
    scenario.raw["data/curated/findings/inv-a.json"] = '[{"value": NaN}]'
    root = scenario.write()
    tool = root / "tools" / "check_data_provenance.py"
    tool.write_text(
        tool.read_text(encoding="utf-8")
        + "\n\ndef check_manifest(manifest, root=ROOT):\n    return []\n",
        encoding="utf-8",
    )
    r = load_evidence(root)
    assert "non-standard JSON number" in reasons(r, "ds-a") and "m1" not in r.store.findings


# --- 3. Per-file: schema, fixture flag, S1, S2 ---


def test_one_invalid_finding_rejects_the_whole_file(scenario):
    bad = measured("m2", "inv-a", "ds-a")
    bad["value"] = "not a number"
    scenario.findings["inv-a"].append(bad)
    r = load(scenario)
    assert r.report.entry("ds-a").status is Status.REJECTED and "schema:" in reasons(r, "ds-a")
    assert {"m1", "ex1", "m2"}.isdisjoint(r.store.findings)  # valid siblings are not loaded either


def test_non_array_document_is_rejected(scenario):
    scenario.raw["data/curated/findings/inv-a.json"] = json.dumps({"not": "an array"})
    assert "must be an array" in reasons(load(scenario), "ds-a")


def test_fixture_flag_is_rejected(scenario):
    scenario.findings["inv-a"][0]["fixture"] = True
    r = load(scenario)
    assert "fixtures never belong" in reasons(r, "ds-a") and "m1" not in r.store.findings


def test_unknown_key_in_a_finding_is_rejected(scenario):
    scenario.findings["inv-a"][0]["score"] = 0.9
    assert "schema:" in reasons(load(scenario), "ds-a")


def test_s1_manifest_id_not_in_manifest(scenario):
    scenario.findings["inv-a"][0]["provenance"]["manifest_id"] = "ds-nowhere"
    text = reasons(load(scenario), "ds-a")
    assert "S1" in text and "not in the manifest" in text


def test_s1_manifest_id_names_an_interpretation_entry(scenario):
    scenario.findings["inv-a"][0]["provenance"]["manifest_id"] = "ds-notes"
    assert "not a measured entry" in reasons(load(scenario), "ds-a")


def test_s1_manifest_id_names_another_measured_file(scenario):
    scenario.findings["inv-a"][0]["provenance"]["manifest_id"] = "ds-inv"
    assert "whose file does not hold it" in reasons(load(scenario), "ds-a")


def test_s2_finding_of_another_investigation_in_the_file(scenario):
    scenario.findings["inv-a"].append(measured("m9", "inv-b", "ds-a"))
    r = load(scenario)
    assert (
        "S2" in reasons(r, "ds-a") and "m9" not in r.store.findings and "m1" not in r.store.findings
    )


def test_interpretation_class_in_a_findings_file_is_rejected(scenario):
    scenario.findings["inv-a"].append(interpretation("i9", "inv-a", ["m1"]))
    text = reasons(load(scenario), "ds-a")
    assert "layout" in text or "provenance" in text


def test_duplicate_investigation_ids_reject_the_file(scenario):
    scenario.investigations.append(investigation("inv-a", []))
    r = load(scenario)
    assert "defined more than once" in reasons(r, "ds-inv") and r.store.investigations == ()


# --- 4a. Duplicate finding ids across files ---


def test_duplicate_finding_id_across_files_rejects_both(scenario):
    scenario.findings["inv-b"] = [measured("m1", "inv-b", "ds-b")]
    r = load(scenario)
    assert "defined more than once" in reasons(r, "ds-a") and "defined more than once" in reasons(
        r, "ds-b"
    )
    assert "m1" not in r.store.findings


def test_duplicate_finding_id_within_one_file_is_rejected(scenario):
    scenario.findings["inv-a"].append(measured("m1", "inv-a", "ds-a"))
    assert "defined more than once" in reasons(load(scenario), "ds-a")


# --- 4b. S3: derived_from resolves, no cycles, failures cascade ---


def test_s3_unresolved_derived_from(scenario):
    scenario.interps["notes"].append(interpretation("i2", "inv-a", ["ghost"]))
    r = load(scenario)
    assert "S3" in reasons(r, "ds-notes") and "does not resolve" in reasons(r, "ds-notes")
    assert {"i1", "e1", "i2"}.isdisjoint(
        r.store.findings
    )  # i1 and e1 were valid but share the file


def test_s3_cycle_is_rejected_not_looped(scenario):
    scenario.interps["notes"] = [
        interpretation("c1", "inv-a", ["c2"]),
        interpretation("c2", "inv-a", ["c1"]),
    ]
    r = load(scenario)
    assert "cycle" in reasons(r, "ds-notes") and {"c1", "c2"}.isdisjoint(r.store.findings)


def test_s3_self_cycle(scenario):
    scenario.interps["notes"] = [interpretation("c1", "inv-a", ["c1"])]
    assert "cycle" in reasons(load(scenario), "ds-notes")


def test_s3_cross_file_chain_resolves(scenario):
    scenario.interps["more"] = [interpretation("i2", "inv-a", ["i1"])]
    r = load(scenario)
    assert_clean(r) and "i2" in r.store.findings


def test_s3_rejected_parent_file_cascades_to_dependents(scenario):
    scenario.interps["more"] = [interpretation("i2", "inv-a", ["i1"])]
    scenario.interps["notes"].append(interpretation("bad", "inv-a", ["ghost"]))
    r = load(scenario)
    assert r.report.entry("ds-notes").status is Status.REJECTED
    assert r.report.entry("ds-more").status is Status.REJECTED and "does not resolve" in reasons(
        r, "ds-more"
    )
    assert "i2" not in r.store.findings


def test_derived_from_may_name_a_measured_finding_in_another_investigation(scenario):
    scenario.findings["inv-b"] = [measured("m2", "inv-b", "ds-b")]
    scenario.investigations.append(investigation("inv-b", ["ds-b"]))
    scenario.interps["notes"].append(interpretation("i3", "inv-a", ["m1", "m2"]))
    assert_clean(load(scenario))


# --- 4c. Transitive S9 ---


def test_s9_explanation_depth_three_is_dependent_and_allowed(scenario):
    scenario.interps["notes"] += [
        explanation("e2", "inv-a", ["e1"]),
        explanation("e3", "inv-a", ["e2"]),
    ]
    r = load(scenario)
    assert_clean(r)
    assert r.store.exclusion_dependent == {"ex1", "e1", "e2", "e3"}


def test_s9_mixed_parents_are_dependent(scenario):
    scenario.interps["notes"].append(explanation("e2", "inv-a", ["m1", "ex1"]))
    assert "e2" in load(scenario).store.exclusion_dependent


@pytest.mark.parametrize(
    ("extra", "fragment"),
    [
        (
            {
                "value": 0.5,
                "quantity": "flame_spread_rate",
                "unit": "mm/s",
                "value_status": "reported",
            },
            "value or quantity",
        ),
        ({"relevant_environments": ["lunar_base"]}, "tagged for an environment"),
        ({"limitations": ["Explains why a value was excluded."]}, "quote the exclusion note"),
        (
            {"limitations": ["Not exclusive to droplets; excluding outliers."]},
            "quote the exclusion note",
        ),
    ],
    ids=["value", "moon-mars-tag", "generic-limitation", "keyword-only-limitation"],
)
def test_s9_misused_dependent_interpretation_rejects_its_file(scenario, extra, fragment):
    scenario.interps["notes"].append(explanation("bad", "inv-a", ["ex1"], **extra))
    r = load(scenario)
    assert "S9" in reasons(r, "ds-notes") and fragment in reasons(r, "ds-notes")
    assert {"bad", "i1", "e1"}.isdisjoint(r.store.findings)


def test_s9_indirect_misuse_is_caught_through_the_chain(scenario):
    scenario.interps["notes"] += [
        explanation("e2", "inv-a", ["e1"]),
        explanation("e3", "inv-a", ["e2"], relevant_environments=["martian_base"]),
    ]
    assert "e3: S9" in reasons(load(scenario), "ds-notes")


def test_s9_clean_chain_is_not_dependent(scenario):
    scenario.interps["notes"].append(interpretation("i4", "inv-a", ["i1"]))
    r = load(scenario)
    assert "i4" in r.store.findings and "i4" not in r.store.exclusion_dependent


def test_s9_exclusion_note_text_must_come_from_an_ancestor(scenario):
    scenario.interps["notes"][1]["limitations"] = ["Explains the exclusion: some other text."]
    assert "quote the exclusion note" in reasons(load(scenario), "ds-notes")
    assert REASON not in "some other text."


# --- 5. S4 ---


def test_s4_unresolved_dataset(scenario):
    scenario.investigations[0]["datasets"] = ["ds-ghost"]
    r = load(scenario)
    assert "S4" in reasons(r, "ds-inv") and r.store.investigations == ()
    assert "m1" in r.store.findings  # findings are independent of the investigations file


def test_s4_dataset_must_be_measured(scenario):
    scenario.investigations[0]["datasets"] = ["ds-notes"]
    assert "not a measured entry" in reasons(load(scenario), "ds-inv")


def test_s4_rejected_dataset_warns_but_keeps_the_investigation(scenario):
    scenario.tamper["ds-a"] = "f" * 64
    r = load(scenario)
    assert r.report.entry("ds-a").status is Status.REJECTED
    assert [i["id"] for i in r.store.investigations] == ["inv-a"]
    assert any("was rejected; no evidence loaded" in w for w in r.report.warnings)


def test_finding_of_an_unloaded_investigation_warns(scenario):
    scenario.investigations = [investigation("inv-z", [])]
    assert any("is not loaded" in w for w in load(scenario).report.warnings)


# --- Layout and simulation isolation ---


def test_csv_sources_and_quality_files_are_skipped_not_parsed(scenario):
    scenario.extra_entries += [
        {
            "id": "src-csv",
            "path": "data/curated/flex_table.csv",
            "evidence_class": "measured",
            "text": "a,b\n1,NaN\n",
            "sources": [SOURCE],
            "rights_status": "under_review",
        },
        {
            "id": "flags",
            "path": "data/curated/interpretations/quality/flags.csv",
            "evidence_class": "interpretation",
            "text": "x\n",
            "derived_from": ["src-csv"],
            "method": "m",
        },
    ]
    r = load(scenario)
    assert (
        r.report.entry("src-csv").status is Status.SKIPPED
        and r.report.entry("flags").status is Status.SKIPPED
    )
    assert r.report.entry("src-csv").role is Role.SOURCE
    assert_clean(r)


def test_json_at_an_unrecognized_path_is_rejected(scenario):
    scenario.extra_entries.append(
        {
            "id": "odd",
            "path": "data/curated/misc/x.json",
            "evidence_class": "measured",
            "text": "[]",
            "sources": [SOURCE],
            "rights_status": "under_review",
        }
    )
    assert "not a recognized evidence document" in reasons(load(scenario), "odd")


def test_simulation_entries_are_skipped_and_never_opened(scenario):
    # A directory where the file should be: opening it would raise, so a pass proves
    # the loader never read it.
    scenario.extra_entries.append(
        {
            "id": "sim",
            "path": "data/simulated/run.json",
            "evidence_class": "illustrative_simulation",
            "text": "{}",
            "model": "m",
            "model_version": "0",
            "label": SIM_LABEL,
        }
    )
    root = scenario.write()
    sim = root / "data/simulated/run.json"
    sim.unlink()
    sim.mkdir()
    r = load_evidence(root)
    assert (
        r.report.entry("sim").status is Status.SKIPPED
        and r.report.entry("sim").role is Role.SIMULATION
    )
    assert "never evidence" in reasons(r, "sim")
    assert_clean(r)


def test_simulation_content_never_enters_the_store(scenario):
    finding_like = measured("sim-m1", "inv-a", "ds-a")
    scenario.extra_entries.append(
        {
            "id": "sim",
            "path": "data/simulated/findings.json",
            "evidence_class": "illustrative_simulation",
            "text": json.dumps([finding_like]),
            "model": "m",
            "model_version": "0",
            "label": SIM_LABEL,
        }
    )
    assert "sim-m1" not in load(scenario).store.findings


def test_simulation_with_a_wrong_hash_does_not_disturb_the_evidence(scenario):
    scenario.extra_entries.append(
        {
            "id": "sim",
            "path": "data/simulated/a.json",
            "evidence_class": "illustrative_simulation",
            "text": "{}",
            "model": "m",
            "model_version": "0",
            "label": SIM_LABEL,
        }
    )
    scenario.tamper["sim"] = "0" * 64
    r = load(scenario)
    assert_clean(r) and r.report.entry("sim").status is Status.SKIPPED


def test_loader_package_imports_no_simulation_research_preview_or_api_code():
    import re

    for path in (REPO / "backend" / "flameguard" / "data").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(
            r"^\s*(from|import)\s+\S*(simulat|research|preview|server|api)", text, re.M
        ), path


def test_nothing_imports_the_loader_from_simulation_code():
    for path in (REPO / "backend").rglob("*.py"):
        if "simulat" in str(path).lower():
            assert "flameguard.data" not in path.read_text(encoding="utf-8"), path


def test_existing_endpoints_are_unchanged_by_the_loader():
    from fastapi.testclient import TestClient

    from flameguard.api.app import app

    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    for path in ("/api/investigations", "/api/findings", "/api/rankings", "/api/compare"):
        assert client.get(path).status_code == 501
