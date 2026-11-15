"""B3: the comparability decision of contract v0.2.2 (rules S5, S9, S11). Pure, no I/O.

`build_comparison` turns the findings the B1 loader accepted into a contract `Comparison` for
one quantity. It decides whether the rows may be compared and says why not. It never computes
with the values: no difference, ratio, mean, ordering, unit conversion, interpolation or gap
filling.

What makes rows NOT comparable (each case gives a reason):
- fewer than two rows, or a selected investigation without a measured finding of the quantity
- a row whose value is not `reported` (`not_reported`, `not_applicable` or `excluded`)
- a condition reported with different values across rows
- a condition reported for some rows and null for others
- a row with a `test_id` but no `test_outcome`
- outcomes reported for some rows and not for others
- rows that report different outcomes

Safeguards:
- Only `measured` findings become rows. Interpretations and simulations never do.
- S9: a value is copied only when its status is `reported`. Excluded and missing values are
  always null, and no reason quotes a measured value or a curation note.
- An outcome is read only from the finding's `test_outcome` field. Nothing here reads
  `statement`, `locator`, `uncertainty` or the value to infer one.
- S11 (test identity is all-or-nothing within an investigation) is enforced by the loader, so
  findings that break it never reach this module. Mixed identity ACROSS investigations is
  handled here: it makes the rows not comparable.

A condition that is null for every row gives no reason: contract v0.2.2 compares such rows. The
stricter mode that would block them is a v0.3 candidate (master spec, open decisions).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from flameguard import CONTRACT_VERSION
from flameguard.data.loader import EvidenceStore

Finding = Mapping[str, Any]

_STATUS_REASON = {
    "not_reported": "the source does not report a value",
    "not_applicable": "no numeric value applies",
    "excluded": "the value is excluded after a reviewed quality flag (see the finding's notes)",
}


class ComparisonError(Exception):
    """The accepted evidence breaks an invariant this module relies on. Nothing is served."""


def _text(value: Any) -> str | None:
    """A reported identifier or outcome; absent, null and "" all mean not reported."""
    return value if isinstance(value, str) and value else None


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _select(
    store: EvidenceStore, quantity: str, unit: str, investigation_ids: Sequence[str] | None
) -> list[Finding]:
    wanted = None if investigation_ids is None else list(investigation_ids)
    picked = []
    for finding in store.findings.values():
        if finding.get("evidence_class") != "measured" or finding.get("quantity") != quantity:
            continue
        if wanted is not None and finding["investigation_id"] not in wanted:
            continue
        if finding.get("unit") != unit:
            raise ComparisonError(f"finding {finding['id']!r}: unit is not the vocabulary unit")
        if finding.get("value_status") == "reported" and not _is_number(finding.get("value")):
            raise ComparisonError(f"finding {finding['id']!r}: reported without a numeric value")
        picked.append(finding)

    def order(finding: Finding) -> tuple[int, str, str]:
        inv = finding["investigation_id"]
        return (wanted.index(inv) if wanted is not None else 0, inv, finding["id"])

    return sorted(picked, key=order)


def _row(finding: Finding) -> dict[str, Any]:
    status = finding["value_status"]
    row: dict[str, Any] = {
        "investigation_id": finding["investigation_id"],
        "finding_id": finding["id"],
        "evidence_class": "measured",
        "value": finding["value"] if status == "reported" else None,  # S9: never anything else
        "value_status": status,
        "conditions": dict(finding["conditions"]),
    }
    for key in ("test_id", "test_outcome"):  # the finding's own fields, copied, never inferred
        if key in finding:
            row[key] = finding[key]
    return row


def _show(value: Any) -> str:
    return f"{value:g}" if _is_number(value) else str(value)


def _condition_reasons(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons = []
    for key in sorted({k for row in rows for k in row["conditions"]}):
        values = [row["conditions"].get(key) for row in rows]
        distinct: list[Any] = []
        for value in values:
            if value is not None and value not in distinct:
                distinct.append(value)
        if len(distinct) > 1:
            shown = ", ".join(sorted(_show(v) for v in distinct))
            reasons.append(f"condition {key} differs across rows: {shown}")
        elif distinct and any(value is None for value in values):
            missing = ", ".join(
                r["finding_id"] for r, v in zip(rows, values, strict=True) if v is None
            )
            reasons.append(
                f"condition {key} is reported for some rows and not for others ({missing})"
            )
    return reasons


def _outcome_reasons(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons = []
    outcomes = [_text(row.get("test_outcome")) for row in rows]
    for row, outcome in zip(rows, outcomes, strict=True):
        if _text(row.get("test_id")) and outcome is None:
            reasons.append(
                f"{row['finding_id']}: the test is identified but its outcome is not reported"
            )
    reported = sorted({o for o in outcomes if o})
    if reported and any(o is None for o in outcomes):
        reasons.append("test outcome is reported for some rows and not for others")
    if len(reported) > 1:
        reasons.append(f"rows report different test outcomes: {', '.join(reported)}")
    return reasons


def build_comparison(
    store: EvidenceStore,
    quantity: str,
    unit: str,
    investigation_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """A contract `Comparison` for `quantity`. `unit` is the vocabulary unit of the quantity.

    `investigation_ids` restricts the rows to those investigations, in that order; None means
    every investigation. Raises `ComparisonError` if accepted evidence breaks an invariant.
    """
    rows = [_row(f) for f in _select(store, quantity, unit, investigation_ids)]
    reasons: list[str] = []

    if investigation_ids is not None:
        present = {row["investigation_id"] for row in rows}
        for inv in investigation_ids:
            if inv not in present:
                reasons.append(f"{inv} has no measured finding for {quantity}")
    if len(rows) < 2:
        reasons.append(f"fewer than two measured findings for {quantity}: nothing to compare")

    for row in rows:
        why = _STATUS_REASON.get(row["value_status"])
        if row["value_status"] != "reported":
            reasons.append(f"{row['finding_id']}: {why or 'the value is not reported'}")

    reasons += _condition_reasons(rows)
    reasons += _outcome_reasons(rows)

    return {
        "contract_version": CONTRACT_VERSION,
        "quantity": quantity,
        "unit": unit,
        "rows": rows,
        "comparable": not reasons,
        "non_comparable_reasons": reasons,
    }
