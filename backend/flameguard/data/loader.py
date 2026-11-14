"""B1 evidence loader: strict, provenance-checked, schema-validated, fail-closed.

`load_evidence(root)` reads `data/manifest.json` and returns a `LoadResult`: an immutable
`EvidenceStore` of what passed, and a typed `LoadReport` naming every manifest entry with its
status and reasons. It never raises for bad data, and it never returns part of a bad file.

Order of checks (spec section 5.2a, contracts/README.md):
 1. manifest: strict JSON (no NaN or Infinity) and `data_manifest.schema.json`. A failure here
    loads nothing.
 2. provenance: `tools/check_data_provenance.py` (the one provenance implementation, loaded
    from the repository, never re-implemented here) for every non-simulation entry.
 3. per file: strict JSON, contract schema for every item, no `fixture: true`, and
    S1 (a measured finding's `manifest_id` is the measured entry whose file holds it) and
    S2 (`findings/<id>.json` holds only findings of investigation <id>).
 4. across files, repeated until stable: duplicate ids, S3 (`derived_from` resolves, no cycle),
    transitive S9 (see rules.py). A file with any bad finding is rejected whole, and files that
    depended on it are rejected in turn.
 5. S4: `Investigation.datasets` ids resolve to measured manifest entries.

Illustrative simulations are never evidence: entries of class `illustrative_simulation` are
skipped before any file is opened, and nothing under `data/simulated/` is read here.
Registered CSV sources and quality-flag files are not Finding JSON and are skipped, not parsed.
This module computes no ranking, comparison or answer.
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from flameguard.data import rules

DEFAULT_ROOT = Path(__file__).resolve().parents[3]
SIMULATION_CLASS = "illustrative_simulation"
MAX_SCHEMA_ERRORS = 5


class Status(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class Role(StrEnum):
    INVESTIGATIONS = "investigations"
    FINDINGS = "findings"
    INTERPRETATIONS = "interpretations"
    SOURCE = "source"  # registered non-JSON file: the as-printed source or a quality-flag file
    SIMULATION = "simulation"
    UNRECOGNIZED = "unrecognized"


@dataclass(frozen=True)
class EntryReport:
    id: str
    path: str
    evidence_class: str
    role: Role
    status: Status
    reasons: tuple[str, ...] = ()
    loaded: int = 0  # investigations or findings taken from this entry


@dataclass(frozen=True)
class LoadReport:
    manifest_ok: bool
    manifest_errors: tuple[str, ...]
    entries: tuple[EntryReport, ...]
    warnings: tuple[str, ...] = ()

    def entry(self, entry_id: str) -> EntryReport:
        return next(e for e in self.entries if e.id == entry_id)

    @property
    def accepted(self) -> tuple[EntryReport, ...]:
        return tuple(e for e in self.entries if e.status is Status.ACCEPTED)

    @property
    def rejected(self) -> tuple[EntryReport, ...]:
        return tuple(e for e in self.entries if e.status is Status.REJECTED)

    @property
    def skipped(self) -> tuple[EntryReport, ...]:
        return tuple(e for e in self.entries if e.status is Status.SKIPPED)


@dataclass(frozen=True)
class EvidenceStore:
    investigations: tuple[Mapping[str, Any], ...] = ()
    findings: Mapping[str, Mapping[str, Any]] = MappingProxyType({})
    exclusion_dependent: frozenset[str] = frozenset()  # S9: never ranking, compare or TARS evidence
    excluded: frozenset[str] = frozenset()


@dataclass(frozen=True)
class LoadResult:
    store: EvidenceStore
    report: LoadReport


@dataclass
class _Doc:
    entry: dict[str, Any]
    role: Role
    inv_id: str | None = None  # the <id> in findings/<id>.json
    items: list[dict[str, Any]] | None = None
    reasons: list[str] | None = None

    def __post_init__(self) -> None:
        self.reasons = [] if self.reasons is None else self.reasons


def classify(entry: Mapping[str, Any]) -> tuple[Role, str | None]:
    """Decide what a manifest entry is, from its class and path alone."""
    if entry.get("evidence_class") == SIMULATION_CLASS:
        return Role.SIMULATION, None
    path = str(entry.get("path", ""))
    if not path.endswith(".json"):
        return Role.SOURCE, None
    parts = path.split("/")
    if path == "data/curated/investigations.json":
        return Role.INVESTIGATIONS, None
    if len(parts) == 4 and parts[:3] == ["data", "curated", "findings"]:
        return Role.FINDINGS, parts[3].removesuffix(".json")
    if len(parts) == 4 and parts[:3] == ["data", "curated", "interpretations"]:
        return Role.INTERPRETATIONS, None
    return Role.UNRECOGNIZED, None


_EXPECTED_CLASS = {
    Role.INVESTIGATIONS: "measured",
    Role.FINDINGS: "measured",
    Role.INTERPRETATIONS: "interpretation",
}


def _load_tool(root: Path) -> Any:
    path = root / "tools" / "check_data_provenance.py"
    spec = importlib.util.spec_from_file_location("_flameguard_provenance_tool", path)
    if spec is None or spec.loader is None or not path.is_file():
        raise FileNotFoundError(f"provenance checker not found: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _registry(root: Path) -> Registry:
    resources = []
    for p in sorted((root / "contracts" / "schemas").glob("*.schema.json")):
        doc = _json_text(p)
        resources.append((doc["$id"], Resource.from_contents(doc)))
    if not resources:
        raise FileNotFoundError(f"contract schemas not found under {root / 'contracts'}")
    return Registry().with_resources(resources)


def _json_text(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_errors(validator: Draft202012Validator, item: Any, label: str) -> list[str]:
    found = sorted(validator.iter_errors(item), key=lambda e: [str(p) for p in e.absolute_path])
    out = [
        f"schema: {label}: {'/'.join(str(p) for p in e.absolute_path) or '<item>'}: "
        f"{e.message[:200]}"
        for e in found[:MAX_SCHEMA_ERRORS]
    ]
    if len(found) > MAX_SCHEMA_ERRORS:
        out.append(f"schema: {label}: and {len(found) - MAX_SCHEMA_ERRORS} more errors")
    return out


def _failed(errors: list[str]) -> LoadResult:
    report = LoadReport(manifest_ok=False, manifest_errors=tuple(errors), entries=())
    return LoadResult(EvidenceStore(), report)


def load_evidence(root: Path | str | None = None) -> LoadResult:
    root = Path(root) if root is not None else DEFAULT_ROOT
    try:
        tool = _load_tool(root)
        registry = _registry(root)
    except (OSError, ValueError, KeyError) as exc:
        return _failed([f"loader setup: {exc}"])

    def validator(name: str) -> Draft202012Validator:
        schema = _json_text(root / "contracts" / "schemas" / name)
        return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

    # 1. manifest ---------------------------------------------------------------------
    try:
        manifest = tool.load_strict_json(root / "data" / "manifest.json")
    except (OSError, ValueError) as exc:
        return _failed([f"manifest: {exc}"])
    errors = _schema_errors(validator("data_manifest.schema.json"), manifest, "manifest")
    if errors:
        return _failed(errors)
    entries: list[dict[str, Any]] = manifest["datasets"]

    # 2. provenance (non-simulation entries only: simulation files are never opened) ------
    evidence = [e for e in entries if e["evidence_class"] != SIMULATION_CLASS]
    ids = {e["id"] for e in evidence}
    by_entry: dict[str, list[str]] = {}
    manifest_level: list[str] = []
    for err in tool.check_manifest({**manifest, "datasets": evidence}, root):
        eid, _, msg = err.partition(": ")
        (by_entry.setdefault(eid, []) if eid in ids else manifest_level).append(msg or err)
    if manifest_level:
        return _failed([f"provenance: {m}" for m in manifest_level])

    # 3. per-file checks -------------------------------------------------------------------
    manifest_class = {e["id"]: e["evidence_class"] for e in entries}
    v_inv, v_finding = validator("investigation.schema.json"), validator("finding.schema.json")
    docs: list[_Doc] = []
    for entry in entries:
        role, inv_id = classify(entry)
        doc = _Doc(entry=entry, role=role, inv_id=inv_id)
        docs.append(doc)
        if role in (Role.SIMULATION, Role.SOURCE):
            continue
        doc.reasons.extend(f"provenance: {m}" for m in by_entry.get(entry["id"], []))
        if role is Role.UNRECOGNIZED:
            doc.reasons.append("layout: path is not a recognized evidence document")
        elif entry["evidence_class"] != _EXPECTED_CLASS[role]:
            doc.reasons.append(
                f"layout: a {role.value} file must be class {_EXPECTED_CLASS[role]!r}, "
                f"not {entry['evidence_class']!r}"
            )
        if doc.reasons:
            continue
        try:
            items = tool.load_strict_json(root / entry["path"])
        except (OSError, ValueError) as exc:
            doc.reasons.append(f"json: {exc}")
            continue
        if not isinstance(items, list):
            doc.reasons.append("json: document must be an array")
            continue
        doc.items = items
        _check_items(
            doc, items, v_inv if role is Role.INVESTIGATIONS else v_finding, manifest_class
        )

    # 4. across files: duplicates, S3, transitive S9 -----------------------------------------
    live = [d for d in docs if d.role in (Role.FINDINGS, Role.INTERPRETATIONS) and not d.reasons]
    analysis = rules.analyze({})
    while True:
        seen: dict[str, list[_Doc]] = {}
        for d in live:
            for f in d.items or []:
                seen.setdefault(f["id"], []).append(d)
        for fid, owners in seen.items():
            if len(owners) > 1:
                where = ", ".join(sorted({o.entry["id"] for o in owners}))
                for o in owners:
                    o.reasons.append(f"ids: finding id {fid!r} is defined more than once ({where})")
        if any(d.reasons for d in live):
            live = [d for d in live if not d.reasons]
            continue
        findings = {f["id"]: f for d in live for f in d.items or []}
        analysis = rules.analyze(findings)
        owner = {f["id"]: d for d in live for f in d.items or []}
        for fid, reasons in analysis.problems.items():
            owner[fid].reasons.extend(f"{fid}: {r}" for r in reasons)
        if not any(d.reasons for d in live):
            break
        live = [d for d in live if not d.reasons]

    # 5. S4 -----------------------------------------------------------------------------------
    rejected_ids = {d.entry["id"] for d in docs if d.reasons and d.role is not Role.INVESTIGATIONS}
    warnings: list[str] = []
    for d in docs:
        if d.role is not Role.INVESTIGATIONS or d.reasons:
            continue
        for inv in d.items or []:
            for ds in inv.get("datasets", []):
                if ds not in manifest_class:
                    d.reasons.append(f"S4: {inv['id']}: dataset {ds!r} is not in the manifest")
                elif manifest_class[ds] != "measured":
                    d.reasons.append(f"S4: {inv['id']}: dataset {ds!r} is not a measured entry")
                elif ds in rejected_ids:
                    warnings.append(f"{inv['id']}: dataset {ds!r} was rejected; no evidence loaded")

    # build the result -------------------------------------------------------------------------
    accepted = [d for d in docs if d.role in _EXPECTED_CLASS and not d.reasons]
    final = {
        f["id"]: f for d in accepted for f in (d.items or []) if d.role is not Role.INVESTIGATIONS
    }
    known = {inv["id"] for d in accepted if d.role is Role.INVESTIGATIONS for inv in d.items or []}
    for f in final.values():
        if f["investigation_id"] not in known:
            warnings.append(f"{f['id']}: investigation {f['investigation_id']!r} is not loaded")
    store = EvidenceStore(
        investigations=tuple(
            inv for d in accepted if d.role is Role.INVESTIGATIONS for inv in d.items or []
        ),
        findings=MappingProxyType(final),
        exclusion_dependent=analysis.exclusion_dependent,
        excluded=analysis.excluded,
    )
    reports = tuple(_report(d) for d in docs)
    return LoadResult(store, LoadReport(True, (), reports, tuple(warnings)))


def _check_items(
    doc: _Doc,
    items: list[dict[str, Any]],
    validate: Draft202012Validator,
    manifest_class: Mapping[str, str],
) -> None:
    role, entry = doc.role, doc.entry
    for n, item in enumerate(items):
        label = item.get("id", f"item {n}") if isinstance(item, dict) else f"item {n}"
        errs = _schema_errors(validate, item, str(label))
        doc.reasons.extend(errs)
        if errs:
            continue
        if item.get("fixture"):
            doc.reasons.append(f"fixture: {label}: fixtures never belong in data/curated")
        if role is Role.INVESTIGATIONS:
            continue
        if item["evidence_class"] != _EXPECTED_CLASS[role]:
            doc.reasons.append(f"layout: {label}: evidence_class must be {_EXPECTED_CLASS[role]}")
            continue  # the remaining checks assume the expected class
        if role is Role.FINDINGS:
            if item["investigation_id"] != doc.inv_id:
                doc.reasons.append(
                    f"S2: {label}: investigation_id {item['investigation_id']!r} in "
                    f"findings/{doc.inv_id}.json"
                )
            mid = item["provenance"]["manifest_id"]
            if mid != entry["id"]:
                if mid not in manifest_class:
                    why = "is not in the manifest"
                elif manifest_class[mid] != "measured":
                    why = "is not a measured entry"
                else:
                    why = f"names entry {mid!r}, whose file does not hold it"
                doc.reasons.append(f"S1: {label}: manifest_id {why}")
    if role is Role.INVESTIGATIONS:
        counts: dict[str, int] = {}
        for item in items:
            if isinstance(item, dict) and "id" in item:
                counts[item["id"]] = counts.get(item["id"], 0) + 1
        doc.reasons.extend(
            f"ids: investigation id {k!r} is defined more than once"
            for k, c in counts.items()
            if c > 1
        )


def _report(doc: _Doc) -> EntryReport:
    e = doc.entry
    base = {
        "id": e["id"],
        "path": e["path"],
        "evidence_class": e["evidence_class"],
        "role": doc.role,
    }
    if doc.role is Role.SIMULATION:
        return EntryReport(
            **base,
            status=Status.SKIPPED,
            reasons=("simulation data is never evidence and is not opened by the loader",),
        )
    if doc.role is Role.SOURCE:
        return EntryReport(
            **base,
            status=Status.SKIPPED,
            reasons=("registered source or quality file: not Finding JSON, so not parsed here",),
        )
    if doc.reasons:
        return EntryReport(**base, status=Status.REJECTED, reasons=tuple(doc.reasons))
    return EntryReport(**base, status=Status.ACCEPTED, loaded=len(doc.items or []))
