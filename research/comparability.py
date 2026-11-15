"""Research-only reference for the contract's scientific comparability rules.

Implements rule S5 of the merged contract (v0.2.0) by default. Two opt-in modes are kept
separate from it:

- ``outcome_rules=True`` adds the test-identity and outcome rules of the contract v0.2.2
  PROPOSAL (PR #17, open and unapproved as of 2026-11-15). B3 (PR #37) implements v0.2.2, so
  the differential check against B3 uses this mode. It becomes the default only after v0.2.2
  is approved and merged.
- ``strict=True`` is Member 5's stricter research proposal (below). It is not contract
  behaviour.

S5 (always):
- every record is ``measured`` evidence with the same ``quantity`` and ``unit``
  (units are never converted);
- every value is ``reported`` (a missing value is never filled in) and, when reported, a
  finite number;
- a condition key reported with different values across records breaks comparability;
- a condition key reported for some records and ``null`` for others breaks it too;
- a condition key that is ``null`` for every record gives no reason (contract S5; blocking
  it is the strict-mode proposal below).

Condition equality is exact and conservative. Numbers are compared by numeric value, so
``760`` and ``760.0`` are one value, and so are ``0`` and ``-0.0``; there is no tolerance, so
``0.21`` and ``0.2100001`` differ. Text is compared exactly (case and whitespace count). A
number never equals a text value, and a non-finite number equals nothing.

Test identity and outcome (``outcome_rules=True``; S5 v0.2.2 proposal and S11), read only
from ``test_id`` and ``test_outcome`` (absent, ``None`` and ``""`` all mean not reported;
never inferred from prose or values):
- a record with a ``test_id`` but no ``test_outcome`` breaks comparability;
- outcomes reported for some records and not for others break it;
- records reporting different outcomes break it;
- a record with a ``test_outcome`` but no ``test_id`` breaks it (S11: an outcome needs an
  identified test; the B1 loader rejects such a finding before it reaches B3).

Strict mode (opt-in with ``strict=True``; Member 5 proposal, NOT contract behaviour):
- a *core* condition (gravity, oxygen, pressure, flow configuration, fuel) that no
  record reports also breaks comparability, because equality cannot be established.
  This core set is under revision: Member 5 has proposed (PR #38 review) that the core be
  defined per experiment class, because FLEX droplet tests leave ``flow_configuration``
  null. Until the owners decide, this set is unchanged.

Any numerical operation on evidence must go through ``require_comparable``.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from research.common import CONDITION_KEYS
from research.evidence import Record

CORE_CONDITION_KEYS: tuple[str, ...] = (
    "gravity_environment",
    "oxygen_mole_fraction",
    "pressure_kpa",
    "flow_configuration",
    "fuel_or_material",
)


class IncomparableEvidenceError(ValueError):
    """Raised when a numerical comparison is requested on incomparable evidence."""

    def __init__(self, reasons: Sequence[str]):
        self.reasons = tuple(reasons)
        super().__init__("Evidence is not comparable: " + "; ".join(self.reasons))


@dataclass(frozen=True)
class ComparabilityResult:
    comparable: bool
    reasons: tuple[str, ...]
    quantity: str | None
    unit: str | None


def check_comparability(
    records: Sequence[Record], *, strict: bool = False, outcome_rules: bool = False
) -> ComparabilityResult:
    """Decide whether ``records`` can be compared numerically, giving one reason per problem."""
    reasons: list[str] = []
    if len(records) < 2:
        reasons.append("at least two records are needed for a comparison")

    quantities = {r.get("quantity") for r in records}
    units = {r.get("unit") for r in records}
    quantity = next(iter(quantities)) if len(quantities) == 1 else None
    unit = next(iter(units)) if len(units) == 1 else None

    for r in records:
        rid = r.get("id", "<no id>")
        category = _category(r)
        if category != "measured":
            reasons.append(
                f"{rid}: only measured evidence can be compared numerically (got {category!r})"
            )
        if r.get("value_status") != "reported":
            reasons.append(
                f"{rid}: value is {r.get('value_status')}; missing values are not filled"
            )
        elif not _is_finite_number(r.get("value")):
            reasons.append(f"{rid}: a reported value must be a finite number")
    if None in quantities:
        reasons.append("a qualitative record (no quantity) cannot be compared numerically")
    if len(quantities) > 1:
        reasons.append(f"different quantities: {sorted(map(str, quantities))}")
    if len(units) > 1:
        reasons.append(f"different units {sorted(map(str, units))}; units are never converted")
    if len({bool(r.get("fixture")) for r in records}) > 1:
        reasons.append("fixture records cannot be compared with real records")

    for key in CONDITION_KEYS:
        values = [(r.get("conditions") or {}).get(key) for r in records]
        known = [v for v in values if v is not None]
        distinct: list[object] = []
        for v in known:
            if not any(_same_condition_value(v, d) for d in distinct):
                distinct.append(v)
        if known and len(known) < len(values):
            reasons.append(f"condition '{key}' is reported for some records and missing for others")
        elif len(distinct) > 1:
            reasons.append(f"condition '{key}' differs: {sorted(map(repr, distinct))}")
        elif strict and not known and key in CORE_CONDITION_KEYS and records:
            reasons.append(
                f"condition '{key}' is not reported for any record; equality cannot be established"
            )

    if outcome_rules:
        reasons.extend(_outcome_reasons(records))
    return ComparabilityResult(not reasons, tuple(reasons), quantity, unit)


def _category(record: Record) -> object:
    """Research ``evidence_category``, or the contract's ``evidence_class`` for a Finding."""
    if "evidence_category" in record:
        return record["evidence_category"]
    return record.get("evidence_class")


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_finite_number(value: object) -> bool:
    return _is_number(value) and math.isfinite(value)


def _same_condition_value(a: object, b: object) -> bool:
    """Exact, conservative equality of two reported condition values (no tolerance)."""
    if _is_number(a) or _is_number(b):
        return _is_finite_number(a) and _is_finite_number(b) and a == b
    return type(a) is type(b) and a == b


def _reported_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _outcome_reasons(records: Sequence[Record]) -> list[str]:
    """S5 v0.2.2 test identity and outcome rules, plus the S11 outcome-needs-test rule."""
    reasons: list[str] = []
    outcomes = [_reported_text(r.get("test_outcome")) for r in records]
    for r, outcome in zip(records, outcomes, strict=True):
        rid = r.get("id", "<no id>")
        test_id = _reported_text(r.get("test_id"))
        if test_id and outcome is None:
            reasons.append(f"{rid}: test {test_id!r} is identified but its outcome is not reported")
        if outcome and not test_id:
            reasons.append(f"{rid}: reports a test outcome but identifies no test (S11)")
    reported = sorted({o for o in outcomes if o})
    if reported and any(o is None for o in outcomes):
        reasons.append("test outcome is reported for some records and not for others")
    if len(reported) > 1:
        reasons.append(f"records report different test outcomes: {reported}")
    return reasons


def require_comparable(
    records: Sequence[Record], *, strict: bool = False, outcome_rules: bool = False
) -> ComparabilityResult:
    """Like ``check_comparability`` but raises ``IncomparableEvidenceError`` on failure."""
    result = check_comparability(records, strict=strict, outcome_rules=outcome_rules)
    if not result.comparable:
        raise IncomparableEvidenceError(result.reasons)
    return result


def numeric_difference(
    a: Record, b: Record, *, strict: bool = False, outcome_rules: bool = False
) -> float:
    """Return ``b.value - a.value``, only after the comparability gate passes."""
    require_comparable([a, b], strict=strict, outcome_rules=outcome_rules)
    return float(b["value"]) - float(a["value"])
