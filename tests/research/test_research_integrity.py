"""Cross-cutting integrity checks for the Member 5 research package and content."""

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from flameguard.api.app import app

ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DOCS = ROOT / "docs" / "research" / "member5"
PACKAGE = ROOT / "backend" / "flameguard" / "research"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_research_package_never_imports_simulation_or_api_code():
    for path in PACKAGE.glob("*.py"):
        for name in _imports(path):
            assert "simulation" not in name, (path.name, name)
            assert not name.startswith("flameguard.api"), (path.name, name)


def test_research_content_has_no_nasa_misattribution_or_fixtures():
    for path in RESEARCH_DOCS.glob("*"):
        text = path.read_text(encoding="utf-8").lower()
        assert "according to nasa" not in text, path.name
        assert '"fixture": true' not in text, path.name


def test_register_imports_no_measurements_and_every_investigation_is_cited(register, real_evidence):
    ids = {inv["id"] for inv in register}
    assert ids == {"bass-ii", "flex", "sofie", "saffire", "fm2"}
    for inv in register:
        assert inv["member5"]["measured_records_imported"] == 0
        assert any(s["quote"] for s in inv["sources"]), inv["id"]
        assert all(s["url"].startswith("https://") for s in inv["sources"])
    assert {r["investigation_id"] for r in real_evidence} <= ids


def test_api_contract_is_unchanged_by_this_package():
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    resp = client.get("/api/rankings")
    assert resp.status_code == 501
    assert resp.json()["error"]["code"] == "not_implemented"
