"""±0.05 weight-sensitivity method (D-01 condition 3), on synthetic fixtures only."""

import math
from pathlib import Path

import pytest
from research_sensitivity import (
    CRITERIA,
    DELTA,
    assess,
    load_fixture,
    markdown,
    perturbed_weights,
    ranking,
)

DOC = (
    Path(__file__).resolve().parents[2] / "docs" / "research" / "member5" / "WEIGHT_SENSITIVITY.md"
)


@pytest.fixture
def fx():
    return load_fixture()


def test_fixture_is_marked_synthetic_and_uses_proposed_weights(fx):
    assert fx["fixture"] is True
    assert "NOT NASA DATA" in fx["note"]
    assert fx["weights"] == {
        "purpose_relevance": 0.40,
        "condition_match": 0.25,
        "source_traceability": 0.20,
        "data_completeness": 0.15,
    }
    for scenario in fx["scenarios"].values():
        assert all(inv.startswith("synthetic-") for inv in scenario["criterion_scores"])


@pytest.mark.parametrize("criterion", CRITERIA)
@pytest.mark.parametrize("delta", [DELTA, -DELTA])
def test_perturbation_renormalizes_and_preserves_other_ratios(fx, criterion, delta):
    base = fx["weights"]
    w = perturbed_weights(base, criterion, delta)
    assert math.isclose(sum(w.values()), 1.0, abs_tol=1e-12)
    assert math.isclose(w[criterion], (base[criterion] + delta) / (1 + delta), abs_tol=1e-12)
    others = [c for c in CRITERIA if c != criterion]
    for a, b in zip(others, others[1:], strict=False):
        assert math.isclose(w[a] / w[b], base[a] / base[b], rel_tol=1e-12)


def test_eight_scenarios_and_contributions_add_up(fx):
    for scenario in fx["scenarios"].values():
        m = scenario["criterion_scores"]
        r = assess(m, fx["weights"])
        assert len(r["scenarios"]) == 8
        for inv, parts in r["contributions"].items():
            assert math.isclose(sum(parts.values()), r["baseline_scores"][inv], abs_tol=1e-12)
        for s in r["scenarios"]:
            assert s["order"] == ranking(s["scores"])


def test_verdicts_on_synthetic_scenarios(fx):
    w = fx["weights"]
    stable = assess(fx["scenarios"]["well-separated"]["criterion_scores"], w)
    assert stable["weight_sensitive"] is False
    assert all(s["max_rank_shift"] == 0 for s in stable["scenarios"])
    sensitive = assess(fx["scenarios"]["documentation-trade-off"]["criterion_scores"], w)
    assert sensitive["weight_sensitive"] is True
    changed = {(s["criterion"], s["delta"]) for s in sensitive["scenarios"] if s["top3_changed"]}
    assert changed == {
        ("purpose_relevance", -DELTA),
        ("condition_match", DELTA),
        ("source_traceability", DELTA),
        ("data_completeness", DELTA),
    }
    # Documentation weight can put an investigation with no condition match first.
    assert sensitive["baseline_order"][0] == "synthetic-q"


def test_negative_weight_is_refused():
    with pytest.raises(ValueError, match="negative"):
        perturbed_weights(
            {c: (1.0 if c == CRITERIA[0] else 0.0) for c in CRITERIA}, CRITERIA[1], -DELTA
        )


def test_document_tables_match_the_code(fx):
    doc = DOC.read_text(encoding="utf-8")
    for name, scenario in fx["scenarios"].items():
        assert markdown(name, scenario["criterion_scores"], fx["weights"]) in doc
    assert "No NASA data is used" in doc
