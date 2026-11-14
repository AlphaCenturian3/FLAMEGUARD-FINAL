"""Shared vocabulary for the research package.

The quantity vocabulary, condition keys, environments and topics mirror the contract
v0.2.0 *proposal* (PR #1, branch ``contract/cp1-v0.2-proposal``), which is not merged.
If that proposal changes, update this file in the same PR. New keys must go through a
contract PR first (CP1 plan, rule D5); do not add them here on their own.
"""

import re

TARGET_CONTRACT = "0.2.0"

#: Quantity key -> required unit (contracts/vocabulary.json in the v0.2.0 proposal).
VOCABULARY: dict[str, str] = {
    "flame_spread_rate": "mm/s",
    "extinction_oxygen_mole_fraction": "1",
    "ignition_delay": "s",
    "flame_length": "mm",
    "flame_temperature": "K",
}

#: Every key must be present on a record; ``None`` means "not reported by the source".
CONDITION_KEYS: tuple[str, ...] = (
    "gravity_environment",
    "oxygen_mole_fraction",
    "pressure_kpa",
    "flow_velocity_mm_s",
    "flow_configuration",
    "diluent",
    "fuel_or_material",
    "sample_geometry",
)

GRAVITY_ENVIRONMENTS = ("microgravity", "partial_gravity", "normal_gravity")
FLOW_CONFIGURATIONS = ("opposed", "concurrent", "quiescent")

ENVIRONMENTS: tuple[str, ...] = (
    "spacecraft",
    "space_station",
    "lunar_base",
    "martian_base",
    "pressurized_rover",
    "earth",
)

#: Environments for which every claim needs an explicit extrapolation warning.
EXTRAPOLATED_ENVIRONMENTS = frozenset({"lunar_base", "martian_base"})

FIRE_SAFETY_TOPICS: tuple[str, ...] = (
    "prevention",
    "detection",
    "suppression",
    "material_flammability",
    "ignition",
    "extinction",
    "other",
)

VALUE_STATUSES = ("reported", "not_reported", "not_applicable")

#: Member 5 evidence categories. See ``evidence.contract_evidence_class`` for the mapping
#: to the contract's ``evidence_class``.
EVIDENCE_CATEGORIES = ("measured", "reported", "interpreted")

GENERATED_BY = "FlameGuard-SI"

NOT_A_RISK_SCORE = (
    "Research-relevance score: how well the evidence matches the stated research "
    "question. It is not a fire-danger, fire-risk or hazard score, and not a probability."
)

NOT_FLIGHT_QUALIFIED = (
    "Qualitative research insight for discussion. Not a flight-qualified or certified "
    "fire-safety recommendation."
)

#: Phrases generated text must never contain (spec 2.4 and Member 5 safeguards).
BANNED_PHRASES: tuple[str, ...] = (
    "according to nasa",
    "flight-qualified recommendation",
    "flight qualified recommendation",
    "certified safe",
    "nasa-certified",
    "nasa certified",
    "probability of fire",
    "fire probability",
    "risk probability",
)

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://\S+$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def banned_phrases_in(text: str) -> list[str]:
    """Return every banned phrase found in ``text`` (case-insensitive)."""
    lowered = text.lower()
    return [p for p in BANNED_PHRASES if p in lowered]
