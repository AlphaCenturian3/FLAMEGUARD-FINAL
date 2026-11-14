"""Research-relevance ranking: transparency, purpose dependence and release gating.

Fixture results test mechanics only. They are not findings.
"""

import math
from pathlib import Path

import pytest

from flameguard.research.common import NOT_A_RISK_SCORE
from flameguard.research.ranking import (
    EXPECTED_CRITERIA,
    RankingInputError,
    load_criteria,
    rank_investigations,
    validate_criteria,
)

CRITERIA_FILE = (
    Path(__file__).resolve().parents[2] / "config" / "research_relevance_criteria_v1.proposed.json"
)

LUNAR_MATERIALS = {
    "text": "Which investigations inform solid-material flammability for a lunar habitat?",
    "target_environment": "lunar_base",
    "topics": ["material_flammability"],
    "quantities": ["flame_spread_rate"],
    "conditions": {
        "gravity_environment": "microgravity",
        "oxygen_mole_fraction": {"min": 0.19, "max": 0.30},
    },
}

EARTH_EXTINCTION = {
    "text": "Which investigations report extinction or ignition behaviour in normal gravity?",
    "target_environment": "earth",
    "topics": ["extinction", "ignition"],
    "conditions": {"gravity_environment": "normal_gravity", "flow_configuration": "opposed"},
}


def _rank(question, fixtures, criteria, **kw):
    return rank_investigations(question, fixtures, criteria, allow_fixtures=True, **kw)


def test_proposed_criteria_file_matches_the_brief(criteria):
    assert validate_criteria(criteria) == []
    assert criteria["status"] == "proposed" and criteria["approved_by"] == []
    weights = {c["id"]: c["weight"] for c in criteria["criteria"]}
    assert weights == {
        "purpose_relevance": 0.40,
        "condition_match": 0.25,
        "source_traceability": 0.20,
        "data_completeness": 0.15,
    }
    assert "not a fire-danger" in criteria["purpose"]
    assert load_criteria(CRITERIA_FILE)["criteria_version"] == "research_relevance_v1"


def test_ranking_satisfies_contract_rule_s6(fixtures, criteria):
    out = _rank(LUNAR_MATERIALS, fixtures, criteria)
    ranking = out["ranking"]
    weights = {c["id"]: c["weight"] for c in ranking["criteria"]}
    assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9)
    ids = {r["id"]: r for r in fixtures}
    items = ranking["items"]
    assert [it["rank"] for it in items] == list(range(1, len(items) + 1))
    assert [it["score"] for it in items] == sorted((it["score"] for it in items), reverse=True)
    for it in items:
        assert [c["criterion_id"] for c in it["criterion_scores"]] == list(EXPECTED_CRITERIA)
        total = sum(weights[c["criterion_id"]] * c["score"] for c in it["criterion_scores"])
        assert abs(it["score"] - total) <= 1e-9
        assert 0 <= it["score"] <= 1
        for c in it["criterion_scores"]:
            if c["score"] > 0:
                assert c["inputs"], c
            for inp in c["inputs"]:
                assert inp["finding_id"] in ids
                assert inp["evidence_class"] in ("measured", "interpretation")
    ranked = {it["investigation_id"] for it in items}
    assert ranked.isdisjoint({e["investigation_id"] for e in ranking["excluded"]})


def test_every_output_says_it_is_not_a_risk_score(fixtures, criteria):
    out = _rank(LUNAR_MATERIALS, fixtures, criteria)
    assert out["disclaimer"] == NOT_A_RISK_SCORE
    for it in out["ranking"]["items"]:
        assert "not fire risk" in it["rationale"]


def test_ranking_depends_on_the_research_purpose(fixtures, criteria):
    lunar = _rank(LUNAR_MATERIALS, fixtures, criteria)["ranking"]["items"]
    earth = _rank(EARTH_EXTINCTION, fixtures, criteria)["ranking"]["items"]
    assert lunar[0]["investigation_id"] == "fixture-inv-a"
    assert earth[0]["investigation_id"] == "fixture-inv-b"


def test_explanations_show_components_and_missing_evidence(fixtures, criteria):
    out = _rank(LUNAR_MATERIALS, fixtures, criteria)
    b = out["explanations"]["fixture-inv-b"]
    assert set(b["criteria"]) == set(EXPECTED_CRITERIA)
    for part in b["criteria"].values():
        assert part["weighted"] == pytest.approx(part["weight"] * part["score"])
    cond = b["criteria"]["condition_match"]
    assert "oxygen_mole_fraction" in cond["missing"]
    assert "gravity_environment" in cond["unmatched"]
    assert "conditions.oxygen_mole_fraction" in b["missing_evidence"]["fixture-b-1"]


def test_reported_only_investigation_is_excluded_with_reason(fixtures, criteria):
    out = _rank(LUNAR_MATERIALS, fixtures, criteria)
    excluded = {e["investigation_id"]: e["reason"] for e in out["ranking"]["excluded"]}
    assert "context only" in excluded["fixture-inv-d"]


def test_interpretation_traceability_is_inherited(fixtures, criteria):
    out = _rank(LUNAR_MATERIALS, fixtures, criteria)
    trace = out["explanations"]["fixture-inv-c"]["criteria"]["source_traceability"]
    # fixture-a-1 is fully traceable; the second parent does not resolve and counts as 0.
    assert trace["per_record"]["fixture-c-1"] == pytest.approx(0.5)


def test_no_conditions_means_not_assessed_not_neutral(fixtures, criteria):
    q = {**LUNAR_MATERIALS, "conditions": {}}
    out = _rank(q, fixtures, criteria)
    for exp in out["explanations"].values():
        part = exp["criteria"]["condition_match"]
        assert part["score"] == 0 and "not assessed" in part["notes"][0]


def test_fixture_rankings_are_never_released(fixtures, criteria):
    approved = {**criteria, "status": "approved", "approved_by": ["reviewer"]}
    out = _rank(LUNAR_MATERIALS, fixtures, approved)
    assert out["release_status"] == "fixture_demo_only"
    assert out["ranking"]["fixture"] is True


def test_fixtures_are_refused_outside_tests(fixtures, criteria):
    out = rank_investigations(LUNAR_MATERIALS, fixtures, criteria)
    assert out["ranking"]["items"] == []
    assert len(out["excluded_records"]) == len(fixtures)


def test_simulations_are_rejected(fx, criteria):
    sim = fx("fixture-a-1")
    sim["evidence_category"] = "illustrative_simulation"
    with pytest.raises(RankingInputError, match="simulation"):
        _rank(LUNAR_MATERIALS, [sim], criteria)
    labelled = fx("fixture-a-1")
    labelled["label"] = "Fluid and thermal transport model. No combustion chemistry."
    with pytest.raises(RankingInputError, match="simulation"):
        _rank(LUNAR_MATERIALS, [labelled], criteria)


def test_fixture_and_real_records_cannot_be_ranked_together(fx, real_evidence, criteria):
    with pytest.raises(RankingInputError, match="together"):
        _rank(LUNAR_MATERIALS, [fx("fixture-a-1"), *real_evidence], criteria)


def test_real_register_yields_no_fabricated_ranking(real_evidence, register, criteria):
    out = rank_investigations(
        LUNAR_MATERIALS,
        real_evidence,
        criteria,
        investigation_ids=[i["id"] for i in register],
    )
    assert out["ranking"]["items"] == []
    assert out["release_status"] == "provisional_not_for_release"
    excluded = {e["investigation_id"] for e in out["ranking"]["excluded"]}
    assert excluded == {"bass-ii", "flex", "sofie", "saffire", "fm2"}
    assert out["excluded_records"] == []


def test_release_requires_approved_criteria(fx, criteria):
    real = fx("fixture-a-1")
    real.pop("fixture")
    assert rank_investigations(LUNAR_MATERIALS, [real], criteria)["release_status"] == (
        "provisional_not_for_release"
    )
    approved = {**criteria, "status": "approved", "approved_by": ["Member 1"]}
    assert rank_investigations(LUNAR_MATERIALS, [real], approved)["release_status"] == "released"
    unnamed = {**criteria, "status": "approved", "approved_by": []}
    with pytest.raises(RankingInputError, match="reviewers"):
        rank_investigations(LUNAR_MATERIALS, [real], unnamed)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"topics": [], "quantities": []}, "at least one topic"),
        ({"target_environment": "venus"}, "target_environment"),
        ({"conditions": {"gravity_g": 1}}, "unknown condition"),
        ({"conditions": {"pressure_kpa": {"min": 5, "max": 1}}}, "min <= max"),
    ],
)
def test_invalid_questions_are_rejected(fixtures, criteria, change, message):
    with pytest.raises(RankingInputError, match=message):
        _rank({**LUNAR_MATERIALS, **change}, fixtures, criteria)


def test_bad_weights_are_rejected(criteria):
    bad = {**criteria, "criteria": [dict(c) for c in criteria["criteria"]]}
    bad["criteria"][0]["weight"] = 0.5
    assert any("sum to 1" in e for e in validate_criteria(bad))
