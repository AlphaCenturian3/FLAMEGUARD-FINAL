"""S5, cross-document half (v0.2.2): outcome and test identity across rows and findings.

`outcome_violations` is a CONTRACT TEST ORACLE for B3 (Member 1) and for Member 5's
independent live-output tests, not runtime code. It is value-agnostic: the real outcome
vocabulary is unconfirmed, so every test here uses clearly SYNTHETIC outcome strings.

The oracle is conservative: `comparable: false` is always acceptable. It only ever reports
the dangerous direction, a response claiming `comparable: true` where the outcome rules forbid
it, plus rows that do not carry the test identity of the finding they cite.
"""

import copy

import pytest

SYN_A, SYN_B = "SYNTHETIC-OUTCOME-A", "SYNTHETIC-OUTCOME-B"


def _norm(value):
    return value if value else None  # absent, null and "" all mean "not reported"


def outcome_rules(rows):
    """Return the reasons the outcome rules forbid `comparable: true` (empty = allowed)."""
    reasons = []
    outcomes = [_norm(r.get("test_outcome")) for r in rows]
    for r in rows:
        if _norm(r.get("test_id")) and not _norm(r.get("test_outcome")):
            reasons.append(f"row {r['finding_id']}: has a test_id but no test_outcome")
    reported = {o for o in outcomes if o}
    if reported and any(o is None for o in outcomes):
        reasons.append("test_outcome is reported for some rows and not for others")
    if len(reported) > 1:
        reasons.append(f"rows report different test outcomes: {sorted(reported)}")
    return reasons


def outcome_violations(comparison, findings_by_id):
    out = []
    for row in comparison["rows"]:
        finding = findings_by_id.get(row["finding_id"])
        if finding is None or finding.get("evidence_class") != "measured":
            out.append(f"row {row['finding_id']}: does not resolve to a measured finding")
            continue
        for key in ("test_id", "test_outcome"):
            if _norm(row.get(key)) != _norm(finding.get(key)):
                out.append(f"row {row['finding_id']}: {key} differs from its finding")
    if comparison["comparable"]:
        out += [f"comparable but: {r}" for r in outcome_rules(comparison["rows"])]
    return out


def _finding(fid, tid, outcome):
    return {"id": fid, "evidence_class": "measured", "test_id": tid, "test_outcome": outcome}


def _row(fid, tid, outcome):
    return {"finding_id": fid, "test_id": tid, "test_outcome": outcome}


def _cmp(rows, comparable=True):
    return {"comparable": comparable, "rows": rows}


def _world(*specs):
    findings = {f"f{i}": _finding(f"f{i}", tid, o) for i, (tid, o) in enumerate(specs)}
    rows = [_row(f"f{i}", tid, o) for i, (tid, o) in enumerate(specs)]
    return rows, findings


def test_same_outcome_is_allowed():
    rows, findings = _world(("T-1", SYN_A), ("T-2", SYN_A))
    assert outcome_violations(_cmp(rows), findings) == []


def test_legacy_rows_without_test_identity_are_allowed():
    rows, findings = _world((None, None), (None, None))
    assert outcome_violations(_cmp(rows), findings) == []


@pytest.mark.parametrize(
    ("specs", "fragment"),
    [
        ([("T-1", SYN_A), ("T-2", SYN_B)], "different test outcomes"),
        ([("T-1", SYN_A), ("T-2", SYN_A), ("T-3", SYN_B)], "different test outcomes"),
        ([("T-1", SYN_A), ("T-2", None)], "some rows and not for others"),
        ([("T-1", SYN_A), (None, None)], "some rows and not for others"),
        ([("T-1", None), ("T-2", None)], "has a test_id but no test_outcome"),
        ([("T-1", None), (None, None)], "has a test_id but no test_outcome"),
    ],
    ids=[
        "differ",
        "odd-one-out",
        "partial",
        "partial-bare-row",
        "id-no-outcome",
        "one-id-no-outcome",
    ],
)
def test_forbidden_outcome_sets_cannot_be_comparable(specs, fragment):
    rows, findings = _world(*specs)
    violations = outcome_violations(_cmp(rows, comparable=True), findings)
    assert any(fragment in v for v in violations), violations
    assert outcome_violations(_cmp(rows, comparable=False), findings) == []  # honest answer is fine


def test_a_row_must_carry_its_findings_test_identity():
    rows, findings = _world(("T-1", SYN_A), ("T-2", SYN_A))
    forged = copy.deepcopy(rows)
    forged[1]["test_outcome"] = SYN_B  # the row lies about the finding
    assert any(
        "test_outcome differs" in v for v in outcome_violations(_cmp(forged, False), findings)
    )
    dropped = copy.deepcopy(rows)
    dropped[0]["test_id"] = None
    assert any("test_id differs" in v for v in outcome_violations(_cmp(dropped, False), findings))


def test_an_outcome_hidden_only_on_the_row_cannot_create_comparability():
    """Rows claiming a shared outcome while the findings disagree are caught twice."""
    rows, findings = _world(("T-1", SYN_A), ("T-2", SYN_B))
    for r in rows:
        r["test_outcome"] = SYN_A
    violations = outcome_violations(_cmp(rows, comparable=True), findings)
    assert any("test_outcome differs from its finding" in v for v in violations)


def test_unresolved_or_non_measured_rows_are_violations():
    rows, findings = _world(("T-1", SYN_A), ("T-2", SYN_A))
    rows.append(_row("ghost", "T-3", SYN_A))
    assert any("does not resolve" in v for v in outcome_violations(_cmp(rows, False), findings))
    findings["f0"]["evidence_class"] = "interpretation"
    assert any("does not resolve" in v for v in outcome_violations(_cmp(rows[:2], False), findings))


def test_absent_null_and_empty_all_mean_not_reported():
    rows = [
        {"finding_id": "a", "test_id": "T-1"},
        {"finding_id": "b", "test_id": "T-2", "test_outcome": ""},
    ]
    assert len(outcome_rules(rows)) == 2


def test_outcome_comparison_is_exact_not_fuzzy():
    rows, findings = _world(("T-1", SYN_A), ("T-2", SYN_A.lower()))
    assert any("different test outcomes" in v for v in outcome_violations(_cmp(rows), findings))


def test_an_empty_string_outcome_next_to_a_reported_one_is_partial_reporting():
    rows = [
        {"finding_id": "a", "test_id": "T-1", "test_outcome": SYN_A},
        {"finding_id": "b", "test_id": "T-2", "test_outcome": ""},
    ]
    assert any("some rows and not for others" in r for r in outcome_rules(rows))


# --- S11: test identity is all-or-nothing within an investigation (Member 5's condition 7) ---


def identity_violations(findings):
    """If any measured finding of an investigation carries a test_id, every measured finding of
    that investigation must carry one, and a finding that carries an outcome must carry a test_id.
    This closes the bypass of omitting both fields. It is a contract oracle for the B1 loader
    (proposed) and for the derivation acceptance tests; it is not runtime code."""
    out = []
    by_investigation = {}
    for f in findings:
        if f.get("evidence_class") == "measured":
            by_investigation.setdefault(f["investigation_id"], []).append(f)
    for inv, group in sorted(by_investigation.items()):
        has_identity = [f for f in group if _norm(f.get("test_id"))]
        if has_identity:
            out += [
                f"{inv}: {f['id']} has no test_id" for f in group if not _norm(f.get("test_id"))
            ]
        out += [
            f"{inv}: {f['id']} has a test_outcome but no test_id"
            for f in group
            if _norm(f.get("test_outcome")) and not _norm(f.get("test_id"))
        ]
    return out


def _mf(fid, inv, tid=None, outcome=None, cls="measured"):
    return {
        "id": fid,
        "investigation_id": inv,
        "evidence_class": cls,
        "test_id": tid,
        "test_outcome": outcome,
    }


def test_identity_complete_investigation_is_clean():
    fs = [_mf("a", "inv", "T-1", SYN_A), _mf("b", "inv", "T-2", SYN_B), _mf("c", "other")]
    assert identity_violations(fs) == []


def test_one_finding_without_identity_in_an_identified_investigation_is_a_violation():
    fs = [_mf("a", "inv", "T-1", SYN_A), _mf("b", "inv")]
    assert identity_violations(fs) == ["inv: b has no test_id"]


def test_omitting_identity_on_every_finding_is_not_detectable_here():
    """Documented limit: only derivation tests can require identity where none is present."""
    assert identity_violations([_mf("a", "inv"), _mf("b", "inv")]) == []


def test_an_outcome_without_an_identity_is_a_violation():
    assert identity_violations([_mf("a", "inv", None, SYN_A)]) == [
        "inv: a has a test_outcome but no test_id"
    ]


def test_interpretations_and_other_investigations_are_not_constrained():
    fs = [
        _mf("a", "inv", "T-1", SYN_A),
        _mf("i", "inv", None, None, cls="interpretation"),
        _mf("z", "other"),
    ]
    assert identity_violations(fs) == []
