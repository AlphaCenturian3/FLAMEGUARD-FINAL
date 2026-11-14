"""Moon/Mars fire-safety insight cards.

Each card follows one chain, and every link is required:

    Finding -> NASA source -> Interpretation -> Moon/Mars implication -> Limitation

Claim types keep observations apart from hypotheses:

- ``finding.claim_type``: ``measured`` or ``source_reported`` (what the source says).
- ``finding.strength``: ``experimental_result`` | ``stated_objective`` |
  ``hypothesis_under_test`` | ``source_statement``. A hypothesis is never shown as a
  result: an ``experimental_result`` card may only cite reported records whose
  ``source_claim_strength`` is also ``experimental_result``.
- ``interpretation.claim_type`` is always ``flameguard_interpretation``.
- ``implication.claim_type`` is always ``engineering_hypothesis``.

Cards are qualitative. ``disclaimer`` must equal ``NOT_FLIGHT_QUALIFIED`` and
``review_status`` starts as ``draft_pending_scientific_review``.

``presentation`` says how a card may be shown (Member 1 review on PR #3, D-05):

- ``accepted_pending_curation``: accepted as a future R3 interpretation once Member 3
  curates its evidence as measured qualitative findings. Its finding must be an
  ``experimental_result``. ``pending_on`` names what it waits for.
- ``pending_measured_data``: may become R3 only after verified measured data exists
  (``pending_on`` names it). Not shown as a finding until then.
- ``research_context``: an open research question built on objectives, hypotheses or
  source statements. Never shown as a FlameGuard-SI finding; ``open_question`` is
  required and its finding cannot be an ``experimental_result``.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from flameguard.research.common import (
    ENVIRONMENTS,
    EXTRAPOLATED_ENVIRONMENTS,
    ID_RE,
    NOT_FLIGHT_QUALIFIED,
    banned_phrases_in,
)
from flameguard.research.evidence import Record

THEMES = (
    "material_selection",
    "ventilation_flow",
    "detection_monitoring",
    "lunar_partial_gravity",
    "martian_extrapolation",
    "fuel_extinction_suppression",
)
FINDING_CLAIM_TYPES = ("measured", "source_reported")
FINDING_STRENGTHS = (
    "experimental_result",
    "stated_objective",
    "hypothesis_under_test",
    "source_statement",
)
#: ``member1_changes_applied``: Member 1's review was applied by Member 5; Member 1 has
#: not yet confirmed the new wording. ``wording_confirmed_by_member1``: Member 1 confirmed
#: the wording matches the review; this is NOT approval of the evidence (Member 1, PR #3
#: comment 6883984161). ``reviewed_by_member1`` is kept for a future evidence approval.
REVIEW_STATUSES = (
    "draft_pending_scientific_review",
    "member1_changes_applied",
    "wording_confirmed_by_member1",
    "reviewed_by_member1",
    "withdrawn",
)
PRESENTATIONS = ("accepted_pending_curation", "pending_measured_data", "research_context")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_card(card: Any, evidence: Mapping[str, Record]) -> list[str]:
    """Return every rule ``card`` breaks. ``evidence`` maps record id -> record."""
    if not isinstance(card, Mapping):
        return ["card must be an object"]
    cid = card.get("id", "<no id>")
    errors: list[str] = []
    if not isinstance(card.get("id"), str) or not ID_RE.match(card["id"]):
        errors.append(f"{cid}: id must match the contract id pattern")
    if card.get("theme") not in THEMES:
        errors.append(f"{cid}: theme must be one of {THEMES}")
    if not _text(card.get("title")):
        errors.append(f"{cid}: title is required")
    if card.get("review_status") not in REVIEW_STATUSES:
        errors.append(f"{cid}: review_status must be one of {REVIEW_STATUSES}")
    if card.get("disclaimer") != NOT_FLIGHT_QUALIFIED:
        errors.append(f"{cid}: disclaimer must state the card is not flight-qualified")

    finding = card.get("finding") or {}
    presentation = card.get("presentation")
    if presentation not in PRESENTATIONS:
        errors.append(f"{cid}: presentation must be one of {PRESENTATIONS}")
    if presentation in ("accepted_pending_curation", "pending_measured_data") and not _text(
        card.get("pending_on")
    ):
        errors.append(f"{cid}: a pending card must say what it waits for in pending_on")
    if presentation == "accepted_pending_curation" and (
        finding.get("strength") != "experimental_result"
    ):
        errors.append(f"{cid}: accepted_pending_curation needs an experimental_result finding")
    if presentation == "research_context":
        if not _text(card.get("open_question")):
            errors.append(f"{cid}: research_context cards need an open_question")
        if finding.get("strength") == "experimental_result":
            errors.append(f"{cid}: research_context cannot present an experimental result")
    if not _text(finding.get("statement")):
        errors.append(f"{cid}: finding.statement is required")
    if finding.get("claim_type") not in FINDING_CLAIM_TYPES:
        errors.append(f"{cid}: finding.claim_type must be one of {FINDING_CLAIM_TYPES}")
    if finding.get("strength") not in FINDING_STRENGTHS:
        errors.append(f"{cid}: finding.strength must be one of {FINDING_STRENGTHS}")
    ids = finding.get("evidence_ids") or []
    if not ids:
        errors.append(f"{cid}: finding must cite at least one evidence record (NASA source)")
    for eid in ids:
        rec = evidence.get(eid)
        if rec is None:
            errors.append(f"{cid}: evidence '{eid}' does not exist")
            continue
        if not any(s.get("quote") and s.get("url") for s in rec.get("sources", [])):
            errors.append(f"{cid}: evidence '{eid}' has no source with a URL and exact quote")
        if finding.get("claim_type") == "measured" and rec.get("evidence_category") != "measured":
            errors.append(
                f"{cid}: finding claims 'measured' but '{eid}' is "
                f"{rec.get('evidence_category')} evidence"
            )
        if (
            finding.get("strength") == "experimental_result"
            and rec.get("evidence_category") == "reported"
            and rec.get("source_claim_strength") != "experimental_result"
        ):
            errors.append(
                f"{cid}: '{eid}' is not a reported experimental result, so the finding "
                "cannot be presented as one"
            )

    interp = card.get("interpretation") or {}
    if not _text(interp.get("text")):
        errors.append(f"{cid}: interpretation.text is required")
    if interp.get("claim_type") != "flameguard_interpretation":
        errors.append(f"{cid}: interpretation.claim_type must be 'flameguard_interpretation'")

    impl = card.get("implication") or {}
    envs = impl.get("environments") or []
    if not _text(impl.get("text")):
        errors.append(f"{cid}: implication.text is required")
    if impl.get("claim_type") != "engineering_hypothesis":
        errors.append(f"{cid}: implication.claim_type must be 'engineering_hypothesis'")
    if not envs or any(e not in ENVIRONMENTS for e in envs):
        errors.append(f"{cid}: implication.environments must use {ENVIRONMENTS}")
    if EXTRAPOLATED_ENVIRONMENTS.intersection(envs) and not _text(
        impl.get("extrapolation_warning")
    ):
        errors.append(f"{cid}: lunar/Martian implication needs an extrapolation_warning")

    limitations = card.get("limitations")
    if not isinstance(limitations, list) or not any(_text(x) for x in limitations):
        errors.append(f"{cid}: at least one limitation is required")

    for where, text in _texts(card):
        for phrase in banned_phrases_in(text):
            errors.append(f"{cid}: {where} contains banned phrase '{phrase}'")
    return errors


def _texts(card: Mapping[str, Any]) -> list[tuple[str, str]]:
    out = [("title", card.get("title")), ("open_question", card.get("open_question"))]
    out.append(("finding.statement", (card.get("finding") or {}).get("statement")))
    out.append(("interpretation.text", (card.get("interpretation") or {}).get("text")))
    impl = card.get("implication") or {}
    out += [("implication.text", impl.get("text"))]
    out += [("implication.extrapolation_warning", impl.get("extrapolation_warning"))]
    out += [("limitations", x) for x in card.get("limitations") or []]
    return [(w, t) for w, t in out if isinstance(t, str)]


def validate_cards(cards: Sequence[Any], evidence: Mapping[str, Record]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for card in cards:
        cid = card.get("id") if isinstance(card, Mapping) else None
        if cid in seen:
            errors.append(f"duplicate card id '{cid}'")
        seen.add(cid)
        errors += validate_card(card, evidence)
    return errors


def themes_covered(cards: Sequence[Mapping[str, Any]]) -> set[str]:
    return {c.get("theme") for c in cards if c.get("review_status") != "withdrawn"}
