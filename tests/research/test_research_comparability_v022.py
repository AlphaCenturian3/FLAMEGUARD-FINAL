"""Member 5 reference S5: numeric equality, v0.2.2 outcome rules (opt-in), differential checks.

SYNTHETIC records only (``fixture: true`` copies from tests/fixtures/research). Not NASA data.

Regression for audit finding D11 (PR #37 review): the reference used ``repr`` to compare
condition values, so ``760`` and ``760.0`` "differed" while B3 (correctly) treated them as one
value. The reference also predated the v0.2.2 test-outcome rules. Contract v0.2.2 (PR #17) is
still an unapproved proposal, so those rules are opt-in (``outcome_rules=True``); the default
stays the merged v0.2.0 S5.

The differential test against B3 runs only when ``flameguard.compare`` (PR #37) is importable;
on branches without B3 it is skipped, never silently passed.
"""

import itertools
import random

import pytest
from research.common import CONDITION_KEYS
from research.comparability import check_comparability, require_comparable

SEED = 20261115  # recorded seed for every randomised check in this file


def with_cond(fx, key, va, vb):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    a["conditions"][key], b["conditions"][key] = va, vb
    return [a, b]


def with_outcomes(fx, ta, oa, tb, ob):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    a.update(test_id=ta, test_outcome=oa)
    b.update(test_id=tb, test_outcome=ob)
    return [a, b]


# --- numeric equality is by value, still exact ---------------------------------------------


@pytest.mark.parametrize(
    ("key", "va", "vb"),
    [
        ("pressure_kpa", 760, 760.0),
        ("flow_velocity_mm_s", 0, -0.0),
        ("flow_velocity_mm_s", 0.0, -0.0),
        ("oxygen_mole_fraction", 0.21, 0.21),
    ],
)
def test_numerically_equal_condition_values_are_one_value(fx, key, va, vb):
    result = check_comparability(with_cond(fx, key, va, vb))
    assert result.comparable, result.reasons


@pytest.mark.parametrize(
    ("key", "va", "vb"),
    [
        ("oxygen_mole_fraction", 0.21, 0.2100001),  # no tolerance
        ("pressure_kpa", 760 * 0.133322387415, 760 * 133.322387415 / 1000),  # 1 ulp apart
        ("pressure_kpa", 101.3, 101.325),
        ("fuel_or_material", "Methanol", "Methanol "),  # whitespace counts
        ("fuel_or_material", "Heptane", "heptane"),  # case counts
        ("fuel_or_material", "Heptane", "n-heptane"),
        ("pressure_kpa", 101.325, "101.325"),  # a number never equals text
        ("pressure_kpa", float("nan"), float("nan")),  # non-finite equals nothing
    ],
)
def test_condition_equality_stays_exact_and_conservative(fx, key, va, vb):
    result = check_comparability(with_cond(fx, key, va, vb))
    assert not result.comparable
    assert any(f"'{key}' differs" in r for r in result.reasons), result.reasons


def test_a_differing_reason_shows_each_value_exactly(fx):
    p1, p2 = 760 * 0.133322387415, 760 * 133.322387415 / 1000
    (reason,) = check_comparability(with_cond(fx, "pressure_kpa", p1, p2)).reasons
    assert repr(p1) in reason and repr(p2) in reason  # never rounded to look identical


# --- null conditions: current S5 versus the strict proposal --------------------------------


def test_a_condition_null_for_every_record_gives_no_reason_in_s5(fx):
    recs = [fx("fixture-a-1"), fx("fixture-a-2")]
    for r in recs:
        r["conditions"] = dict.fromkeys(CONDITION_KEYS)
    assert check_comparability(recs).comparable  # contract v0.2.2 behaviour
    strict = check_comparability(recs, strict=True)  # proposal only
    assert not strict.comparable
    assert sum("not reported for any record" in r for r in strict.reasons) == 5


def test_a_condition_null_for_some_records_breaks_comparability(fx):
    result = check_comparability(with_cond(fx, "diluent", "N2 0.79", None))
    assert not result.comparable
    assert any("'diluent' is reported for some records and missing" in r for r in result.reasons)


# --- S5 v0.2.2 test identity and outcome (opt-in until PR #17 is approved) -----------------


def test_the_default_follows_the_merged_contract_and_ignores_outcomes(fx):
    recs = with_outcomes(fx, "T-1", "Extinction", "T-2", "Disruption")
    assert check_comparability(recs).comparable  # merged v0.2.0 has no outcome rule
    assert not check_comparability(recs, outcome_rules=True).comparable


def test_same_outcome_on_identified_tests_is_comparable(fx):
    result = check_comparability(
        with_outcomes(fx, "T-1", "Extinction", "T-2", "Extinction"), outcome_rules=True
    )
    assert result.comparable, result.reasons


def test_different_outcomes_break_comparability(fx):
    result = check_comparability(
        with_outcomes(fx, "T-1", "Extinction", "T-2", "Disruption"), outcome_rules=True
    )
    assert not result.comparable
    assert "records report different test outcomes: ['Disruption', 'Extinction']" in result.reasons


@pytest.mark.parametrize("missing", [None, ""])
def test_an_identified_test_without_its_outcome_breaks_comparability(fx, missing):
    result = check_comparability(
        with_outcomes(fx, "T-1", "Extinction", "T-2", missing), outcome_rules=True
    )
    assert not result.comparable
    text = " | ".join(result.reasons)
    assert "'T-2' is identified but its outcome is not reported" in text
    assert "reported for some records and not for others" in text


def test_identified_tests_without_any_outcome_break_comparability(fx):
    result = check_comparability(with_outcomes(fx, "T-1", None, "T-2", None), outcome_rules=True)
    assert not result.comparable
    assert sum("outcome is not reported" in r for r in result.reasons) == 2


def test_an_outcome_without_a_test_id_breaks_comparability(fx):
    result = check_comparability(
        with_outcomes(fx, None, "Extinction", None, "Extinction"), outcome_rules=True
    )
    assert not result.comparable
    assert sum("identifies no test (S11)" in r for r in result.reasons) == 2


def test_mixed_identity_breaks_comparability(fx):
    result = check_comparability(
        with_outcomes(fx, "T-1", "Extinction", None, None), outcome_rules=True
    )
    assert not result.comparable


def test_records_without_any_test_identity_follow_conditions_only(fx):
    assert check_comparability(
        with_outcomes(fx, None, None, None, None), outcome_rules=True
    ).comparable


def test_an_outcome_is_never_inferred_from_prose(fx):
    recs = with_outcomes(fx, "T-1", "Extinction", "T-2", None)
    recs[1]["statement"] = "SYNTHETIC: the flame showed Extinction."
    assert not check_comparability(recs, outcome_rules=True).comparable


# --- values: excluded, missing, non-finite --------------------------------------------------


@pytest.mark.parametrize("status", ["excluded", "not_reported", "not_applicable"])
def test_a_non_reported_value_is_never_comparable(fx, status):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    b.update(value=None, value_status=status)
    result = check_comparability([a, b])
    assert not result.comparable
    assert any(status in r for r in result.reasons)


def test_an_excluded_value_never_appears_in_reasons(fx):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    b.update(value=987654.321, value_status="excluded")  # schema-invalid on purpose
    result = check_comparability([a, b])
    assert not result.comparable
    assert not any("987654" in r for r in result.reasons)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, "1.0", None])
def test_a_reported_value_must_be_a_finite_number(fx, bad):
    a, b = fx("fixture-a-1"), fx("fixture-a-2")
    b["value"] = bad
    result = check_comparability([a, b])
    assert not result.comparable
    assert any("finite number" in r for r in result.reasons)
    with pytest.raises(ValueError):
        require_comparable([a, b])


# --- differential: independent brute-force S5 statement, recorded seed ----------------------

_COND_CHOICES = {
    "gravity_environment": ["microgravity", "normal_gravity", None],
    "oxygen_mole_fraction": [0.21, 0.2100001, None],
    "pressure_kpa": [101.3250144354, 760 * 0.133322387415, 101, 101.0, None],
    "flow_velocity_mm_s": [0, 0.0, -0.0, 5, None],
    "flow_configuration": ["opposed", None],
    "diluent": ["N2 0.79", "N2 0.79 ", None],
    "fuel_or_material": ["Methanol", "methanol", None],
    "sample_geometry": [None, "droplet"],
}
# (test_id, test_outcome) per record; outcome-without-id is excluded (the loader rejects it).
_IDENTITY = [(None, None), ("T-1", None), ("T-1", "Extinction"), ("T-2", "Disruption")]
_STATUS = ["reported", "reported", "reported", "excluded", "not_reported"]


def _brute_s5(recs):
    """Second, deliberately naive statement of S5 with the v0.2.2 outcome rules (no shared code)."""
    if len(recs) < 2 or any(r["value_status"] != "reported" for r in recs):
        return False
    for key in CONDITION_KEYS:
        vals = [r["conditions"][key] for r in recs]
        rep = [v for v in vals if v is not None]
        if rep and len(rep) != len(vals):
            return False
        for x, y in itertools.combinations(rep, 2):
            if isinstance(x, str) != isinstance(y, str) or x != y:
                return False
    outs = [r.get("test_outcome") or None for r in recs]
    if any((r.get("test_id") or None) and o is None for r, o in zip(recs, outs, strict=True)):
        return False
    if any(o is None for o in outs) and any(o is not None for o in outs):
        return False
    return len({o for o in outs if o}) <= 1


def _random_records(rng, template, perturb=0.15):
    """Records share a random base and each field is re-drawn with probability ``perturb``,
    so the sweep reaches both comparable and non-comparable answers."""
    base_cond = {k: rng.choice(v) for k, v in _COND_CHOICES.items()}
    base_identity = rng.choice(_IDENTITY)
    recs = []
    for i in range(rng.choice([2, 2, 3])):
        r = dict(template)
        r["id"], r["investigation_id"] = f"fixture-r-{i}", f"fixture-inv-{i}"
        r["conditions"] = {
            k: rng.choice(v) if rng.random() < perturb else base_cond[k]
            for k, v in _COND_CHOICES.items()
        }
        r["value_status"] = rng.choice(_STATUS) if rng.random() < perturb else "reported"
        r["value"] = 1.0 if r["value_status"] == "reported" else None
        identity = rng.choice(_IDENTITY) if rng.random() < perturb else base_identity
        r["test_id"], r["test_outcome"] = identity
        recs.append(r)
    return recs


def test_reference_agrees_with_an_independent_brute_force_s5(fx):
    rng = random.Random(SEED)  # noqa: S311 (seeded, reproducible, not cryptographic)
    template = fx("fixture-a-1")
    agree = comparable = 0
    for _ in range(5000):
        recs = _random_records(rng, template)
        ours = check_comparability(recs, outcome_rules=True).comparable
        assert ours == _brute_s5(recs), recs
        agree += 1
        comparable += ours
    assert agree == 5000 and comparable > 0  # the sweep reaches both answers


def test_reference_agrees_with_b3_engine_when_available(fx):
    """Differential against Member 1's B3 (PR #37). Skipped where B3 is not on the branch."""
    compare = pytest.importorskip("flameguard.compare")
    from types import MappingProxyType

    from flameguard.data.loader import EvidenceStore

    rng = random.Random(SEED)  # noqa: S311 (seeded, reproducible, not cryptographic)
    template = fx("fixture-a-1")
    template.pop("evidence_category")
    template["evidence_class"] = "measured"
    disagreements = []
    for _ in range(20000):
        recs = _random_records(rng, template)
        store = EvidenceStore(findings=MappingProxyType({r["id"]: r for r in recs}))
        b3 = compare.build_comparison(store, template["quantity"], template["unit"])
        if b3["comparable"] != check_comparability(recs, outcome_rules=True).comparable:
            disagreements.append(recs)
    assert disagreements == []
