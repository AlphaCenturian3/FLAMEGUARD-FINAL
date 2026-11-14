import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_data_provenance", ROOT / "tools" / "check_data_provenance.py"
)
cdp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cdp)

SOURCE = {"title": "T", "url": "https://example.invalid", "retrieved": "2026-11-14"}


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "data/curated").mkdir(parents=True)
    (tmp_path / "data/simulated").mkdir(parents=True)
    f = tmp_path / "data/curated/a.csv"
    f.write_text("x\n1\n")
    return tmp_path, hashlib.sha256(f.read_bytes()).hexdigest()


def _measured(sha, **kw):
    entry = {
        "id": "a",
        "path": "data/curated/a.csv",
        "evidence_class": "measured",
        "sha256": sha,
        "description": "d",
        "sources": [SOURCE],
        "rights_status": "under_review",
    }
    entry.update(kw)
    return entry


def test_repository_manifest_passes_schema_and_rules(validator_for):
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    validator_for("data_manifest.schema.json").validate(manifest)
    assert cdp.check_manifest(manifest) == []
    assert cdp.tracked_raw_files() == []


def test_valid_measured_entry_passes(repo):
    root, sha = repo
    assert cdp.check_manifest({"datasets": [_measured(sha)]}, root) == []


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"sources": []}, "needs at least one source"),
        ({"rights_status": None}, "rights_status"),
        ({"sha256": "0" * 64}, "sha256 mismatch"),
        ({"fixture": True}, "fixtures belong"),
        ({"path": "data/simulated/a.csv"}, "must live under data/curated"),
        ({"evidence_class": "estimated"}, "evidence_class must be"),
        ({"path": "data/curated/interpretations/a.csv"}, "must live under data/curated/"),
    ],
)
def test_measured_violations_are_caught(repo, override, fragment):
    root, sha = repo
    errors = cdp.check_manifest({"datasets": [_measured(sha, **override)]}, root)
    assert any(fragment in e for e in errors), errors


def test_interpretation_needs_known_parent_and_method(repo):
    root, sha = repo
    interp = _measured(sha, id="b", evidence_class="interpretation", derived_from=["nope"])
    errors = cdp.check_manifest({"datasets": [_measured(sha), interp]}, root)
    assert any("unknown id 'nope'" in e for e in errors)
    assert any("needs method" in e for e in errors)


def test_simulation_needs_exact_label(repo):
    root, _ = repo
    f = root / "data/simulated/s.json"
    f.write_text("{}")
    sim = {
        "id": "s",
        "path": "data/simulated/s.json",
        "evidence_class": "illustrative_simulation",
        "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        "description": "d",
        "model": "m",
        "model_version": "0",
        "label": "Simulation",
    }
    errors = cdp.check_manifest({"datasets": [sim]}, root)
    assert any("simulation label" in e for e in errors)
    sim["label"] = cdp.SIMULATION_LABEL
    assert cdp.check_manifest({"datasets": [sim]}, root) == []


def test_duplicate_ids_are_caught(repo):
    root, sha = repo
    errors = cdp.check_manifest({"datasets": [_measured(sha), _measured(sha)]}, root)
    assert any("duplicate id" in e for e in errors)


AGREEMENT_CASES = {
    "measured-no-sources": {"sources": []},
    "measured-no-rights": {"rights_status": None},
    "measured-in-simulated": {"path": "data/simulated/a.csv"},
    "measured-in-interpretations": {"path": "data/curated/interpretations/a.csv"},
    "unknown-class": {"evidence_class": "estimated"},
    "fixture-flag": {"fixture": True},
}


@pytest.mark.parametrize("override", AGREEMENT_CASES.values(), ids=AGREEMENT_CASES)
def test_manifest_schema_and_checker_both_reject(validator_for, repo, override):
    """The schema (used by any validator) and the tool must agree, so no workstream
    can pass one while failing the other."""
    from jsonschema import ValidationError

    root, sha = repo
    entry = {k: v for k, v in _measured(sha, **override).items() if v is not None}
    manifest = {"manifest_version": "0.2.0", "datasets": [entry]}
    with pytest.raises(ValidationError):
        validator_for("data_manifest.schema.json").validate(manifest)
    assert cdp.check_manifest(manifest, root)


def test_valid_entry_passes_schema_and_checker(validator_for, repo):
    root, sha = repo
    manifest = {"manifest_version": "0.2.0", "datasets": [_measured(sha)]}
    validator_for("data_manifest.schema.json").validate(manifest)
    assert cdp.check_manifest(manifest, root) == []


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_registered_json_with_nan_or_infinity_is_rejected(repo, constant):
    """Rule S0: NaN passes JSON Schema numeric bounds, so files must be parsed strictly."""
    root, _ = repo
    f = root / "data/curated/findings.json"
    f.write_text(f'[{{"value": {constant}}}]')
    entry = _measured(hashlib.sha256(f.read_bytes()).hexdigest(), path="data/curated/findings.json")
    errors = cdp.check_manifest({"datasets": [entry]}, root)
    assert any("non-standard JSON number" in e for e in errors), errors


def test_strict_loader_accepts_normal_json(tmp_path):
    f = tmp_path / "ok.json"
    f.write_text('[{"value": 1.5, "missing": null}]')
    assert cdp.load_strict_json(f) == [{"value": 1.5, "missing": None}]
