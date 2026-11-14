"""Transitive exclusion protection (rule S9, CP1 Option (a)).

A finding is *exclusion-dependent* if it is `excluded`, or if any `derived_from` ancestor at
any depth is `excluded`. An exclusion-dependent interpretation may exist only to explain an
exclusion. It never supports a ranking, a comparison, a TARS evidence-based conclusion or a
Moon/Mars recommendation, and it never carries the excluded number as a usable value.

`exclusion_dependent_ids` below is a CONTRACT TEST ORACLE, not runtime code. Member 1
enforces the rule at runtime (B4, B6), and Member 5 tests it independently against live
outputs in tests/research/. The gap was identified by Member 2 (buihhlong-a11y) on PR #1.
"""

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"


def _load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


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


def exclusion_violations(findings, ranking=None, answer=None, comparison=None):
    """Cross-file S9 checks for one set of documents. Returns human-readable violations."""
    dep = exclusion_dependent_ids(findings)
    by_id = {f["id"]: f for f in findings}
    out = []
    for fid in sorted(dep):
        f = by_id[fid]
        if f["evidence_class"] != "interpretation":
            continue
        if f["value"] is not None or f["quantity"] is not None:
            out.append(f"{fid}: exclusion-dependent interpretation carries a value or quantity")
        if f.get("relevant_environments"):
            out.append(
                f"{fid}: exclusion-dependent interpretation is tagged as a Moon/Mars recommendation"
            )
        if not any("exclu" in lim.lower() for lim in f.get("limitations", [])):
            out.append(f"{fid}: limitations do not state that it explains an exclusion")
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
        excluded_values = {str(by_id[c]["value"]) for c in dep if by_id[c]["value"] is not None}
        for cit in answer["citations"]:
            if cit["finding_id"] in dep and answer["mode"] != "no_evidence":
                if not any("exclu" in lim.lower() for lim in answer.get("limitations", [])):
                    out.append(
                        f"citation {cit['finding_id']}: answer does not explain an exclusion"
                    )
        out += [
            f"answer states value {v!r} of an exclusion-dependent finding"
            for v in excluded_values
            if v in answer["answer"]
        ]
    return out


# --- Fixture chain built from the contract examples (all fixture: true) ------------

EXCLUDED = _load("finding.measured_excluded.example.json")
MEASURED = _load("finding.measured.example.json")
INTERP = _load("finding.interpretation.example.json")


def _interp(fid, parents, **extra):
    f = copy.deepcopy(INTERP)
    f.update(id=fid, statement=f"FIXTURE interpretation {fid}.")
    f["provenance"] = {**f["provenance"], "derived_from": parents}
    f.pop("relevant_environments", None)
    f["limitations"] = ["FIXTURE: explains why a value was excluded."]
    f.update(extra)
    return f


E, M = EXCLUDED["id"], MEASURED["id"]


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
        _interp("i5", [M, "i3"]),  # diamond-like: clean parent plus deep dependent parent
    ]
    assert exclusion_dependent_ids(fs) == {E, "i1", "i2", "i3", "i4", "i5"}


def test_clean_chain_is_not_dependent():
    fs = [MEASURED, _interp("c1", [M]), _interp("c2", ["c1"])]
    assert exclusion_dependent_ids(fs) == set()


@pytest.mark.parametrize(
    "chain",
    [
        [_interp("x", ["x"])],  # self-cycle
        [_interp("x", ["y"]), _interp("y", ["x"])],  # two-cycle
        [
            EXCLUDED,
            _interp("x", [E, "z"]),
            _interp("y", ["x"]),
            _interp("z", ["y"]),
        ],  # cycle behind an excluded parent
    ],
    ids=["self", "two", "behind-excluded"],
)
def test_cycles_are_rejected_not_looped(chain):
    with pytest.raises(ValueError, match="cycle"):
        exclusion_dependent_ids(chain)


def test_unresolved_parent_is_rejected():
    with pytest.raises(ValueError, match="unresolved"):
        exclusion_dependent_ids([_interp("i1", ["missing"])])


# --- What an exclusion-dependent interpretation may and may not do -----------------


def test_explanation_only_interpretation_is_allowed():
    fs = [EXCLUDED, _interp("i1", [E])]
    assert exclusion_violations(fs) == []
    assert fs[1]["provenance"]["derived_from"] == [E]  # explanation stays traceable


@pytest.mark.parametrize(
    ("extra", "fragment"),
    [
        (
            {
                "value": 0.37,
                "quantity": "flame_spread_rate",
                "unit": "mm/s",
                "value_status": "reported",
            },
            "carries a value",
        ),
        ({"relevant_environments": ["lunar_base"]}, "Moon/Mars"),
        ({"limitations": ["FIXTURE: generic limitation."]}, "explains an exclusion"),
    ],
    ids=["exposes-number", "moon-mars-recommendation", "no-exclusion-explanation"],
)
def test_misused_dependent_interpretation_is_caught(extra, fragment):
    fs = [EXCLUDED, _interp("i1", [E], **extra)]
    assert any(fragment in v for v in exclusion_violations(fs))


def test_dependent_finding_cannot_be_ranking_input():
    ranking = copy.deepcopy(_load("ranking.example.json"))
    ranking["items"][0]["criterion_scores"][0]["inputs"] = [
        {"finding_id": "i2", "evidence_class": "interpretation"}
    ]
    fs = [EXCLUDED, _interp("i1", [E]), _interp("i2", ["i1"])]
    assert any("ranking input i2" in v for v in exclusion_violations(fs, ranking=ranking))


def test_dependent_finding_cannot_be_comparable_row():
    cmp = copy.deepcopy(_load("comparison.example.json"))
    cmp["comparable"] = True
    cmp["rows"][0]["finding_id"] = E
    assert any("comparable row" in v for v in exclusion_violations([EXCLUDED], comparison=cmp))


def test_dependent_citation_only_to_explain_exclusion():
    ans = copy.deepcopy(_load("assistant_answer.example.json"))
    ans["citations"][0]["finding_id"] = "i1"
    fs = [EXCLUDED, _interp("i1", [E])]
    assert any("not explain an exclusion" in v for v in exclusion_violations(fs, answer=ans))
    ans["limitations"] = ["Cites i1 only to explain why a value was excluded."]
    assert exclusion_violations(fs, answer=ans) == []


def test_contract_examples_are_clean():
    """No input of the ranking example and no citation of the answer example is
    exclusion-dependent under the finding list example."""
    findings = _load("finding_list.example.json")["items"]
    assert (
        exclusion_violations(
            findings,
            ranking=_load("ranking.example.json"),
            answer=_load("assistant_answer.example.json"),
            comparison=_load("comparison.example.json"),
        )
        == []
    )
