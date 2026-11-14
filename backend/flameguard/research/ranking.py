"""Transparent research-relevance ranking.

The ranking answers one question: *which NASA investigations hold evidence that best fits
the user's stated research question?* It does **not** rank fire danger, and no score is a
probability (``NOT_A_RISK_SCORE`` is attached to every output).

Method (weights are read from a criteria file; the v1 weights are a *proposal*):

``score = sum(weight_c * criterion_score_c)`` over four criteria, each scored in [0, 1]:

- ``purpose_relevance``: mean of the parts the question specifies: share of question
  topics covered, share of question quantities with a reported value, and whether the
  evidence is tagged for the question's target environment.
- ``condition_match``: share of the question's experimental conditions matched by at
  least one record. A condition no record reports counts as unmatched and is listed as
  missing. If the question gives no conditions the criterion scores 0 for everyone and is
  marked "not assessed" (this does not change the order).
- ``source_traceability``: per record, the share of four checks (http(s) URL, retrieval
  date, exact quote, locator/archive id/DOI). An interpretation inherits the mean
  traceability of the records it is derived from; unresolved inputs count as 0.
- ``data_completeness``: per record, the share of condition keys, test id, value and
  uncertainty that the source reports.

Only ``measured`` and ``interpreted`` records are scored (contract 5.1: ranking inputs
are measured or interpretation only). ``reported`` statements are listed as context.
Simulations raise an error. Fixtures are refused unless ``allow_fixtures=True`` (tests).

Gates (``release_status``):

- ``disabled_criteria_not_frozen``: real records, but the criteria file is not
  ``approved`` with named reviewers. No item is scored (CP1: no ranking output before R1).
- ``evidence_insufficient``: criteria approved, but no investigation has verified
  measured or interpreted evidence. Real measured records count only if their
  ``manifest_id`` is in ``verified_manifest_ids``.
- ``fixture_demo_only``: fixture records (tests). Never released.
- ``released``: approved criteria and at least one scored investigation.

Each criterion in ``explanations`` has a ``status`` (``complete``, ``partially_missing``
or ``not_assessed``) so a missing input is never hidden inside a zero.
"""

import json
import math
from collections.abc import Collection, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from flameguard.research.common import (
    CONDITION_KEYS,
    DATE_RE,
    ENVIRONMENTS,
    FIRE_SAFETY_TOPICS,
    GENERATED_BY,
    NOT_A_RISK_SCORE,
    TARGET_CONTRACT,
    URL_RE,
    VOCABULARY,
)
from flameguard.research.evidence import (
    Record,
    contract_evidence_class,
    missing_fields,
    validate_evidence,
)

EXPECTED_CRITERIA = (
    "purpose_relevance",
    "condition_match",
    "source_traceability",
    "data_completeness",
)
CRITERIA_STATUSES = ("proposed", "approved", "superseded")
SCORED_CATEGORIES = ("measured", "interpreted")


class RankingInputError(ValueError):
    """Raised for an invalid question, criteria file, or forbidden input."""


# --------------------------------------------------------------------------- criteria


def validate_criteria(criteria: Any) -> list[str]:
    if not isinstance(criteria, Mapping):
        return ["criteria must be an object"]
    errors = []
    for key in ("criteria_version", "status", "approved_by", "purpose", "criteria"):
        if key not in criteria:
            errors.append(f"criteria file missing '{key}'")
    if errors:
        return errors
    if criteria["status"] not in CRITERIA_STATUSES:
        errors.append(f"status must be one of {CRITERIA_STATUSES}")
    if criteria["status"] == "approved" and not criteria["approved_by"]:
        errors.append("an approved criteria file must name its reviewers in approved_by")
    items = criteria["criteria"]
    ids = [c.get("id") for c in items if isinstance(c, Mapping)]
    if sorted(ids) != sorted(EXPECTED_CRITERIA) or len(ids) != len(items):
        errors.append(f"criteria ids must be exactly {EXPECTED_CRITERIA}")
    total = 0.0
    for c in items:
        if not isinstance(c, Mapping):
            continue
        w = c.get("weight")
        if isinstance(w, bool) or not isinstance(w, int | float) or not 0 <= w <= 1:
            errors.append(f"{c.get('id')}: weight must be within 0..1")
        else:
            total += w
        for key in ("description", "scoring_rule"):
            if not isinstance(c.get(key), str) or not c[key].strip():
                errors.append(f"{c.get('id')}: '{key}' is required")
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        errors.append(f"weights must sum to 1 (got {total})")
    return errors


def load_criteria(path: str | Path) -> dict[str, Any]:
    criteria = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_criteria(criteria)
    if errors:
        raise RankingInputError("; ".join(errors))
    return criteria


# --------------------------------------------------------------------------- question


def validate_question(question: Any) -> list[str]:
    """A research question is structured so that relevance is computed, not guessed.

    Keys: ``text`` (str), ``target_environment`` (contract environment), ``topics``
    (fire-safety topics), ``quantities`` (vocabulary keys), ``conditions``
    (condition key -> exact value or ``{"min": x, "max": y}``).
    """
    if not isinstance(question, Mapping):
        return ["question must be an object"]
    errors = []
    if not isinstance(question.get("text"), str) or not question["text"].strip():
        errors.append("question text is required")
    if question.get("target_environment") not in ENVIRONMENTS:
        errors.append(f"target_environment must be one of {ENVIRONMENTS}")
    topics = question.get("topics", [])
    quantities = question.get("quantities", [])
    if any(t not in FIRE_SAFETY_TOPICS for t in topics):
        errors.append(f"topics must use {FIRE_SAFETY_TOPICS}")
    if any(q not in VOCABULARY for q in quantities):
        errors.append(f"quantities must use {sorted(VOCABULARY)}")
    if not topics and not quantities:
        errors.append("the question must name at least one topic or quantity")
    for key, spec in (question.get("conditions") or {}).items():
        if key not in CONDITION_KEYS:
            errors.append(f"unknown condition '{key}'")
        elif isinstance(spec, Mapping):
            lo, hi = spec.get("min"), spec.get("max")
            if not all(isinstance(v, int | float) for v in (lo, hi)) or lo > hi:
                errors.append(f"condition '{key}': range needs numeric min <= max")
        elif spec is None:
            errors.append(f"condition '{key}': give a value or a range, not null")
    return errors


def _matches(value: Any, spec: Any) -> bool:
    if value is None:
        return False
    if isinstance(spec, Mapping):
        return isinstance(value, int | float) and spec["min"] <= value <= spec["max"]
    return value == spec


# --------------------------------------------------------------------------- criteria scores


def _criterion(score: float, inputs: Iterable[Record], **detail: Any) -> dict[str, Any]:
    return {
        "score": score,
        "inputs": sorted({r["id"]: r for r in inputs}.values(), key=lambda r: r["id"]),
        **detail,
    }


def _purpose(q: Mapping, recs: Sequence[Record]) -> dict[str, Any]:
    parts, used, notes = [], [], []
    if q.get("topics"):
        wanted = set(q["topics"])
        hits = [r for r in recs if wanted.intersection(r.get("fire_safety_topics", []))]
        covered = wanted.intersection(t for r in hits for t in r.get("fire_safety_topics", []))
        parts.append(len(covered) / len(wanted))
        used += hits
        notes.append(f"topics covered {len(covered)}/{len(wanted)}: {sorted(covered)}")
    if q.get("quantities"):
        wanted = set(q["quantities"])
        hits = [r for r in recs if r["quantity"] in wanted and r["value_status"] == "reported"]
        covered = {r["quantity"] for r in hits}
        parts.append(len(covered) / len(wanted))
        used += hits
        notes.append(f"quantities with a reported value {len(covered)}/{len(wanted)}")
    env = q["target_environment"]
    hits = [r for r in recs if env in r.get("relevant_environments", [])]
    parts.append(1.0 if hits else 0.0)
    used += hits
    notes.append(f"evidence tagged for '{env}': {'yes' if hits else 'no'}")
    return _criterion(sum(parts) / len(parts), used, notes=notes)


def _conditions(q: Mapping, recs: Sequence[Record]) -> dict[str, Any]:
    wanted = q.get("conditions") or {}
    if not wanted:
        return _criterion(
            0.0, [], notes=["not assessed: the question specifies no conditions"], matched=[]
        )
    matched, unmatched, missing, used = [], [], [], []
    for key, spec in wanted.items():
        values = [(r, (r.get("conditions") or {}).get(key)) for r in recs]
        hits = [r for r, v in values if _matches(v, spec)]
        if hits:
            matched.append(key)
            used += hits
        elif all(v is None for _, v in values):
            missing.append(key)
        else:
            unmatched.append(key)
    return _criterion(
        len(matched) / len(wanted),
        used,
        matched=matched,
        unmatched=unmatched,
        missing=missing,
        notes=[f"conditions matched {len(matched)}/{len(wanted)}"],
    )


def _record_traceability(rec: Record, index: Mapping[str, Record], seen: frozenset) -> float:
    if rec["id"] in seen:
        return 0.0  # cycle
    if rec["evidence_category"] == "interpreted":
        parents = rec.get("derived_from") or []
        scores = [
            _record_traceability(index[p], index, seen | {rec["id"]})
            if p in index and index[p]["evidence_category"] in SCORED_CATEGORIES
            else 0.0
            for p in parents
        ]
        return sum(scores) / len(scores) if scores else 0.0
    best = 0.0
    anchored = bool(rec.get("locator") or rec.get("doi"))
    for src in rec.get("sources", []):
        checks = (
            bool(URL_RE.match(src.get("url") or "")),
            bool(DATE_RE.match(src.get("retrieved") or "")),
            bool(src.get("quote")),
            anchored or bool(src.get("archive_id")),
        )
        best = max(best, sum(checks) / len(checks))
    return best


def _traceability(recs: Sequence[Record], index: Mapping[str, Record]) -> dict[str, Any]:
    per = {r["id"]: _record_traceability(r, index, frozenset()) for r in recs}
    weak = sorted(k for k, v in per.items() if v < 1)
    return _criterion(
        sum(per.values()) / len(per),
        recs,
        per_record=per,
        notes=[f"records with incomplete traceability: {weak or 'none'}"],
    )


def _record_completeness(rec: Record) -> float:
    conditions = rec.get("conditions") or {}
    checks = [conditions.get(k) is not None for k in CONDITION_KEYS]
    checks.append(rec.get("test_id") is not None)
    if rec.get("quantity") is not None:
        checks.append(rec.get("value_status") == "reported")
        checks.append(rec.get("uncertainty") is not None)
    return sum(checks) / len(checks)


def _completeness(recs: Sequence[Record]) -> dict[str, Any]:
    per = {r["id"]: _record_completeness(r) for r in recs}
    return _criterion(
        sum(per.values()) / len(per),
        recs,
        per_record=per,
        notes=["share of condition keys, test id, value and uncertainty reported"],
    )


# --------------------------------------------------------------------------- ranking


def _criterion_status(part: Mapping[str, Any]) -> str:
    """Make missing inputs visible instead of hiding them inside a zero.

    ``not_assessed``: the question gave nothing to assess. ``partially_missing``: some
    inputs were not reported by the source. ``complete``: every input was reported.
    """
    if any("not assessed" in n for n in part.get("notes", [])):
        return "not_assessed"
    if part.get("missing") or any(v < 1 for v in part.get("per_record", {}).values()):
        return "partially_missing"
    return "complete"


def _reject_simulations(records: Sequence[Record]) -> None:
    for r in records:
        marks = (r.get("evidence_category"), r.get("evidence_class"))
        if "illustrative_simulation" in marks or "label" in r or "model" in r:
            raise RankingInputError(
                f"{r.get('id')}: simulation output can never be a ranking input"
            )


def rank_investigations(
    question: Mapping[str, Any],
    records: Sequence[Record],
    criteria: Mapping[str, Any],
    *,
    investigation_ids: Iterable[str] | None = None,
    verified_manifest_ids: Collection[str] | None = None,
    allow_fixtures: bool = False,
) -> dict[str, Any]:
    """Rank investigations by research relevance to ``question``. See module docstring.

    ``verified_manifest_ids`` is the set of manifest ids that passed the provenance check
    and the loader (Member 3 data, Member 1 loader B1). A real ``measured`` record whose
    ``manifest_id`` is not in it is excluded, so no ranking runs on unverified values.
    """
    errors = validate_question(question) + validate_criteria(criteria)
    if errors:
        raise RankingInputError("; ".join(errors))
    _reject_simulations(records)
    fixture_flags = {bool(r.get("fixture")) for r in records}
    if len(fixture_flags) > 1:
        raise RankingInputError("fixture and real records cannot be ranked together")
    uses_fixtures = fixture_flags == {True}
    criteria_frozen = criteria["status"] == "approved" and bool(criteria["approved_by"])
    disabled = not uses_fixtures and not criteria_frozen
    verified = set(verified_manifest_ids or ())

    excluded_records: list[dict[str, Any]] = []
    valid: list[Record] = []
    for r in records:
        problems = validate_evidence(r)
        if r.get("fixture") and not allow_fixtures:
            problems.append("fixture records are refused outside tests")
        if (
            not r.get("fixture")
            and r.get("evidence_category") == "measured"
            and r.get("manifest_id") not in verified
        ):
            problems.append(
                "manifest_id is not a verified manifest entry; measured values are used only "
                "after Member 3's import and the provenance check"
            )
        if problems:
            excluded_records.append({"id": r.get("id"), "reasons": problems})
        else:
            valid.append(r)
    index = {r["id"]: r for r in valid}

    universe = sorted(set(investigation_ids or []) | {r.get("investigation_id") for r in records})
    weights = {c["id"]: c["weight"] for c in criteria["criteria"]}

    items, excluded, explanations = [], [], {}
    for inv in universe:
        mine = [r for r in valid if r["investigation_id"] == inv]
        scored = [r for r in mine if r["evidence_category"] in SCORED_CATEGORIES]
        context = [r["id"] for r in mine if r["evidence_category"] == "reported"]
        if disabled or not scored:
            if not scored:
                reason = "insufficient evidence: no verified measured or interpreted evidence"
            else:
                reason = f"{len(scored)} eligible record(s) not scored"
            if context:
                reason += f"; {len(context)} quoted source statement(s) available as context only"
            if disabled:
                reason += (
                    "; ranking disabled until the criteria are frozen and approved (R1, "
                    "approvers named in approved_by)"
                )
            excluded.append({"investigation_id": inv, "reason": reason})
            continue
        parts = {
            "purpose_relevance": _purpose(question, scored),
            "condition_match": _conditions(question, scored),
            "source_traceability": _traceability(scored, index),
            "data_completeness": _completeness(scored),
        }
        score = sum(weights[c] * parts[c]["score"] for c in EXPECTED_CRITERIA)
        criterion_scores = [
            {
                "criterion_id": c,
                "score": parts[c]["score"],
                "inputs": [
                    {
                        "finding_id": r["id"],
                        "evidence_class": contract_evidence_class(r["evidence_category"]),
                    }
                    for r in parts[c]["inputs"]
                ],
            }
            for c in EXPECTED_CRITERIA
        ]
        rationale = "; ".join(
            f"{c} {parts[c]['score']:.2f} x weight {weights[c]:.2f}" for c in EXPECTED_CRITERIA
        )
        items.append(
            {
                "investigation_id": inv,
                "score": score,
                "criterion_scores": criterion_scores,
                "rationale": f"{rationale}. Research relevance only, not fire risk.",
            }
        )
        explanations[inv] = {
            "criteria": {
                c: {
                    "weight": weights[c],
                    "score": parts[c]["score"],
                    "weighted": weights[c] * parts[c]["score"],
                    "status": _criterion_status(parts[c]),
                    **{k: v for k, v in parts[c].items() if k not in ("score", "inputs")},
                }
                for c in EXPECTED_CRITERIA
            },
            "missing_evidence": {r["id"]: missing_fields(r) for r in scored},
            "context_statements": context,
        }

    items.sort(key=lambda it: (-it["score"], it["investigation_id"]))
    for rank, it in enumerate(items, start=1):
        it["rank"] = rank

    if uses_fixtures:
        release_status = "fixture_demo_only"
    elif disabled:
        release_status = "disabled_criteria_not_frozen"
    elif not items:
        release_status = "evidence_insufficient"
    else:
        release_status = "released"

    ranking = {
        "contract_version": TARGET_CONTRACT,
        "context": question["target_environment"],
        "criteria_version": criteria["criteria_version"],
        "criteria": [
            {"id": c["id"], "description": c["description"], "weight": c["weight"]}
            for c in criteria["criteria"]
        ],
        "items": items,
        "excluded": excluded,
        "generated_by": GENERATED_BY,
    }
    if uses_fixtures:
        ranking["fixture"] = True
    return {
        "disclaimer": NOT_A_RISK_SCORE,
        "release_status": release_status,
        "criteria_status": criteria["status"],
        "question": dict(question),
        "ranking": ranking,
        "explanations": explanations,
        "excluded_records": excluded_records,
    }
