"""Builders for B1 loader tests: small SYNTHETIC repositories written into tmp_path.

Nothing here is NASA data. Documents are derived from the contract examples, with the
`fixture` flag removed so that they exercise the loader's accept path, and they live only
in temporary directories. The real data/curated folder is never touched.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "contracts" / "examples"
SYN = "SYNTHETIC LOADER TEST DATA. Not NASA data."
REASON = "SYNTHETIC exclusion reason: value conflicts with a caption in the same source."
SOURCE = {
    "title": "SYNTHETIC SOURCE",
    "url": "https://example.invalid/synthetic",
    "retrieved": "2026-11-14",
}


def example(name: str) -> dict:
    doc = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    doc.pop("fixture", None)
    return doc


def investigation(inv_id: str, datasets: list[str]) -> dict:
    doc = example("investigation.example.json")
    doc.update(id=inv_id, name=f"SYNTHETIC {inv_id}", datasets=datasets)
    return doc


def measured(fid: str, inv_id: str, manifest_id: str, **extra) -> dict:
    doc = example("finding.measured.example.json")
    doc.update(id=fid, investigation_id=inv_id, statement=SYN)
    doc["provenance"] = {
        "manifest_id": manifest_id,
        "locator": f"SYNTHETIC {fid}",
        "sources": [SOURCE],
    }
    doc.update(extra)
    return doc


def excluded(fid: str, inv_id: str, manifest_id: str) -> dict:
    doc = example("finding.measured_excluded.example.json")
    doc.update(id=fid, investigation_id=inv_id, statement=SYN)
    doc["provenance"] = {
        "manifest_id": manifest_id,
        "locator": f"SYNTHETIC {fid}",
        "sources": [SOURCE],
    }
    note = doc["curation_notes"][0]
    note.update(note=REASON)
    note["source"] = {**SOURCE, "quote": "SYNTHETIC quote."}
    return doc


def interpretation(fid: str, inv_id: str, parents: list[str], **extra) -> dict:
    doc = example("finding.interpretation.example.json")
    doc.update(id=fid, investigation_id=inv_id, statement=SYN)
    doc["provenance"] = {**doc["provenance"], "derived_from": parents}
    doc.update(extra)
    return doc


def explanation(fid: str, inv_id: str, parents: list[str], **extra) -> dict:
    """An interpretation that only explains an exclusion (valid under S9)."""
    doc = interpretation(fid, inv_id, parents, limitations=[f"Explains the exclusion: {REASON}"])
    doc.pop("relevant_environments", None)
    doc.update(extra)
    return doc


class Scenario:
    """A synthetic repository: documents are plain dicts so tests can break one rule at a time.

    Entry ids: ds-inv (investigations), ds-a (findings/inv-a.json), ds-notes (interpretations).
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.investigations = [investigation("inv-a", ["ds-a"])]
        self.findings = {
            "inv-a": [measured("m1", "inv-a", "ds-a"), excluded("ex1", "inv-a", "ds-a")],
        }
        self.interps = {
            "notes": [interpretation("i1", "inv-a", ["m1"]), explanation("e1", "inv-a", ["ex1"])]
        }
        self.extra_entries: list[dict] = []
        self.raw: dict[str, str] = {}  # relative path -> raw text written instead of JSON
        self.tamper: dict[str, str] = {}  # entry id -> sha256 to register instead of the real one

    def write(self) -> Path:
        shutil.copytree(REPO / "contracts" / "schemas", self.root / "contracts" / "schemas")
        shutil.copy(REPO / "contracts" / "vocabulary.json", self.root / "contracts")
        (self.root / "tools").mkdir()
        shutil.copy(REPO / "tools" / "check_data_provenance.py", self.root / "tools")
        entries = []

        def add(entry_id: str, rel: str, cls: str, text: str, **fields) -> None:
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            sha = self.tamper.get(entry_id, hashlib.sha256(text.encode("utf-8")).hexdigest())
            entries.append(
                {
                    "id": entry_id,
                    "path": rel,
                    "evidence_class": cls,
                    "sha256": sha,
                    "description": f"SYNTHETIC {entry_id}",
                    **fields,
                }
            )

        def dump(obj) -> str:
            return json.dumps(obj, indent=1, allow_nan=True)

        measured_fields = {"sources": [SOURCE], "rights_status": "under_review"}
        add(
            "ds-inv",
            "data/curated/investigations.json",
            "measured",
            self.raw.get("data/curated/investigations.json", dump(self.investigations)),
            **measured_fields,
        )
        for inv_id, items in self.findings.items():
            rel = f"data/curated/findings/{inv_id}.json"
            add(
                "ds-" + inv_id.removeprefix("inv-"),
                rel,
                "measured",
                self.raw.get(rel, dump(items)),
                **measured_fields,
            )
        for name, items in self.interps.items():
            rel = f"data/curated/interpretations/{name}.json"
            add(
                "ds-" + name,
                rel,
                "interpretation",
                self.raw.get(rel, dump(items)),
                derived_from=["ds-a"],
                method="SYNTHETIC method",
            )
        for extra in copy.deepcopy(self.extra_entries):
            add(
                extra.pop("id"),
                extra.pop("path"),
                extra.pop("evidence_class"),
                extra.pop("text"),
                **extra,
            )
        manifest = {"manifest_version": "0.2.0", "datasets": entries}
        manifest_text = self.raw.get("data/manifest.json", dump(manifest))
        (self.root / "data").mkdir(exist_ok=True)
        (self.root / "data" / "manifest.json").write_text(
            manifest_text, encoding="utf-8", newline="\n"
        )
        return self.root


@pytest.fixture
def scenario(tmp_path) -> Scenario:
    return Scenario(tmp_path / "repo")
