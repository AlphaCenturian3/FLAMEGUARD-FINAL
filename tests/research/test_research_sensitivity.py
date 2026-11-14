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


# --- Applicability-dominance invariant (Member 1, PR #3 comment 6883984161) ---


def _dominates(w_c, w_t, w_d, delta_min):
    return w_c * delta_min > w_t + w_d


def test_original_weights_fail_the_invariant_for_any_delta_up_to_one(fx):
    w = fx["weights"]
    for delta_min in (1.0, 0.5, 1 / 3, 0.1):
        assert not _dominates(
            w["condition_match"], w["source_traceability"], w["data_completeness"], delta_min
        )
    # Removing purpose_relevance and rescaling keeps C : (T + D) = 0.25 : 0.35, so it fails too.
    rest = w["condition_match"] + w["source_traceability"] + w["data_completeness"]
    c, t, d = (w[k] / rest for k in ("condition_match", "source_traceability", "data_completeness"))
    assert math.isclose(c, 0.25 / 0.60) and not _dominates(c, t, d, 1.0)


@pytest.mark.parametrize(("delta_min", "bound"), [(1.0, 0.5), (1 / 3, 0.75)])
def test_invariant_bound_on_w_c(delta_min, bound):
    # With w_C + w_T + w_D = 1, the invariant is w_C > 1 / (1 + delta_min).
    assert math.isclose(1 / (1 + delta_min), bound)
    eps = 1e-6
    assert _dominates(bound + eps, (1 - bound - eps) / 2, (1 - bound - eps) / 2, delta_min)
    assert not _dominates(bound, (1 - bound) / 2, (1 - bound) / 2, delta_min)


def test_document_records_the_invariant_without_proposing_weights():
    doc = DOC.read_text(encoding="utf-8")
    assert "w_C · Δ_min > w_T + w_D" in doc
    assert "No replacement weight set is proposed here." in doc
    assert "not validation on NASA measurements" in doc
    assert "superseded four-criterion structure" in doc
