"""Scientific evidence records: structure, validation and explicit missing-data reporting.

A record is a plain JSON-compatible dict, so it can sit next to contract objects. Fields:

=====================  =====================================================================
``id``                 Record id (contract id pattern).
``investigation_id``   Investigation the record belongs to.
``test_id``            Test-level identifier from the source, or ``None`` if not identified.
``evidence_category``  ``measured`` | ``reported`` | ``interpreted`` (see below).
``statement``          What the record says, in plain language.
``quantity``           Vocabulary key, or ``None`` for a qualitative statement.
``value`` / ``unit``   Value as reported. ``None`` when missing. Never estimated.
``value_status``       ``reported`` | ``not_reported`` | ``not_applicable`` | ``excluded``.
``uncertainty``        As reported by the source, or ``None``.
``conditions``         Every key in ``CONDITION_KEYS``; ``None`` = not reported.
``sources``            Contract ``Source`` objects (title, url, page, quote, retrieved,
                       archive_id).
``doi``                DOI if the source has one, else ``None``.
``locator``            Where in the source (table/row/page/file line). Required if measured.
``manifest_id``        Manifest entry holding the value. Required if measured.
``derived_from``       Record ids an interpretation is built on. Required if interpreted.
``method``             Interpretation method and version. Required if interpreted.
``interpretation``     FlameGuard-SI reading of the evidence, or ``None``.
``limitations``        At least one experimental limitation.
``relevant_environments``  Contract environment keys.
``extrapolation_warning``  Required when a lunar or Martian environment is listed.
``fire_safety_topics`` Contract topic keys.
``source_claim_strength``  For ``reported`` records: ``experimental_result`` |
                       ``stated_objective`` | ``hypothesis_under_test`` |
                       ``source_statement``. Required for reported records.
``curation_notes``    For measured records: FlameGuard-SI cautions or exclusions attributed
                       to a quality flag and its recorded source passage.
``fixture``            ``True`` only for test fixtures (never NASA data).
=====================  =====================================================================

Evidence categories:

- ``measured``: a value taken from a NASA experimental record, traceable to a manifest
  entry and a locator. Maps to contract ``measured``.
- ``reported``: a qualitative statement quoted exactly from a NASA source (objective,
  stated result, stated hypothesis). It carries no numeric value. The contract has no
  class for it yet; see ``contract_evidence_class``.
- ``interpreted``: a FlameGuard-SI interpretation built on other records. Maps to
  contract ``interpretation``.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from research.common import (
    CONDITION_KEYS,
    DATE_RE,
    DOI_RE,
    ENVIRONMENTS,
    EVIDENCE_CATEGORIES,
    EXTRAPOLATED_ENVIRONMENTS,
    FIRE_SAFETY_TOPICS,
    FLOW_CONFIGURATIONS,
    GENERATED_BY,
    GRAVITY_ENVIRONMENTS,
    ID_RE,
    URL_RE,
    VALUE_STATUSES,
    VOCABULARY,
    banned_phrases_in,
)

Record = Mapping[str, Any]

REQUIRED_FIELDS = (
    "id",
    "investigation_id",
    "test_id",
    "evidence_category",
    "statement",
    "quantity",
    "value",
    "unit",
    "value_status",
    "conditions",
    "sources",
    "doi",
    "limitations",
    "relevant_environments",
)

SOURCE_CLAIM_STRENGTHS = (
    "experimental_result",
    "stated_objective",
    "hypothesis_under_test",
    "source_statement",
)

#: Text fields checked for banned phrases.
_TEXT_FIELDS = ("statement", "interpretation", "extrapolation_warning")


def contract_evidence_class(category: str) -> str | None:
    """Map a Member 5 category to the contract ``evidence_class``.

    Returns ``None`` for ``reported``: contract v0.2.0 has no class for a quoted
    qualitative source statement. Forcing it into ``measured`` would overstate it, so the
    decision is left to Members 1 and 3 (see docs/research/member5/COORDINATION.md).
    """
    return {"measured": "measured", "interpreted": "interpretation"}.get(category)


def validate_source(source: Any, where: str) -> list[str]:
    """Check one contract ``Source`` object."""
    if not isinstance(source, Mapping):
        return [f"{where}: source must be an object"]
    errors = []
    allowed = {"title", "url", "page", "quote", "retrieved", "archive_id"}
    extra = set(source) - allowed
    if extra:
        errors.append(f"{where}: unknown source keys {sorted(extra)}")
    if not isinstance(source.get("title"), str) or not source["title"].strip():
        errors.append(f"{where}: source title is required")
    if not isinstance(source.get("url"), str) or not URL_RE.match(source["url"]):
        errors.append(f"{where}: source url must be http(s)")
    if not isinstance(source.get("retrieved"), str) or not DATE_RE.match(source["retrieved"]):
        errors.append(f"{where}: source retrieved must be YYYY-MM-DD")
    quote = source.get("quote")
    if quote is not None and (not isinstance(quote, str) or not quote.strip()):
        errors.append(f"{where}: quote must be non-empty text or null")
    return errors


def validate_evidence(record: Any) -> list[str]:
    """Return every rule the record breaks. An empty list means the record is valid."""
    if not isinstance(record, Mapping):
        return ["record must be an object"]
    rid = record.get("id", "<no id>")
    errors = [f"{rid}: missing field '{f}'" for f in REQUIRED_FIELDS if f not in record]
    if errors:
        return errors

    category = record["evidence_category"]
    if category not in EVIDENCE_CATEGORIES:
        # Simulations and anything else are rejected outright.
        return [f"{rid}: evidence_category must be one of {EVIDENCE_CATEGORIES}"]
    for key in ("id", "investigation_id"):
        if not isinstance(record[key], str) or not ID_RE.match(record[key]):
            errors.append(f"{rid}: {key} must match the contract id pattern")
    if record["test_id"] is not None and not (
        isinstance(record["test_id"], str) and record["test_id"].strip()
    ):
        errors.append(f"{rid}: test_id must be non-empty text or null")
    if not isinstance(record["statement"], str) or not record["statement"].strip():
        errors.append(f"{rid}: statement is required")

    errors += _validate_value(record, rid)
    errors += _validate_conditions(record.get("conditions"), rid)
    errors += _validate_curation_notes(record, rid)

    if record["value_status"] == "excluded":
        if category != "measured":
            errors.append(f"{rid}: excluded values must be measured evidence")
        if record["quantity"] is None:
            errors.append(f"{rid}: excluded measurements must retain their quantity")
        notes = record.get("curation_notes")
        if not isinstance(notes, list) or not any(
            isinstance(note, Mapping) and note.get("kind") == "exclusion" for note in notes
        ):
            errors.append(f"{rid}: excluded values need an attributed exclusion note")

    sources = record["sources"]
    if not isinstance(sources, list):
        errors.append(f"{rid}: sources must be a list")
        sources = []
    for i, src in enumerate(sources):
        errors += validate_source(src, f"{rid}.sources[{i}]")
    if record["doi"] is not None and not (
        isinstance(record["doi"], str) and DOI_RE.match(record["doi"])
    ):
        errors.append(f"{rid}: doi must look like 10.xxxx/... or be null")

    if category == "measured":
        if not sources:
            errors.append(f"{rid}: measured evidence needs at least one source")
        for key in ("manifest_id", "locator"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                errors.append(f"{rid}: measured evidence needs '{key}'")
    elif category == "reported":
        if not sources or not any(isinstance(s, Mapping) and s.get("quote") for s in sources):
            errors.append(f"{rid}: reported evidence needs a source with an exact quote")
        if record.get("source_claim_strength") not in SOURCE_CLAIM_STRENGTHS:
            errors.append(
                f"{rid}: reported evidence needs source_claim_strength in {SOURCE_CLAIM_STRENGTHS}"
            )
        if record["quantity"] is not None or isinstance(record["value"], int | float):
            errors.append(
                f"{rid}: reported evidence is qualitative; numeric values must be "
                "imported as measured evidence with a manifest entry and locator"
            )
    elif category == "interpreted":
        derived = record.get("derived_from")
        if not isinstance(derived, list) or not derived:
            errors.append(f"{rid}: interpreted evidence needs derived_from")
        if not isinstance(record.get("method"), str) or not record["method"].strip():
            errors.append(f"{rid}: interpreted evidence needs a method")
        if record.get("generated_by") != GENERATED_BY:
            errors.append(f"{rid}: interpreted evidence must have generated_by={GENERATED_BY}")

    limitations = record["limitations"]
    if not isinstance(limitations, list) or not any(
        isinstance(x, str) and x.strip() for x in limitations
    ):
        errors.append(f"{rid}: at least one experimental limitation is required")

    envs = record["relevant_environments"]
    if not isinstance(envs, list) or any(e not in ENVIRONMENTS for e in envs):
        errors.append(f"{rid}: relevant_environments must use {ENVIRONMENTS}")
        envs = []
    if EXTRAPOLATED_ENVIRONMENTS.intersection(envs):
        warning = record.get("extrapolation_warning")
        if not isinstance(warning, str) or not warning.strip():
            errors.append(
                f"{rid}: lunar/Martian relevance requires an explicit extrapolation_warning"
            )

    topics = record.get("fire_safety_topics", [])
    if not isinstance(topics, list) or any(t not in FIRE_SAFETY_TOPICS for t in topics):
        errors.append(f"{rid}: fire_safety_topics must use {FIRE_SAFETY_TOPICS}")

    for field in _TEXT_FIELDS:
        text = record.get(field)
        if isinstance(text, str):
            for phrase in banned_phrases_in(text):
                errors.append(f"{rid}: {field} contains banned phrase '{phrase}'")
    return errors


def _validate_curation_notes(record: Record, rid: str) -> list[str]:
    notes = record.get("curation_notes")
    if notes is None:
        return []
    if record["evidence_category"] != "measured":
        return [f"{rid}: curation_notes are allowed only on measured evidence"]
    if not isinstance(notes, list) or not notes:
        return [f"{rid}: curation_notes must be a non-empty list"]

    errors = []
    for i, note in enumerate(notes):
        where = f"{rid}.curation_notes[{i}]"
        if not isinstance(note, Mapping):
            errors.append(f"{where}: note must be an object")
            continue
        if note.get("kind") not in ("caution", "exclusion"):
            errors.append(f"{where}: kind must be 'caution' or 'exclusion'")
        if not isinstance(note.get("note"), str) or not note["note"].strip():
            errors.append(f"{where}: note text is required")
        if note.get("generated_by") != GENERATED_BY:
            errors.append(f"{where}: generated_by must be {GENERATED_BY}")

        flag_ref = note.get("flag_ref")
        if (
            not isinstance(flag_ref, Mapping)
            or set(flag_ref) != {"manifest_id", "flag_id"}
            or not all(isinstance(flag_ref.get(k), str) and flag_ref[k].strip() for k in flag_ref)
        ):
            errors.append(f"{where}: flag_ref needs manifest_id and flag_id")

        source = note.get("source")
        source_errors = validate_source(source, f"{where}.source")
        errors.extend(source_errors)
        if isinstance(source, Mapping) and (
            not isinstance(source.get("quote"), str) or not source["quote"].strip()
        ):
            errors.append(f"{where}: source needs a recorded quote")

    has_exclusion = any(
        isinstance(note, Mapping) and note.get("kind") == "exclusion" for note in notes
    )
    if has_exclusion and record["value_status"] != "excluded":
        errors.append(f"{rid}: an exclusion note requires value_status 'excluded'")
    return errors


def _validate_value(record: Record, rid: str) -> list[str]:
    errors = []
    quantity, value, unit, status = (
        record["quantity"],
        record["value"],
        record["unit"],
        record["value_status"],
    )
    if status not in VALUE_STATUSES:
        return [f"{rid}: value_status must be one of {VALUE_STATUSES}"]
    if status == "reported" and value is None:
        errors.append(f"{rid}: value_status 'reported' needs a value")
    if status != "reported" and value is not None:
        errors.append(f"{rid}: a value that is {status} must be null, never filled in")
    if quantity is None:
        if unit is not None:
            errors.append(f"{rid}: a qualitative record has no unit")
        return errors
    if quantity not in VOCABULARY:
        errors.append(f"{rid}: unknown quantity '{quantity}' (add it via a contract PR)")
        return errors
    if unit != VOCABULARY[quantity]:
        errors.append(f"{rid}: {quantity} must use unit '{VOCABULARY[quantity]}', got {unit!r}")
    if value is not None and (isinstance(value, bool) or not isinstance(value, int | float)):
        errors.append(f"{rid}: {quantity} value must be a number")
    return errors


def _validate_conditions(conditions: Any, rid: str) -> list[str]:
    if not isinstance(conditions, Mapping):
        return [f"{rid}: conditions must be an object"]
    errors = []
    missing = [k for k in CONDITION_KEYS if k not in conditions]
    if missing:
        errors.append(f"{rid}: conditions must list every key (null if not reported): {missing}")
    extra = set(conditions) - set(CONDITION_KEYS)
    if extra:
        errors.append(f"{rid}: unknown condition keys {sorted(extra)} (add via a contract PR)")
    g = conditions.get("gravity_environment")
    if g is not None and g not in GRAVITY_ENVIRONMENTS:
        errors.append(f"{rid}: gravity_environment must be one of {GRAVITY_ENVIRONMENTS}")
    f = conditions.get("flow_configuration")
    if f is not None and f not in FLOW_CONFIGURATIONS:
        errors.append(f"{rid}: flow_configuration must be one of {FLOW_CONFIGURATIONS}")
    o2 = conditions.get("oxygen_mole_fraction")
    if o2 is not None and not (isinstance(o2, int | float) and 0 <= o2 <= 1):
        errors.append(f"{rid}: oxygen_mole_fraction must be within 0..1")
    for key in ("pressure_kpa", "flow_velocity_mm_s"):
        v = conditions.get(key)
        if v is not None and not (isinstance(v, int | float) and v >= 0):
            errors.append(f"{rid}: {key} must be a non-negative number")
    return errors


def missing_fields(record: Record) -> list[str]:
    """List every field the record leaves missing, so the UI can show it explicitly."""
    missing = []
    if record.get("test_id") is None:
        missing.append("test_id")
    if record.get("doi") is None:
        missing.append("doi")
    conditions = record.get("conditions") or {}
    missing += [f"conditions.{k}" for k in CONDITION_KEYS if conditions.get(k) is None]
    if record.get("quantity") is not None:
        if record.get("value_status") != "reported":
            missing.append("value")
        if record.get("uncertainty") is None:
            missing.append("uncertainty")
    return missing


def index_records(records: Iterable[Record]) -> dict[str, Record]:
    """Index records by id, refusing duplicate ids."""
    index: dict[str, Record] = {}
    for rec in records:
        rid = rec["id"]
        if rid in index:
            raise ValueError(f"duplicate evidence id '{rid}'")
        index[rid] = rec
    return index


def exclusion_dependent_ids(records: Iterable[Record]) -> set[str]:
    """Find excluded findings and every interpretation derived from them.

    Broken provenance is rejected rather than treated as independent evidence.
    """
    index = index_records(records)
    state: dict[str, bool] = {}
    visiting: set[str] = set()

    def depends(record_id: str) -> bool:
        if record_id in state:
            return state[record_id]
        if record_id not in index:
            raise ValueError(f"unresolved derived_from id {record_id!r}")
        if record_id in visiting:
            raise ValueError(f"derived_from cycle through {record_id!r}")

        visiting.add(record_id)
        record = index[record_id]
        parents = record.get("derived_from") or []
        dependent = record.get("value_status") == "excluded"
        if record.get("evidence_category") == "interpreted":
            for parent_id in parents:
                parent_dependent = depends(parent_id)
                dependent = parent_dependent or dependent
        visiting.remove(record_id)
        state[record_id] = dependent
        return dependent

    return {record_id for record_id in index if depends(record_id)}
