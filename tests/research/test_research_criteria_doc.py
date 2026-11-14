"""Consistency checks for CRITERIA_ENVIRONMENT_CONTEXT.md, revision 2 (documentation only)."""

from pathlib import Path

DOC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "research"
    / "member5"
    / "CRITERIA_ENVIRONMENT_CONTEXT.md"
)


def _text():
    return DOC.read_text(encoding="utf-8")


def test_purpose_relevance_is_not_weighted():
    t = _text()
    assert "score = w_C · C + w_T · T + w_D · D" in t
    assert "removed from the weighted score" in t
    assert "w_P" not in t


def test_gates_are_documented_and_pending_member3():
    t = _text()
    for gate in ("E1 Evidence", "E2 Source-stated relevance", "E3 Integrity"):
        assert gate in t
    assert "pending Member 3" in t.lower() or "Pending Member 3" in t


def test_oxygen_and_pressure_are_descriptive_and_unknowns_are_marked():
    t = _text()
    assert "O₂ and pressure: descriptive, not scored" in t
    assert "Inactive" in t or "inactive" in t
    assert "reference unknown" in t
    assert "assumed: coast phase" in t


def test_nothing_is_presented_as_approved():
    t = _text()
    assert "not approved" in t
    assert "No weights are proposed or approved here." in t
