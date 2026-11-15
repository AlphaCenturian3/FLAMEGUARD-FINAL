"""SYNTHETIC evidence scenarios for the development preview's tests. NOT NASA DATA.

Each scenario writes a small repository under `dest`, built from the contract examples of the
exported tree (schemas, vocabulary and provenance checker are copied from it), and is read by
the unmodified B1 loader through `FLAMEGUARD_DATA_ROOT`. Every statement says SYNTHETIC. Live
mode shows no fixture banner, so these must never be used for anything but local inspection
and the smoke tests on a throwaway port.

    empty     the exported data/manifest.json as it is (no registered evidence)
    synthetic one investigation: a measured, an excluded and a missing finding, plus an
              interpretation that explains the exclusion
    rejected  as `synthetic`, plus one file whose checksum is wrong (rejected, reported in the
              X-FlameGuard-Rejected-Entries header, the rest still served)
    broken    an unreadable manifest (every evidence endpoint fails closed with 503)
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

SYN = "SYNTHETIC PREVIEW DATA. Not NASA data."
REASON = "SYNTHETIC exclusion reason: not a real source note."
SOURCE = {
    "title": "SYNTHETIC SOURCE",
    "url": "https://example.invalid/synthetic",
    "retrieved": "2026-11-14",
}
SCENARIOS = ("empty", "synthetic", "rejected", "broken")


def _example(tree: Path, name: str) -> dict:
    doc = json.loads((tree / "contracts" / "examples" / name).read_text(encoding="utf-8"))
    doc.pop("fixture", None)
    return doc


def _prov(fid: str) -> dict:
    return {"manifest_id": "ds-a", "locator": f"SYNTHETIC {fid}", "sources": [SOURCE]}


def make_scenario(name: str, tree: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for rel in ("contracts/schemas", "contracts/vocabulary.json", "tools", "data"):
        src, out = tree / rel, dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copy)(src, out)
    if name == "empty":
        return dest
    if name == "broken":
        (dest / "data" / "manifest.json").write_text("{ not json", encoding="utf-8")
        return dest

    inv = _example(tree, "investigation.example.json")
    inv.update(id="inv-a", name="SYNTHETIC investigation", datasets=["ds-a"], sources=[SOURCE])
    m1 = _example(tree, "finding.measured.example.json")
    m1.update(id="m1", investigation_id="inv-a", statement=SYN, provenance=_prov("m1"))
    ex = _example(tree, "finding.measured_excluded.example.json")
    ex.update(id="ex1", investigation_id="inv-a", statement=SYN, provenance=_prov("ex1"))
    ex["curation_notes"][0]["note"] = REASON
    ex["curation_notes"][0]["source"] = {**SOURCE, "quote": "SYNTHETIC quote."}
    miss = _example(tree, "finding.measured_missing.example.json")
    miss.update(id="mi1", investigation_id="inv-a", statement=SYN, provenance=_prov("mi1"))
    expl = _example(tree, "finding.interpretation.example.json")
    expl.update(id="e1", investigation_id="inv-a", statement=SYN)
    expl["provenance"] = {**expl["provenance"], "derived_from": ["ex1"]}
    expl["limitations"] = [f"Explains the exclusion: {REASON}"]
    expl.pop("relevant_environments", None)

    docs = {
        "data/curated/investigations.json": ("ds-inv", "measured", [inv]),
        "data/curated/findings/inv-a.json": ("ds-a", "measured", [m1, ex, miss]),
        "data/curated/interpretations/notes.json": ("ds-notes", "interpretation", [expl]),
    }
    entries = []
    for rel, (entry_id, cls, doc) in docs.items():
        text = json.dumps(doc, indent=1).replace("FIXTURE", "SYNTHETIC")
        text = text.replace("fixture", "synthetic")
        if "fixture" in text.lower():
            raise RuntimeError(f"{rel}: fixture wording leaked into a scenario")
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if name == "rejected" and entry_id == "ds-notes":
            sha = "0" * 64  # wrong checksum: the loader must reject this one file
        entry = {
            "id": entry_id,
            "path": rel,
            "evidence_class": cls,
            "sha256": sha,
            "description": f"SYNTHETIC {entry_id}",
        }
        if cls == "measured":
            entry.update(sources=[SOURCE], rights_status="under_review")
        else:
            entry.update(derived_from=["ds-a"], method="SYNTHETIC method")
        entries.append(entry)
    manifest = {"manifest_version": "0.2.0", "datasets": entries}
    (dest / "data" / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return dest
