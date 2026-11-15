"""What the preview smoke suite expects from the live evidence: nothing, or what is registered.

The smoke suite supports two scenarios without being edited:
- **empty**: the approved state today. The live API and dashboard must be honestly empty.
- **registered**: the tree registers Findings in data/manifest.json. The live API and dashboard must
  show exactly those (counts, statuses, test rows), withhold every excluded value and never show
  fixture data.

`decide` picks the scenario from the exported tree (or the API) unless `--expect` forces one, so a
mismatch (for example an empty tree that serves Findings, or the reverse) is a failure, never a
silent pass. Nothing here registers anything or reads fixtures: it only reads what the manifest
already registers. Pure functions, tested in tests/test_preview_smoke_scenarios.py.
"""

# ruff: noqa: E501  (verdict messages read better unwrapped)
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

EXPECTATIONS = ("auto", "empty", "registered")
FINDING_DIRS = ("data/curated/findings/", "data/curated/interpretations/")
INVESTIGATIONS_PATH = "data/curated/investigations.json"
GROUPING_THRESHOLD = 6  # the dashboard groups an investigation's measured findings above this


def registered_documents(tree: Path) -> tuple[list[dict], list[dict]]:
    """(Findings, investigations) inside the JSON files the manifest registers."""
    manifest = json.loads((tree / "data" / "manifest.json").read_text(encoding="utf-8"))
    findings: list[dict] = []
    investigations: list[dict] = []
    for entry in manifest.get("datasets", []):
        path = entry["path"]
        if not path.endswith(".json"):
            continue  # registered source and quality files are not Finding JSON
        items = json.loads((tree / path).read_text(encoding="utf-8"))
        if path == INVESTIGATIONS_PATH:
            investigations += items
        elif path.startswith(FINDING_DIRS):
            findings += items
    return findings, investigations


def printed_value(tree: Path, finding: dict) -> str | None:
    """The number printed in the registered source CSV for a finding, via its locator, or None."""
    m = re.search(r"field (\w+), CSV line (\d+)", finding.get("provenance", {}).get("locator", ""))
    if not m:
        return None
    field, line = m.group(1), int(m.group(2))
    for entry in json.loads((tree / "data" / "manifest.json").read_text(encoding="utf-8"))[
        "datasets"
    ]:
        if entry["path"].endswith(".csv") and "/quality/" not in entry["path"]:
            rows = list(
                csv.DictReader((tree / entry["path"]).read_text(encoding="utf-8").splitlines())
            )
            if 0 <= line - 2 < len(rows) and field in rows[line - 2]:
                return rows[line - 2][field] or None
    return None


def registered_summary(tree: Path) -> dict:
    findings, investigations = registered_documents(tree)
    measured = [f for f in findings if f.get("evidence_class") == "measured"]
    groups = 0
    for inv in investigations:
        rows = [f for f in measured if f["investigation_id"] == inv["id"]]
        if len(rows) > GROUPING_THRESHOLD:
            groups += len({f.get("test_id") or f["provenance"]["locator"] for f in rows})
    by_status: dict[str, int] = {}
    for f in measured:
        by_status[f["value_status"]] = by_status.get(f["value_status"], 0) + 1
    return {
        "investigations": len(investigations),
        "findings": len(findings),
        "measured": len(measured),
        "by_status": by_status,
        "groups": groups,
        "ids": sorted(f["id"] for f in findings),
        "outcomes": sorted({f["test_outcome"] for f in measured if f.get("test_outcome")}),
        "excluded": [
            {"id": f["id"], "printed": printed_value(tree, f), "value": f.get("value")}
            for f in measured
            if f["value_status"] == "excluded"
        ],
    }


def decide(expect: str, tree: Path | None, api_total: int | None) -> tuple[str, dict | None]:
    """(scenario, summary). `summary` comes from the tree when there is one, else None."""
    if expect not in EXPECTATIONS:
        raise ValueError(f"--expect must be one of {EXPECTATIONS}")
    summary = registered_summary(tree) if tree is not None else None
    if expect != "auto":
        return expect, summary
    if summary is not None:
        return (
            "registered" if summary["findings"] or summary["investigations"] else "empty"
        ), summary
    return ("registered" if (api_total or 0) > 0 else "empty"), None


def api_verdicts(expect: str, summary: dict | None, observed: dict) -> list[tuple[bool, str, str]]:
    """Pass/fail verdicts for the live API lists. `observed`: totals, ids, by_status, rejected header."""
    out = []
    if expect == "empty":
        for what in ("investigations", "findings"):
            ok = observed[what]["total"] == 0 and observed[what]["items"] == []
            out.append(
                (
                    ok,
                    f"live: no registered evidence -> honest empty {what[:-1] if what == 'findings' else 'investigation'} list",
                    f"total={observed[what]['total']}",
                )
            )
        return out
    out.append(
        (
            observed["findings"]["total"] > 0,
            "live: registered evidence is served (not empty)",
            f"total={observed['findings']['total']}",
        )
    )
    out.append(
        (
            observed["rejected_header"] in (None, "0"),
            "live: nothing is silently withheld (no rejected-files header)",
            str(observed["rejected_header"]),
        )
    )
    out.append(
        (
            all(v is None for v in observed["excluded_values"]),
            "live: every excluded value is null in the API",
            str(observed["excluded_values"]),
        )
    )
    if summary is not None:
        out.append(
            (
                observed["investigations"]["total"] == summary["investigations"],
                "live: investigation count equals the registered count",
                f"{observed['investigations']['total']} vs {summary['investigations']}",
            )
        )
        out.append(
            (
                observed["findings"]["total"] == summary["findings"],
                "live: finding count equals the registered count",
                f"{observed['findings']['total']} vs {summary['findings']}",
            )
        )
        out.append(
            (
                sorted(observed["ids"]) == summary["ids"],
                "live: exactly the registered Finding ids are served",
                "",
            )
        )
        out.append(
            (
                observed["by_status"] == summary["by_status"],
                "live: reported / not_reported / excluded counts match the registered data",
                f"{observed['by_status']} vs {summary['by_status']}",
            )
        )
    return out


def footer_expectation(tree: Path | None) -> dict:
    """The frontend's own declared contract version and tolerated versions, read from config.js."""
    if tree is None:
        return {"declared": None, "supported": None}
    path = tree / "frontend" / "static" / "js" / "config.js"
    if not path.is_file():
        return {"declared": None, "supported": None}
    text = path.read_text(encoding="utf-8")
    declared = re.search(r'CONTRACT_VERSION\s*=\s*"(\d+\.\d+\.\d+)"', text)
    listed = re.search(r"SUPPORTED_CONTRACT_VERSIONS\s*=\s*Object\.freeze\(\[(.*?)\]\)", text, re.S)
    supported = re.findall(r'"(\d+\.\d+\.\d+)"', listed.group(1)) if listed else None
    d = declared.group(1) if declared else None
    return {"declared": d, "supported": supported or ([d] if d else None)}
