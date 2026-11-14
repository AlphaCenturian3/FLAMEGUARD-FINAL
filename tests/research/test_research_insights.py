"""Moon/Mars insight cards: full evidence chain, claim types, extrapolation warnings."""

import copy

from flameguard.research.common import NOT_FLIGHT_QUALIFIED
from flameguard.research.evidence import index_records
from flameguard.research.insights import THEMES, themes_covered, validate_card, validate_cards


def test_real_cards_are_valid_and_cover_every_theme(real_cards, real_evidence):
    evidence = index_records(real_evidence)
    assert validate_cards(real_cards, evidence) == []
    assert themes_covered(real_cards) == set(THEMES)


def test_every_card_has_the_full_chain(real_cards, real_evidence):
    evidence = index_records(real_evidence)
    for card in real_cards:
        assert card["finding"]["statement"]
        assert card["finding"]["evidence_ids"]
        for eid in card["finding"]["evidence_ids"]:
            assert any(s["quote"] for s in evidence[eid]["sources"])
        assert card["interpretation"]["claim_type"] == "flameguard_interpretation"
        assert card["implication"]["claim_type"] == "engineering_hypothesis"
        assert card["limitations"]
        assert card["disclaimer"] == NOT_FLIGHT_QUALIFIED
        assert card["review_status"] == "draft_pending_scientific_review"


def test_lunar_and_martian_cards_carry_extrapolation_warnings(real_cards):
    for card in real_cards:
        envs = set(card["implication"]["environments"])
        if envs & {"lunar_base", "martian_base"}:
            assert card["implication"]["extrapolation_warning"].strip()


def test_hypothesis_cannot_be_presented_as_a_result(real_cards, real_evidence):
    evidence = index_records(real_evidence)
    card = copy.deepcopy(next(c for c in real_cards if c["theme"] == "lunar_partial_gravity"))
    assert card["finding"]["strength"] == "hypothesis_under_test"
    card["finding"]["strength"] = "experimental_result"
    assert any("not a reported experimental result" in e for e in validate_card(card, evidence))


def test_reported_evidence_cannot_be_called_measured(real_cards, real_evidence):
    evidence = index_records(real_evidence)
    card = copy.deepcopy(real_cards[0])
    card["finding"]["claim_type"] = "measured"
    assert any("claims 'measured'" in e for e in validate_card(card, evidence))


def test_broken_cards_are_rejected(real_cards, real_evidence):
    evidence = index_records(real_evidence)
    base = next(c for c in real_cards if c["theme"] == "martian_extrapolation")
    cases = {
        "limitation": lambda c: c.update(limitations=[]),
        "does not exist": lambda c: c["finding"].update(evidence_ids=["m5-missing"]),
        "at least one evidence": lambda c: c["finding"].update(evidence_ids=[]),
        "extrapolation_warning": lambda c: c["implication"].pop("extrapolation_warning"),
        "engineering_hypothesis": lambda c: c["implication"].update(claim_type="finding"),
        "not flight-qualified": lambda c: c.update(disclaimer="Safe to fly."),
        "banned phrase": lambda c: c["interpretation"].update(
            text="According to NASA, this habitat is certified safe."
        ),
    }
    for expected, mutate in cases.items():
        card = copy.deepcopy(base)
        mutate(card)
        errors = validate_card(card, evidence)
        assert any(expected in e for e in errors), (expected, errors)
