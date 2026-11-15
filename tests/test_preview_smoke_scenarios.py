"""The preview smoke suite's evidence scenarios (preview/evidence_expect.py).

Empty and registered evidence are both supported, chosen from the tree unless forced, and a
mismatch is always a failure. SYNTHETIC trees only; nothing here is NASA data.
"""

# ruff: noqa: E501  (inline synthetic config.js reads better unwrapped)
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "evidence_expect", ROOT / "preview" / "evidence_expect.py"
)
ee = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = ee
_spec.loader.exec_module(ee)

CSV_REL = "data/curated/table.csv"


def finding(fid, test, status, line, field="k"):
    return {
        "id": fid,
        "investigation_id": "inv",
        "evidence_class": "measured",
        "value": None if status != "reported" else 1.0,
        "value_status": status,
        "test_id": test,
        "test_outcome": "Extinction",
        "provenance": {"locator": f"SYNTHETIC table, field {field}, CSV line {line}"},
    }


def write_tree(tmp_path, findings=None, investigations=None, csv_text="k\n.37\n0.5\n"):
    tree = tmp_path / "tree"
    (tree / "data" / "curated" / "findings").mkdir(parents=True)
    (tree / CSV_REL).write_text(csv_text, encoding="utf-8")
    datasets = [{"id": "src", "path": CSV_REL}]
    if findings is not None:
        text = json.dumps(findings)
        (tree / "data/curated/findings/inv.json").write_text(text, encoding="utf-8")
        datasets.append({"id": "f", "path": "data/curated/findings/inv.json"})
    if investigations is not None:
        text = json.dumps(investigations)
        (tree / "data/curated/investigations.json").write_text(text, encoding="utf-8")
        datasets.append({"id": "i", "path": "data/curated/investigations.json"})
    manifest = json.dumps({"datasets": datasets})
    (tree / "data" / "manifest.json").write_text(manifest, encoding="utf-8")
    return tree


def flex_like():
    rows = []
    for t in range(1, 3):
        for q in range(4):
            status = "excluded" if (t, q) == (2, 1) else "not_reported" if q == 3 else "reported"
            rows.append(finding(f"f{t}{q}", f"T-{t}", status, 2))
    return rows


def test_an_empty_tree_is_the_empty_scenario(tmp_path):
    tree = write_tree(tmp_path)
    assert ee.decide("auto", tree, api_total=99)[0] == "empty", "the tree wins over the API"
    summary = ee.registered_summary(tree)
    assert summary["findings"] == 0 and summary["groups"] == 0 and summary["excluded"] == []


def test_a_registered_tree_is_summarised_exactly(tmp_path):
    tree = write_tree(tmp_path, flex_like(), [{"id": "inv"}])
    scenario, s = ee.decide("auto", tree, None)
    assert scenario == "registered"
    assert s["findings"] == 8 and s["investigations"] == 1 and s["groups"] == 2
    assert s["by_status"] == {"reported": 5, "not_reported": 2, "excluded": 1}
    assert s["outcomes"] == ["Extinction"]
    assert s["excluded"] == [{"id": "f21", "printed": ".37", "value": None}]


def test_without_a_tree_the_api_decides_and_expect_overrides(tmp_path):
    assert ee.decide("auto", None, 0) == ("empty", None)
    assert ee.decide("auto", None, 40) == ("registered", None)
    tree = write_tree(tmp_path)
    assert ee.decide("registered", tree, 0)[0] == "registered", "a forced scenario is kept"
    with pytest.raises(ValueError):
        ee.decide("maybe", None, 0)


def test_small_investigations_are_not_grouped_and_rows_fall_back_to_locators(tmp_path):
    rows = flex_like()[:5]
    assert ee.registered_summary(write_tree(tmp_path, rows, [{"id": "inv"}]))["groups"] == 0
    many = [dict(f, test_id=None) for f in flex_like()]
    for i, f in enumerate(many):
        f["provenance"] = {"locator": f"SYNTHETIC row {i}"}
    other = tmp_path / "b"
    other.mkdir()
    assert ee.registered_summary(write_tree(other, many, [{"id": "inv"}]))["groups"] == 8


def observed(
    total=0, items=None, by_status=None, excluded=None, header=None, inv_total=0, ids=None
):
    items = items or []
    return {
        "investigations": {"total": inv_total, "items": [{}] * inv_total},
        "findings": {"total": total, "items": items},
        "ids": ids or [],
        "by_status": by_status or {},
        "excluded_values": excluded or [],
        "rejected_header": header,
    }


def test_empty_verdicts_pass_only_when_nothing_is_served():
    assert all(ok for ok, _, _ in ee.api_verdicts("empty", None, observed()))
    assert not all(
        ok
        for ok, _, _ in ee.api_verdicts(
            "empty", None, observed(total=40, items=[{}] * 40, inv_total=1)
        )
    )


def test_registered_verdicts_check_counts_ids_statuses_header_and_excluded_values(tmp_path):
    summary = ee.registered_summary(write_tree(tmp_path, flex_like(), [{"id": "inv"}]))
    good = observed(8, [{}] * 8, summary["by_status"], [None], None, 1, summary["ids"])
    assert all(ok for ok, _, _ in ee.api_verdicts("registered", summary, good))
    cases = {
        "empty served": observed(),
        "a finding missing": observed(
            7, [{}] * 7, summary["by_status"], [None], None, 1, summary["ids"][:-1]
        ),
        "a different finding with the same count": observed(
            8,
            [{}] * 8,
            summary["by_status"],
            [None],
            None,
            1,
            [*summary["ids"][:-1], "staged.lookalike"],
        ),
        "excluded value leaked": observed(
            8, [{}] * 8, summary["by_status"], [0.37], None, 1, summary["ids"]
        ),
        "a file rejected": observed(
            8, [{}] * 8, summary["by_status"], [None], "1", 1, summary["ids"]
        ),
        "statuses differ": observed(
            8, [{}] * 8, {"reported": 6, "not_reported": 2}, [None], None, 1, summary["ids"]
        ),
    }
    for name, obs in cases.items():
        assert not all(ok for ok, _, _ in ee.api_verdicts("registered", summary, obs)), name


def test_the_printed_value_is_found_only_through_a_parsable_locator(tmp_path):
    tree = write_tree(tmp_path, flex_like(), [{"id": "inv"}])
    assert ee.printed_value(tree, finding("x", "T", "excluded", 3)) == "0.5"
    assert ee.printed_value(tree, {"provenance": {"locator": "no field here"}}) is None
    assert ee.printed_value(tree, finding("x", "T", "excluded", 99)) is None


def test_footer_expectation_reads_the_frontends_declared_and_supported_versions(tmp_path):
    js = tmp_path / "frontend" / "static" / "js"
    js.mkdir(parents=True)
    (js / "config.js").write_text('export const CONTRACT_VERSION = "0.2.0";\n', encoding="utf-8")
    assert ee.footer_expectation(tmp_path) == {"declared": "0.2.0", "supported": ["0.2.0"]}
    (js / "config.js").write_text(
        'export const CONTRACT_VERSION = "0.2.2";\nexport const SUPPORTED_CONTRACT_VERSIONS = Object.freeze(["0.2.0", "0.2.1", "0.2.2"]);\n',
        encoding="utf-8",
    )
    assert ee.footer_expectation(tmp_path)["supported"] == ["0.2.0", "0.2.1", "0.2.2"]
    assert ee.footer_expectation(None) == {"declared": None, "supported": None}


def test_the_demo_contract_carries_both_live_scenarios():
    contract = json.loads((ROOT / "preview" / "demo_contract.json").read_text(encoding="utf-8"))
    assert contract["ui"]["live"]["#/explorer"] == ["No investigations available"]
    assert "Test end as printed" in contract["ui"]["live_registered"]["#/explorer"]
    assert (
        contract["ui"]["live"]["#/rank"] == contract["ui"]["live_registered"]["#/rank"] == ["501"]
    )
