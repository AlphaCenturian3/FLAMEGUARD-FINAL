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
