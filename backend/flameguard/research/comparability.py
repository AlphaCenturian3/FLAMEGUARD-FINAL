"""Scientific comparability gate for numerical comparisons.

Implements rule S5 of the contract v0.2.0 proposal and, by default, one stricter rule:

S5 (always):
- every record is ``measured`` evidence with the same ``quantity`` and ``unit``
  (units are never converted);
- every value is ``reported`` (a missing value is never filled in);
- a condition key reported with different values across records breaks comparability;
- a condition key reported for some records and ``null`` for others breaks it too.

Strict mode (default, Member 5 proposal for Member 1 review):
- a *core* condition (gravity, oxygen, pressure, flow configuration, fuel) that no
  record reports also breaks comparability, because equality cannot be established.

Any numerical operation on evidence must go through ``require_comparable``.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from flameguard.research.common import CONDITION_KEYS
from flameguard.research.evidence import Record

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


def check_comparability(records: Sequence[Record], *, strict: bool = True) -> ComparabilityResult:
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
        if r.get("evidence_category") != "measured":
            reasons.append(
                f"{rid}: only measured evidence can be compared numerically "
                f"(got {r.get('evidence_category')!r})"
            )
        if r.get("value_status") != "reported":
            reasons.append(
                f"{rid}: value is {r.get('value_status')}; missing values are not filled"
            )
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
        if known and len(known) < len(values):
            reasons.append(f"condition '{key}' is reported for some records and missing for others")
        elif len(set(map(repr, known))) > 1:
            reasons.append(f"condition '{key}' differs: {sorted(set(map(repr, known)))}")
        elif strict and not known and key in CORE_CONDITION_KEYS and records:
            reasons.append(
                f"condition '{key}' is not reported for any record; equality cannot be established"
            )
    return ComparabilityResult(not reasons, tuple(reasons), quantity, unit)


def require_comparable(records: Sequence[Record], *, strict: bool = True) -> ComparabilityResult:
    """Like ``check_comparability`` but raises ``IncomparableEvidenceError`` on failure."""
    result = check_comparability(records, strict=strict)
    if not result.comparable:
        raise IncomparableEvidenceError(result.reasons)
    return result


def numeric_difference(a: Record, b: Record, *, strict: bool = True) -> float:
    """Return ``b.value - a.value``, only after the comparability gate passes."""
    require_comparable([a, b], strict=strict)
    return float(b["value"]) - float(a["value"])
