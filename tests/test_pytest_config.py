"""The repository root must be importable from tests (spec 4.3: research/ is test-only)."""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pytest_pythonpath_includes_repository_root():
    cfg = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert cfg["tool"]["pytest"]["ini_options"]["pythonpath"] == ["."]


def test_repository_root_is_importable(tmp_path):
    assert str(ROOT) in [str(Path(p).resolve()) for p in sys.path if p]
