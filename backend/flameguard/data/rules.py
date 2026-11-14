"""Pure cross-file evidence rules: S3 (derived_from chains) and transitive S9.

No I/O and no imports from the rest of the backend. The loader (loader.py) feeds it the
findings of every document that already passed schema and provenance checks.

S3   `derived_from` ids resolve to loaded findings and form no cycle. A finding that depends
     on an unresolved, cyclic or otherwise invalid finding is itself invalid, never "clean".
S9   A finding is exclusion-dependent if it is `excluded`, or if any `derived_from` ancestor
     at any depth is `excluded`. An exclusion-dependent interpretation may only explain the
     exclusion: `value` and `quantity` are null, it carries no `relevant_environments`, and
     its `limitations` quote the exact exclusion note of an excluded ancestor.

Ranking, comparison and TARS (B3, B4, B6) must use `exclusion_dependent` to keep such
findings out of evidence. This module decides validity only; it never scores anything.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

Finding = Mapping[str, Any]


@dataclass(frozen=True)
class ChainAnalysis:
    problems: Mapping[str, tuple[str, ...]]  # finding id -> reasons; empty if the chain is sound
    exclusion_dependent: frozenset[str]  # sound chains only; includes the excluded findings
    excluded: frozenset[str]  # findings whose value_status is "excluded"


def parents_of(finding: Finding) -> tuple[str, ...]:
    if finding.get("evidence_class") != "interpretation":
        return ()
    return tuple(finding.get("provenance", {}).get("derived_from", ()))


def _reaches(start: str, target: str, findings: Mapping[str, Finding]) -> bool:
    """True if `target` is `start` or one of its ancestors (iterative, cycle-safe)."""
    seen: set[str] = set()
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur == target:
            return True
        if cur in seen or cur not in findings:
            continue
        seen.add(cur)
        stack.extend(parents_of(findings[cur]))
    return False


def exclusion_notes(finding: Finding) -> tuple[str, ...]:
    return tuple(
        n["note"] for n in finding.get("curation_notes", ()) if n.get("kind") == "exclusion"
    )


def analyze(findings: Mapping[str, Finding]) -> ChainAnalysis:
    problems: dict[str, list[str]] = {}

    def flag(fid: str, reason: str) -> None:
        problems.setdefault(fid, []).append(reason)

    for fid, f in findings.items():
        for parent in parents_of(f):
            if parent not in findings:
                flag(fid, f"S3: derived_from id {parent!r} does not resolve to a loaded finding")
            elif _reaches(parent, fid, findings):
                flag(fid, f"S3: derived_from cycle through {parent!r}")

    # A finding that depends on an invalid finding is invalid (fixed point).
    changed = True
    while changed:
        changed = False
        for fid, f in findings.items():
            if fid in problems:
                continue
            bad = next((p for p in parents_of(f) if p in problems), None)
            if bad is not None:
                flag(fid, f"S3: depends on invalid finding {bad!r}")
                changed = True

    memo: dict[str, bool] = {}

    def dependent(fid: str) -> bool:  # only called on sound (acyclic, resolved) findings
        if fid not in memo:
            f = findings[fid]
            memo[fid] = f.get("value_status") == "excluded" or any(
                dependent(p) for p in parents_of(f)
            )
        return memo[fid]

    sound = [fid for fid in findings if fid not in problems]
    dep = frozenset(fid for fid in sound if dependent(fid))
    excluded = frozenset(fid for fid in sound if findings[fid].get("value_status") == "excluded")

    def excluded_ancestors(fid: str) -> set[str]:
        out: set[str] = set()
        seen: set[str] = set()
        stack = [fid]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            if cur in excluded:
                out.add(cur)
            stack.extend(parents_of(findings[cur]))
        return out

    for fid in sorted(dep):
        f = findings[fid]
        if f.get("evidence_class") != "interpretation":
            continue
        if f.get("value") is not None or f.get("quantity") is not None:
            flag(fid, "S9: exclusion-dependent interpretation carries a value or quantity")
        if f.get("relevant_environments"):
            flag(fid, "S9: exclusion-dependent interpretation is tagged for an environment")
        reasons = {n for anc in excluded_ancestors(fid) for n in exclusion_notes(findings[anc])}
        limitations = f.get("limitations", ())
        if not any(r in lim for lim in limitations for r in reasons):
            flag(fid, "S9: limitations do not quote the exclusion note it explains")

    # An S9 violation makes the finding invalid, so it must not appear as sound evidence.
    return ChainAnalysis(
        problems={k: tuple(v) for k, v in problems.items()},
        exclusion_dependent=frozenset(fid for fid in dep if fid not in problems),
        excluded=frozenset(fid for fid in excluded if fid not in problems),
    )
