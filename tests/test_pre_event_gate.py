"""Master spec 2.5: nothing from earlier private repositories is copied here without a recorded
organizer ruling and a checked content and license audit.

The Combustion Signal Analysis feature would reuse pre-event FFT/STFT work, so its code may not
exist in this repository until docs/decisions/pre-event-signal-analysis.md records both.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "docs" / "decisions" / "pre-event-signal-analysis.md"
FEATURE_PATHS = (
    "backend/flameguard/signal",
    "backend/flameguard/signal.py",
    "backend/flameguard/spectral.py",
    "data/retrospective",
    "frontend/static/js/signal",
    "frontend/static/js/views/signal.js",
)


def decision_state(text: str) -> dict:
    def field(name: str) -> str:
        m = re.search(rf"^(?:- )?{re.escape(name)}:[ \t]*(.*)$", text, re.M)
        return m.group(1).strip() if m else ""

    return {
        "status": field("Status"),
        "ruling": field("Organizer ruling"),
        "audit": field("Content and license audit checked by"),
    }


def approved(state: dict) -> bool:
    filled = all(v and "PENDING" not in v.upper() for v in (state["ruling"], state["audit"]))
    return state["status"] == "APPROVED" and filled


def test_decision_record_exists_and_has_a_known_status():
    state = decision_state(DECISION.read_text(encoding="utf-8"))
    assert state["status"] in {"PENDING", "APPROVED", "REFUSED"}
    assert state["ruling"] and state["audit"]


def test_signal_analysis_code_is_absent_until_both_sign_offs_are_recorded():
    present = [p for p in FEATURE_PATHS if (ROOT / p).exists()]
    state = decision_state(DECISION.read_text(encoding="utf-8"))
    assert not present or approved(state), (
        f"{present} exist but the pre-event decision is not approved: {state}"
    )


def test_a_status_line_alone_does_not_approve():
    assert not approved({"status": "APPROVED", "ruling": "PENDING", "audit": "Member 3"})
    assert not approved({"status": "APPROVED", "ruling": "yes, 2026-11-20", "audit": ""})
    assert not approved({"status": "PENDING", "ruling": "yes", "audit": "Member 3"})
    assert approved({"status": "APPROVED", "ruling": "yes, 2026-11-20", "audit": "Member 3"})
