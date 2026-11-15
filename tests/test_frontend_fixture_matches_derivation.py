"""The frontend's staged-FLEX test fixture must be exactly what the derivation produces.

The browser tests (frontend branch, PR #29) check the dashboard against a copy of the staged
derivation output. If the derivation or its inputs change, that copy must be regenerated, or the
dashboard would be tested against data it will never receive. The copy is not served and not
evidence. Skipped when the fixture is not present in this tree.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "frontend"
FINDINGS = FIXTURES / "flex-staged-candidate.json"
INVESTIGATIONS = FIXTURES / "flex-staged-investigation.json"

_spec = importlib.util.spec_from_file_location(
    "derive_flex_findings", ROOT / "tools" / "derive_flex_findings.py"
)
dv = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = dv
_spec.loader.exec_module(dv)

pytestmark = pytest.mark.skipif(
    not FINDINGS.is_file(), reason="NOT APPLICABLE: the frontend fixture is not in this tree"
)


def test_the_frontend_fixture_is_byte_identical_to_a_fresh_derivation():
    fresh = dv.derive(ROOT)
    assert FINDINGS.read_text(encoding="utf-8") == dv.dumps(fresh["findings"])
    assert INVESTIGATIONS.read_text(encoding="utf-8") == dv.dumps([fresh["investigation"]])


def test_the_fixture_is_the_staged_candidate_not_an_independent_copy_of_evidence():
    readme = (FIXTURES / "STAGED_FLEX_README.md").read_text(encoding="utf-8")
    assert "STAGING ONLY. NOT REGISTERED. NOT EVIDENCE." in readme
    assert len(json.loads(FINDINGS.read_text(encoding="utf-8"))) == 40
