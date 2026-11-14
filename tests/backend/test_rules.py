"""Pure cross-file rules (S3 and transitive S9), tested without any files.

Findings are minimal synthetic dicts: only the keys the rules read.
"""

from flameguard.data.rules import analyze, exclusion_notes, parents_of

NOTE = "SYNTHETIC exclusion reason."


def measured(fid):
    return {"id": fid, "evidence_class": "measured", "value_status": "reported"}


def excluded(fid):
    return {
        "id": fid,
        "evidence_class": "measured",
        "value_status": "excluded",
        "curation_notes": [
            {"kind": "exclusion", "note": NOTE},
            {"kind": "caution", "note": "other"},
        ],
    }


def interp(fid, parents, **extra):
    f = {
        "id": fid,
        "evidence_class": "interpretation",
        "value_status": "not_applicable",
        "value": None,
        "quantity": None,
        "provenance": {"derived_from": parents},
        "limitations": [f"Explains: {NOTE}"],
    }
    f.update(extra)
    return f


def run(*findings):
    return analyze({f["id"]: f for f in findings})


def test_empty_input():
    a = run()
    assert a.problems == {} and a.exclusion_dependent == frozenset() and a.excluded == frozenset()


def test_parents_only_come_from_interpretations():
    assert parents_of(interp("i", ["a", "b"])) == ("a", "b")
    assert parents_of({**measured("m"), "provenance": {"derived_from": ["x"]}}) == ()


def test_exclusion_notes_keeps_only_exclusion_kind():
    assert exclusion_notes(excluded("e")) == (NOTE,)


def test_unresolved_parent_is_a_problem():
    a = run(interp("i", ["ghost"]))
    assert "does not resolve" in a.problems["i"][0]


def test_cycles_are_problems_for_every_member():
    a = run(interp("a", ["b"]), interp("b", ["c"]), interp("c", ["a"]))
    assert set(a.problems) == {"a", "b", "c"}
    assert all("cycle" in p[0] for p in a.problems.values())


def test_self_cycle_is_a_problem():
    assert "cycle" in run(interp("a", ["a"])).problems["a"][0]


def test_dependents_of_an_invalid_finding_are_invalid():
    """Propagation: validity is not decided per finding in isolation."""
    a = run(
        measured("m"), interp("bad", ["ghost"]), interp("d1", ["m", "bad"]), interp("d2", ["d1"])
    )
    assert "depends on invalid finding" in a.problems["d1"][0]
    assert "depends on invalid finding" in a.problems["d2"][0]
    assert "m" not in a.problems


def test_dependents_of_a_cycle_are_invalid():
    a = run(interp("a", ["b"]), interp("b", ["a"]), interp("d", ["a"]))
    assert "d" in a.problems


def test_invalid_chains_are_never_reported_as_exclusion_dependent():
    a = run(excluded("e"), interp("bad", ["e", "ghost"]))
    assert "bad" in a.problems and "bad" not in a.exclusion_dependent


def test_exclusion_dependence_is_transitive_and_includes_the_excluded_finding():
    a = run(
        excluded("e"),
        measured("m"),
        interp("i1", ["e"]),
        interp("i2", ["i1"]),
        interp("i3", ["m", "i2"]),
        interp("clean", ["m"]),
    )
    assert a.exclusion_dependent == {"e", "i1", "i2", "i3"}
    assert a.excluded == {"e"} and a.problems == {}


def test_valid_explanations_have_no_problems():
    assert run(excluded("e"), interp("i", ["e"])).problems == {}


def test_s9_value_and_quantity_are_problems():
    for extra in ({"value": 1.0}, {"quantity": "flame_length"}):
        assert "carries a value" in run(excluded("e"), interp("i", ["e"], **extra)).problems["i"][0]


def test_s9_environment_tag_is_a_problem():
    a = run(excluded("e"), interp("i", ["e"], relevant_environments=["lunar_base"]))
    assert "tagged for an environment" in a.problems["i"][0]


def test_s9_limitation_must_contain_the_exact_note_not_a_keyword():
    for lim in (["excluded"], ["Not exclusive; excluding outliers."], []):
        a = run(excluded("e"), interp("i", ["e"], limitations=lim))
        assert "quote the exclusion note" in a.problems["i"][0]


def test_s9_note_may_come_from_any_excluded_ancestor_at_depth():
    a = run(excluded("e"), interp("i1", ["e"]), interp("i2", ["i1"], limitations=[f"x {NOTE}"]))
    assert a.problems == {}


def test_s9_does_not_constrain_clean_interpretations():
    a = run(
        measured("m"),
        interp("i", ["m"], value=2.0, limitations=[], relevant_environments=["lunar_base"]),
    )
    assert a.problems == {}


def test_s9_does_not_apply_to_the_excluded_measured_finding_itself():
    assert run(excluded("e")).problems == {}


def test_an_s9_violation_removes_the_finding_from_the_dependent_set():
    a = run(excluded("e"), interp("i", ["e"], value=1.0))
    assert "i" in a.problems and "i" not in a.exclusion_dependent
