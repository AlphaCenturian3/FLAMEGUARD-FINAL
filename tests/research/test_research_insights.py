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
        # Member 1 confirmed the wording only (PR #3 comment 6883984161), not the evidence.
        assert card["review_status"] == "wording_confirmed_by_member1"
        assert "Not an approval" in card["member1_review"]["wording_confirmation"]


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


# --- Member 1 scientific review (PR #3 comment 6883406826), applied by Member 5 ---


def _cards_by_id(real_cards):
    return {c["id"]: c for c in real_cards}


def test_presentation_follows_member1_review(real_cards):
    p = {c["id"]: c["presentation"] for c in real_cards}
    assert p == {
        "card-ventilation-flow": "accepted_pending_curation",
        "card-detection-monitoring": "accepted_pending_curation",
        "card-fuel-extinction-suppression": "pending_measured_data",
        "card-material-selection": "research_context",
        "card-lunar-partial-gravity": "research_context",
        "card-martian-extrapolation": "research_context",
    }
    for card in real_cards:
        assert card["member1_review"]["applied"].strip()


def test_ventilation_evidence_keeps_only_the_observational_clause(real_evidence):
    rec = next(r for r in real_evidence if r["id"] == "m5-bass2-flow-flareup")
    quote = rec["sources"][0]["quote"]
    assert quote == "they can flare up quickly with a sudden increase in air flow speed."
    for text in (quote, rec["statement"]):
        assert "dangerous" not in text and "dim" not in text


def test_detection_card_does_not_compare_across_units(real_cards):
    card = _cards_by_id(real_cards)["card-detection-monitoring"]
    text = " ".join([card["title"], card["interpretation"]["text"], card["implication"]["text"]])
    assert "larger signal" not in text
    assert "less significant than the increase in carbon dioxide and carbon monoxide" in text
    assert any("uncrewed" in lim and "habitat" in lim for lim in card["limitations"])


def test_flex_card_waits_for_data_and_states_pre_dilution(real_cards):
    card = _cards_by_id(real_cards)["card-fuel-extinction-suppression"]
    assert "PR #4" in card["pending_on"] and "C4" in card["pending_on"]
    assert card["presentation"] == "pending_measured_data"
    assert "pre-diluted" in card["interpretation"]["text"]
    # Verified against the FLEX report (NASA/TP-2015-216046) and cited as its own evidence.
    assert "m5-flex-prediluted-ambient" in card["finding"]["evidence_ids"]
    assert any("Verified by Member 5" in lim for lim in card["limitations"])
    assert not any("not yet checked" in lim for lim in card["limitations"])


def test_context_cards_are_open_questions_and_name_non_nasa_authors(real_cards, real_evidence):
    cards = _cards_by_id(real_cards)
    for cid in (
        "card-material-selection",
        "card-lunar-partial-gravity",
        "card-martian-extrapolation",
    ):
        assert cards[cid]["open_question"].strip()
        assert cards[cid]["finding"]["strength"] != "experimental_result"
    assert cards["card-lunar-partial-gravity"]["title"].startswith("Hypothesis under test")
    assert "Liao" in cards["card-martian-extrapolation"]["finding"]["statement"]
    wp = next(r for r in real_evidence if r["id"] == "m5-partial-gravity-not-interpolated")
    assert "Liao" in wp["statement"] and "hosted by NASA states" not in wp["statement"]


def test_presentation_rules_are_enforced(real_cards, real_evidence):
    evidence = index_records(real_evidence)
    cards = _cards_by_id(real_cards)
    ctx = copy.deepcopy(cards["card-material-selection"])
    ctx.pop("open_question")
    assert any("open_question" in e for e in validate_card(ctx, evidence))
    ctx = copy.deepcopy(cards["card-lunar-partial-gravity"])
    ctx["finding"]["strength"] = "experimental_result"
    assert any("cannot present an experimental result" in e for e in validate_card(ctx, evidence))
    pend = copy.deepcopy(cards["card-ventilation-flow"])
    pend.pop("pending_on")
    assert any("pending_on" in e for e in validate_card(pend, evidence))
    acc = copy.deepcopy(cards["card-ventilation-flow"])
    acc["finding"]["strength"] = "stated_objective"
    assert any("needs an experimental_result" in e for e in validate_card(acc, evidence))
    bad = copy.deepcopy(cards["card-ventilation-flow"])
    bad["presentation"] = "finding"
    assert any("presentation must be" in e for e in validate_card(bad, evidence))
