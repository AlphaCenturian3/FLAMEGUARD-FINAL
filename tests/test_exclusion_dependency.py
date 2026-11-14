"""Transitive exclusion protection (rule S9, CP1 Option (a)).

A finding is *exclusion-dependent* if it is `excluded`, or if any `derived_from` ancestor at
any depth is `excluded`. An exclusion-dependent interpretation may exist only to explain an
exclusion. It never supports a ranking, a comparison, a TARS evidence-based conclusion or a
Moon/Mars recommendation, and it never carries the excluded number as a usable value.

`exclusion_violations` below is a CONTRACT TEST ORACLE, not runtime code, and it is a LOWER
BOUND. In contract v0.2 a citation is not linked to a sentence or a role, so no contract test
can prove that a future TARS answer never uses an exclusion-dependent finding as support. That
stays a mandatory runtime acceptance gate for B6 and T1 (Member 1), with Member 5's independent
live-output test (docs/CP1_WORKSTREAMS.md). Member 1 enforces the rule at runtime.

The gap was identified by Member 2 (buihhlong-a11y). The oracle defects corrected here (a dead
number check, and keyword checks) were found by Member 2 and Member 5 on PR #1.
"""

import copy
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"

# A number as written in prose: 0.37, .37, 37, -1.5e3. Not part of a longer token like 1.37.
NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?![\w])")


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def numbers_in(text: str) -> set[Decimal]:
    """Every number written in `text`, as an exact Decimal (so .37 == 0.37 == 0.370)."""
    out = set()
    for token in NUMBER.findall(text):
        try:
            out.add(Decimal(token))
        except InvalidOperation:
            continue
    return out


def exclusion_dependent_ids(findings):
    """Return ids of exclusion-dependent findings. Raise ValueError on a derived_from cycle
    or an unresolved id (both already violate S3), so a broken chain can never pass."""
    by_id = {f["id"]: f for f in findings}
    state: dict[str, bool] = {}
    visiting: set[str] = set()

    def dependent(fid):
        if fid in state:
            return state[fid]
        if fid not in by_id:
            raise ValueError(f"S3: unresolved derived_from id {fid!r}")
        if fid in visiting:
            raise ValueError(f"S3: derived_from cycle through {fid!r}")
        visiting.add(fid)
        f = by_id[fid]
        parents = (
            f.get("provenance", {}).get("derived_from", [])
            if f["evidence_class"] == "interpretation"
            else []
        )
        result = f["value_status"] == "excluded"
        for parent in parents:  # evaluate every parent, so cycles and broken ids are always found
            result = dependent(parent) or result
        visiting.discard(fid)
        state[fid] = result
        return result

    return {fid for fid in by_id if dependent(fid)}


def excluded_ancestors(fid, by_id):
    """The `excluded` findings a finding depends on (itself included). Call only after
    exclusion_dependent_ids() has validated the chain (no cycles, no unresolved ids)."""
    out, seen, stack = set(), set(), [fid]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        f = by_id[cur]
        if f["value_status"] == "excluded":
            out.add(cur)
        if f["evidence_class"] == "interpretation":
            stack.extend(f["provenance"]["derived_from"])
    return out


def exclusion_reasons(fid, by_id):
    """Exact exclusion-note texts of every excluded ancestor of `fid`."""
    return {
        n["note"]
        for anc in excluded_ancestors(fid, by_id)
        for n in by_id[anc].get("curation_notes", [])
        if n["kind"] == "exclusion"
    }


def exclusion_violations(findings, ranking=None, answer=None, comparison=None, printed_values=None):
    """Cross-file S9 checks for one set of documents. Returns human-readable violations.

    printed_values: {excluded finding id: the value exactly as printed in the registered
    source file at its locator}. The excluded number never appears in Finding JSON (its value
    is null), so it must be supplied. A missing printed value FAILS the check, it never passes.
    """
    printed_values = printed_values or {}
    dep = exclusion_dependent_ids(findings)
    by_id = {f["id"]: f for f in findings}
    out = []

    def leaked_numbers(fid, texts, label=None):
        label = label or fid
        stated = set().union(*(numbers_in(t) for t in texts)) if texts else set()
        for anc in sorted(excluded_ancestors(fid, by_id)):
            if anc not in printed_values:
                out.append(f"{label}: printed value of excluded {anc} not supplied; cannot check")
            elif Decimal(printed_values[anc]) in stated:
                out.append(f"{label}: states printed value {printed_values[anc]!r} of {anc}")

    for fid in sorted(dep):
        f = by_id[fid]
        if f["evidence_class"] != "interpretation":
            continue
        if f["value"] is not None or f["quantity"] is not None:
            out.append(f"{fid}: exclusion-dependent interpretation carries a value or quantity")
        if f.get("relevant_environments"):
            out.append(f"{fid}: exclusion-dependent interpretation is tagged for an environment")
        reasons = exclusion_reasons(fid, by_id)
        if not any(r in lim for lim in f.get("limitations", []) for r in reasons):
            out.append(f"{fid}: limitations do not quote the exclusion note it explains")
        leaked_numbers(fid, [f["statement"], *f.get("limitations", [])])

    if ranking:
        for item in ranking["items"]:
            for cs in item["criterion_scores"]:
                for inp in cs["inputs"]:
                    if inp["finding_id"] in dep:
                        out.append(f"ranking input {inp['finding_id']} is exclusion-dependent")

    if comparison and comparison.get("comparable"):
        for row in comparison["rows"]:
            if row["finding_id"] in dep:
                out.append(f"comparable row {row['finding_id']} is exclusion-dependent")

    if answer:
        texts = [answer["answer"], *answer.get("limitations", [])]
        for cit in answer["citations"]:
            cid = cit["finding_id"]
            if cid not in dep:
                continue
            reasons = exclusion_reasons(cid, by_id)
            if not any(r in t for t in texts for r in reasons):
                out.append(f"citation {cid}: answer does not give its exclusion reason")
            leaked_numbers(cid, texts, label=f"answer citation {cid}")
    return out


# --- Fixture chain built from the contract examples (all fixture: true) ------------

EXCLUDED = _load("finding.measured_excluded.example.json")
MEASURED = _load("finding.measured.example.json")
INTERP = _load("finding.interpretation.example.json")
E, M = EXCLUDED["id"], MEASURED["id"]
REASON = next(n["note"] for n in EXCLUDED["curation_notes"] if n["kind"] == "exclusion")
PRINTED = {E: ".37"}  # FIXTURE: what the source file prints at the excluded finding's locator


def _interp(fid, parents, **extra):
    f = copy.deepcopy(INTERP)
    f.update(id=fid, statement=f"FIXTURE interpretation {fid}.")
    f["provenance"] = {**f["provenance"], "derived_from": parents}
    f.pop("relevant_environments", None)
    f["limitations"] = [f"Explains why a value was excluded: {REASON}"]
    f.update(extra)
    return f


def _answer(text, limitations, citations):
    a = copy.deepcopy(_load("assistant_answer.example.json"))
    a.update(answer=text, limitations=limitations)
    src = a["citations"][0]["source"]
    a["citations"] = [
        {"finding_id": c, "evidence_class": "interpretation", "source": src} for c in citations
    ]
    return a


def _violations(*args, **kwargs):
    kwargs.setdefault("printed_values", PRINTED)
    return exclusion_violations(*args, **kwargs)


# --- Transitive dependency (unchanged behaviour) -------------------------------------


def test_direct_dependency():
    assert exclusion_dependent_ids([EXCLUDED, _interp("i1", [E])]) == {E, "i1"}


def test_indirect_dependency():
    fs = [EXCLUDED, _interp("i1", [E]), _interp("i2", ["i1"])]
    assert exclusion_dependent_ids(fs) == {E, "i1", "i2"}


def test_nested_and_mixed_parents():
    fs = [
        EXCLUDED,
        MEASURED,
        _interp("i1", [E]),
        _interp("i2", ["i1"]),
        _interp("i3", ["i2"]),  # depth 3
        _interp("i4", [M, E]),  # one excluded parent is enough
        _interp("i5", [M, "i3"]),  # clean parent plus deep dependent parent
    ]
    assert exclusion_dependent_ids(fs) == {E, "i1", "i2", "i3", "i4", "i5"}


def test_clean_chain_is_not_dependent():
    fs = [MEASURED, _interp("c1", [M]), _interp("c2", ["c1"])]
    assert exclusion_dependent_ids(fs) == set()


@pytest.mark.parametrize(
    "chain",
    [
        [_interp("x", ["x"])],
        [_interp("x", ["y"]), _interp("y", ["x"])],
        [EXCLUDED, _interp("x", [E, "z"]), _interp("y", ["x"]), _interp("z", ["y"])],
    ],
    ids=["self", "two", "behind-excluded"],
)
def test_cycles_are_rejected_not_looped(chain):
    with pytest.raises(ValueError, match="cycle"):
        exclusion_dependent_ids(chain)


def test_unresolved_parent_is_rejected():
    with pytest.raises(ValueError, match="unresolved"):
        exclusion_dependent_ids([_interp("i1", ["missing"])])


def test_ancestors_and_reasons_follow_the_chain():
    fs = [EXCLUDED, MEASURED, _interp("i1", [E]), _interp("i2", [M, "i1"])]
    by_id = {f["id"]: f for f in fs}
    exclusion_dependent_ids(fs)
    assert excluded_ancestors("i2", by_id) == {E}
    assert exclusion_reasons("i2", by_id) == {REASON}


# --- Defect 1 (corrected): the excluded number is checked as printed in the source ---


def test_excluded_value_is_null_in_finding_json():
    """Why the old check was dead: the number S9 protects is never in Finding JSON."""
    assert EXCLUDED["value_status"] == "excluded"
    assert EXCLUDED["value"] is None


def test_numbers_compare_exactly():
    assert Decimal(".37") in numbers_in("the rate was 0.37 mm/s")
    assert Decimal(".37") in numbers_in("it read .37")
    assert Decimal("0.37") in numbers_in("0.370 as printed")
    assert Decimal(".37") not in numbers_in("1.37 and 37 and 0.371 and v0.37a")


@pytest.mark.parametrize(
    "text",
    ["The excluded rate was 0.37.", "Table IX prints .37 here.", "A value of 0.370 was printed."],
    ids=["0.37", ".37", "0.370"],
)
def test_answer_stating_excluded_number_is_caught(text):
    fs = [EXCLUDED, _interp("i1", [E])]
    ans = _answer(f"{text} {REASON}", [], ["i1"])
    assert any("states printed value '.37'" in v for v in _violations(fs, answer=ans))


def test_excluded_number_in_limitations_is_caught():
    fs = [EXCLUDED, _interp("i1", [E])]
    ans = _answer(REASON, ["Note: the table printed 0.37."], ["i1"])
    assert any("states printed value" in v for v in _violations(fs, answer=ans))


def test_dependent_interpretation_stating_excluded_number_is_caught():
    stmt = "FIXTURE: the excluded value .37 is unreliable."
    fs = [EXCLUDED, _interp("i1", [E], statement=stmt)]
    assert any("states printed value" in v for v in _violations(fs))


def test_other_numbers_do_not_trigger():
    fs = [EXCLUDED, _interp("i1", [E])]
    ans = _answer(f"{REASON} Tests ran at 1.37 bar for 37 s.", [], ["i1"])
    assert _violations(fs, answer=ans) == []


def test_missing_printed_value_fails_closed():
    fs = [EXCLUDED, _interp("i1", [E])]
    ans = _answer(REASON, [], ["i1"])
    violations = exclusion_violations(fs, answer=ans)  # no printed_values supplied
    assert any("not supplied; cannot check" in v for v in violations)


# --- Defects 2 and 3 (corrected): structured reasons, per citation ------------------


def test_keyword_limitation_no_longer_clears_a_citation():
    """The old check passed this: one limitation containing 'exclu' cleared every citation."""
    fs = [EXCLUDED, _interp("i1", [E])]
    ans = _answer("FIXTURE conclusion.", ["Results are not exclusive to microgravity."], ["i1"])
    assert any("does not give its exclusion reason" in v for v in _violations(fs, answer=ans))


def test_citation_with_its_exclusion_reason_passes():
    fs = [EXCLUDED, _interp("i1", [E])]
    ans = _answer(f"The value was excluded: {REASON}", [], ["i1"])
    assert _violations(fs, answer=ans) == []


def test_reason_is_required_per_citation():
    """A clean citation needs nothing; each dependent citation needs its own reason."""
    other = copy.deepcopy(EXCLUDED)
    other["id"] = "fixture-finding-measured-excluded-2"
    other_reason = "FIXTURE second, different exclusion reason."
    other["curation_notes"] = [{**other["curation_notes"][0], "note": other_reason}]
    fs = [
        EXCLUDED,
        other,
        MEASURED,
        _interp("i1", [E]),
        _interp("i2", [other["id"]], limitations=[f"Explains: {other_reason}"]),
    ]
    ans = _answer(f"The value was excluded: {REASON}", [], ["i1", "i2", M])
    v = _violations(fs, answer=ans, printed_values={**PRINTED, other["id"]: "2.5"})
    assert v == ["citation i2: answer does not give its exclusion reason"]


@pytest.mark.parametrize(
    "lim", ["FIXTURE: excluding outliers.", "FIXTURE: not exclusive to droplets."]
)
def test_keyword_interpretation_limitation_is_rejected(lim):
    """The old check passed 'excluding ...' or 'not exclusive to ...'."""
    fs = [EXCLUDED, _interp("i1", [E], limitations=[lim])]
    assert any("do not quote the exclusion note" in v for v in _violations(fs))


def test_explanation_only_interpretation_is_allowed():
    fs = [EXCLUDED, _interp("i1", [E]), _interp("i2", ["i1"])]
    assert _violations(fs) == []
    assert fs[1]["provenance"]["derived_from"] == [E]  # explanation stays traceable


# --- Other uses an exclusion-dependent finding may not have ------------------------


@pytest.mark.parametrize(
    ("extra", "fragment"),
    [
        (
            {
                "value": 0.5,
                "quantity": "flame_spread_rate",
                "unit": "mm/s",
                "value_status": "reported",
            },
            "carries a value",
        ),
        ({"relevant_environments": ["lunar_base"]}, "tagged for an environment"),
    ],
    ids=["carries-a-value", "moon-mars-recommendation"],
)
def test_misused_dependent_interpretation_is_caught(extra, fragment):
    fs = [EXCLUDED, _interp("i1", [E], **extra)]
    assert any(fragment in v for v in _violations(fs))


def test_dependent_finding_cannot_be_ranking_input():
    ranking = copy.deepcopy(_load("ranking.example.json"))
    ranking["items"][0]["criterion_scores"][0]["inputs"] = [
        {"finding_id": "i2", "evidence_class": "interpretation"}
    ]
    fs = [EXCLUDED, _interp("i1", [E]), _interp("i2", ["i1"])]
    assert any("ranking input i2" in v for v in _violations(fs, ranking=ranking))


def test_dependent_finding_cannot_be_comparable_row():
    cmp = copy.deepcopy(_load("comparison.example.json"))
    cmp["comparable"] = True
    cmp["rows"][0]["finding_id"] = E
    assert any("comparable row" in v for v in _violations([EXCLUDED], comparison=cmp))


def test_contract_examples_are_clean():
    """No input of the ranking example and no citation of the answer example is
    exclusion-dependent under the finding list example."""
    findings = _load("finding_list.example.json")["items"]
    printed = {f["id"]: ".37" for f in findings if f["value_status"] == "excluded"}
    violations = exclusion_violations(
        findings,
        ranking=_load("ranking.example.json"),
        answer=_load("assistant_answer.example.json"),
        comparison=_load("comparison.example.json"),
        printed_values=printed,
    )
    assert violations == []
