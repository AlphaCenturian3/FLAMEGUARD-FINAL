"""Runtime dependencies the backend needs, pinned so a removal is noticed."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _project():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_jsonschema_is_a_runtime_dependency():
    """The B1 evidence loader validates every file against the contract schemas at runtime."""
    names = {d.split(">")[0].split("=")[0].strip() for d in _project()["dependencies"]}
    assert "jsonschema" in names


def test_jsonschema_is_not_dev_only():
    dev = {d.split(">")[0].strip() for d in _project()["optional-dependencies"]["dev"]}
    assert "jsonschema" not in dev  # one declaration, in the runtime list
