"""The development preview must stay isolated from production scientific logic."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_backend_never_imports_preview():
    for path in (ROOT / "backend").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^\s*(from|import)\s+(preview|server)\b", text, re.M), path


def test_preview_server_adds_no_api_logic():
    """It may only dispatch /api to the production app and serve static files."""
    src = (ROOT / "preview" / "server.py").read_text(encoding="utf-8")
    code = src.split('"""', 2)[2]  # skip the module docstring
    for forbidden in (
        "add_api_route",
        "@app.",
        "APIRouter",
        "Response(",
        "FastAPI(",
        "def endpoint",
    ):
        assert forbidden not in code, forbidden
    assert "from flameguard.api.app import app as production_app" in src


def test_preview_forces_blank_ai_key_and_localhost():
    src = (ROOT / "preview" / "run.py").read_text(encoding="utf-8")
    assert '"FLAMEGUARD_AI_API_KEY": ""' in src
    assert '"--host", "127.0.0.1"' in src


def test_preview_serves_the_evidence_root_it_was_given():
    """The backend is pip-installed, so without this the loader would look inside site-packages."""
    src = (ROOT / "preview" / "run.py").read_text(encoding="utf-8")
    assert 'env["FLAMEGUARD_DATA_ROOT"]' in src


def test_default_preview_serves_no_synthetic_data():
    """Synthetic scenarios exist only behind an explicit --scenario flag, and warn loudly."""
    src = (ROOT / "preview" / "run.py").read_text(encoding="utf-8")
    assert "if args.scenario:" in src and "make_scenario" in src
    assert "The page will NOT say so" in src


def test_synthetic_scenarios_never_reach_the_backend_or_data():
    for path in (ROOT / "backend").rglob("*.py"):
        assert "scenarios" not in path.read_text(encoding="utf-8"), path
    assert "SYNTHETIC" not in (ROOT / "data" / "manifest.json").read_text(encoding="utf-8")
