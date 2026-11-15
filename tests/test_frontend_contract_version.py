"""The dashboard's accepted contract versions are explicit, and tied to the contract in this tree.

A version bump in the backend must fail here until the frontend adds the new version on purpose,
after testing it (frontend/tests/flex.test.js). The staged FLEX fixture is validated against the
real schemas whenever the tree's contract is new enough to describe it.
"""

import json
import re
from pathlib import Path

import pytest

from flameguard import CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]
CONFIG = (ROOT / "frontend" / "static" / "js" / "config.js").read_text(encoding="utf-8")


def js_supported() -> list[str]:
    m = re.search(r"SUPPORTED_CONTRACT_VERSIONS = Object\.freeze\(\[(.*?)\]\)", CONFIG, re.S)
    assert m, "SUPPORTED_CONTRACT_VERSIONS not found in config.js"
    return re.findall(r'"(\d+\.\d+\.\d+)"', m.group(1))


def version_tuple(v):
    return tuple(int(x) for x in v.split("."))


def test_the_backend_contract_version_is_one_the_dashboard_explicitly_supports():
    assert CONTRACT_VERSION in js_supported(), (
        f"backend contract {CONTRACT_VERSION} is not in the dashboard's SUPPORTED_CONTRACT_VERSIONS; "
        "test the dashboard with that version, then add it deliberately"
    )


def test_the_dashboard_implements_the_newest_supported_version_and_only_0_2_patches():
    supported = js_supported()
    declared = re.search(r'CONTRACT_VERSION = "(\d+\.\d+\.\d+)"', CONFIG).group(1)
    assert declared == max(supported, key=version_tuple)
    assert supported == sorted(supported, key=version_tuple) and len(set(supported)) == len(
        supported
    )
    assert all(v.startswith("0.2.") for v in supported), (
        "a minor or major change is never tolerated silently"
    )


def test_the_vocabulary_version_matches_the_contract_version():
    vocabulary = json.loads((ROOT / "contracts" / "vocabulary.json").read_text(encoding="utf-8"))
    assert vocabulary["vocabulary_version"] == CONTRACT_VERSION


def test_the_staged_flex_fixture_matches_the_contract_schemas(validator_for):
    if version_tuple(CONTRACT_VERSION) < (0, 2, 2):
        pytest.skip(
            "NOT VERIFIED: the schemas of this tree (v%s) predate test_id/test_outcome"
            % CONTRACT_VERSION
        )
    findings = json.loads(
        (ROOT / "tests/fixtures/frontend/flex-staged-candidate.json").read_text(encoding="utf-8")
    )
    investigations = json.loads(
        (ROOT / "tests/fixtures/frontend/flex-staged-investigation.json").read_text(
            encoding="utf-8"
        )
    )
    finding_v, inv_v = (
        validator_for("finding.schema.json"),
        validator_for("investigation.schema.json"),
    )
    for f in findings:
        assert not list(finding_v.iter_errors(f)), f["id"]
    for i in investigations:
        assert not list(inv_v.iter_errors(i)), i["id"]
