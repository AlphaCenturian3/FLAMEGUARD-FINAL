"""B7: the dashboard and the API on one origin (backend/flameguard/api/frontend.py).

Mechanics are tested with a tiny SYNTHETIC dashboard in a temp folder, so these tests run
everywhere. The tests that use the real `frontend/` skip with "NOT VERIFIED" where it is absent.
"""

from __future__ import annotations

import posixpath
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flameguard.api.app import create_app
from flameguard.api.explorer import REJECTED_HEADER, EvidenceSource
from flameguard.api.frontend import FrontendError, default_fixtures_dir, default_frontend_dir

REPO = Path(__file__).resolve().parents[2]
REAL_FRONTEND = REPO / "frontend"
INDEX = (
    '<!doctype html><title>SYNTHETIC dashboard</title><div id="source-banner"></div>'
    '<script type="module" src="static/js/main.js"></script>'
)


@pytest.fixture
def site_dir(tmp_path):
    root = tmp_path / "dashboard"
    (root / "static" / "js").mkdir(parents=True)
    (root / "static" / "css").mkdir(parents=True)
    (root / "index.html").write_text(INDEX, encoding="utf-8")
    (root / "static" / "js" / "main.js").write_text("export const ok = true;\n", encoding="utf-8")
    (root / "static" / "css" / "app.css").write_text("body{}\n", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("SECRET OUTSIDE THE DASHBOARD", encoding="utf-8")
    return root


@pytest.fixture
def examples_dir(tmp_path):
    d = tmp_path / "examples"
    d.mkdir()
    (d / "health.example.json").write_text('{"fixture": true}', encoding="utf-8")
    (tmp_path / "vocabulary.json").write_text("NOT AN EXAMPLE", encoding="utf-8")
    return d


def site(scenario, site_dir, **kwargs):
    if not hasattr(scenario, "written_root"):
        scenario.written_root = scenario.write()
    return TestClient(create_app(EvidenceSource(scenario.written_root), site_dir, **kwargs))


def assert_error(r, status, code):
    assert r.status_code == status, r.text
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["error"]["code"] == code


# ---------------------------------------------------------------------------------------------
# One origin: dashboard assets and API
# ---------------------------------------------------------------------------------------------


def test_the_dashboard_and_its_assets_are_served_with_the_right_types(scenario, site_dir):
    client = site(scenario, site_dir)
    index = client.get("/")
    assert index.status_code == 200 and "SYNTHETIC dashboard" in index.text
    assert index.headers["content-type"].startswith("text/html")
    js = client.get("/static/js/main.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    assert client.get("/static/css/app.css").headers["content-type"].startswith("text/css")
    assert client.head("/").status_code == 200


def test_api_routes_win_and_unknown_api_paths_are_json_errors_never_the_dashboard(
    scenario, site_dir
):
    client = site(scenario, site_dir)
    health = client.get("/api/health")
    assert health.json()["status"] == "ok" and "SYNTHETIC" not in health.text
    assert "items" in client.get("/api/investigations").json()
    assert "items" in client.get("/api/findings").json()
    assert_error(client.get("/api/does-not-exist"), 404, "not_found")
    assert_error(client.post("/api/does-not-exist"), 405, "invalid_request")
    assert_error(client.get("/api/investigations/nope"), 404, "not_found")
    for path in ("/api/compare?quantity=burn_time", "/api/rankings?context=spacecraft"):
        assert_error(client.get(path), 501, "not_implemented")
    assert_error(client.post("/api/assistant/ask", json={"question": "x"}), 501, "not_implemented")


def test_a_hostile_file_named_like_an_api_route_cannot_shadow_the_api(scenario, site_dir):
    (site_dir / "api").mkdir()
    (site_dir / "api" / "health").write_text("HOSTILE", encoding="utf-8")
    (site_dir / "api" / "findings").write_text("HOSTILE", encoding="utf-8")
    client = site(scenario, site_dir)
    assert client.get("/api/health").json()["status"] == "ok"
    assert "items" in client.get("/api/findings").json()
    assert "HOSTILE" not in client.get("/api/investigations").text


def test_there_is_no_spa_fallback_an_unknown_file_is_a_json_404(scenario, site_dir):
    client = site(scenario, site_dir)
    assert_error(client.get("/no/such/page"), 404, "not_found")
    assert_error(client.get("/static/js/missing.js"), 404, "not_found")


def test_files_outside_the_dashboard_cannot_be_reached(scenario, site_dir):
    client = site(scenario, site_dir)
    for path in (
        "/../secret.txt",
        "/static/../../secret.txt",
        "/static/..%2f..%2fsecret.txt",
        "/%2e%2e/secret.txt",
        "/..%2fsecret.txt",
    ):
        r = client.get(path)
        assert "SECRET" not in r.text, path
        assert r.status_code in (400, 404), path


def test_without_a_dashboard_the_root_is_an_honest_json_404(scenario):
    client = TestClient(create_app(EvidenceSource(scenario.write())))
    assert_error(client.get("/"), 404, "not_found")
    assert client.get("/api/health").status_code == 200


def test_a_dashboard_folder_without_index_html_is_refused_at_startup(scenario, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FrontendError, match="no index.html"):
        create_app(EvidenceSource(scenario.write()), empty)
    assert default_frontend_dir(tmp_path) is None


def test_security_headers_and_api_responses_are_never_cached(scenario, site_dir):
    client = site(scenario, site_dir)
    for path in ("/", "/static/js/main.js", "/api/health", "/api/findings", "/api/nope"):
        r = client.get(path)
        assert r.headers["x-content-type-options"] == "nosniff", path
        assert r.headers["referrer-policy"] == "no-referrer", path
    assert client.get("/api/findings").headers["cache-control"] == "no-store"
    assert client.get("/api/nope").headers["cache-control"] == "no-store"
    assert "no-store" not in client.get("/").headers.get("cache-control", "")


# ---------------------------------------------------------------------------------------------
# Evidence, errors and fixtures
# ---------------------------------------------------------------------------------------------


def test_registered_evidence_is_served_and_the_excluded_value_never_is(scenario, site_dir):
    client = site(scenario, site_dir)
    items = client.get("/api/findings").json()["items"]
    by_id = {f["id"]: f for f in items}
    assert by_id["ex1"]["value_status"] == "excluded" and by_id["ex1"]["value"] is None
    assert by_id["m1"]["value_status"] == "reported"
    assert not [f for f in items if f.get("fixture")], "fixture data is never served by the API"


def test_a_broken_evidence_set_fails_closed_while_the_dashboard_still_loads(scenario, site_dir):
    scenario.raw["data/manifest.json"] = "{ not json"
    client = site(scenario, site_dir)
    assert client.get("/").status_code == 200, "the page can load and show its own error panel"
    for path in ("/api/findings", "/api/investigations", "/api/investigations/x"):
        assert_error(client.get(path), 503, "unavailable")


def test_a_rejected_file_is_visible_to_the_page_through_the_header(scenario, site_dir):
    scenario.interps["notes"][0]["statement"] = ""  # invalid, so that file is rejected whole
    client = site(scenario, site_dir)
    r = client.get("/api/findings")
    assert r.status_code == 200 and r.headers[REJECTED_HEADER] == "1"


def test_fixtures_are_off_by_default_and_only_the_examples_folder_is_exposed_when_on(
    scenario, site_dir, examples_dir
):
    off = site(scenario, site_dir)
    assert_error(off.get("/contracts/examples/health.example.json"), 404, "not_found")
    on = site(scenario, site_dir, serve_fixtures_dir=examples_dir)
    assert on.get("/contracts/examples/health.example.json").json() == {"fixture": True}
    for path in (
        "/contracts/vocabulary.json",
        "/contracts/examples/../vocabulary.json",
        "/contracts/examples/..%2fvocabulary.json",
    ):
        r = on.get(path)
        assert "NOT AN EXAMPLE" not in r.text, path
    assert not [f for f in on.get("/api/findings").json()["items"] if f.get("fixture")]


def test_default_fixture_serving_needs_an_explicit_environment_switch(tmp_path, monkeypatch):
    (tmp_path / "contracts" / "examples").mkdir(parents=True)
    monkeypatch.delenv("FLAMEGUARD_SERVE_FIXTURES", raising=False)
    assert default_fixtures_dir(tmp_path) is None
    monkeypatch.setenv("FLAMEGUARD_SERVE_FIXTURES", "yes")
    assert default_fixtures_dir(tmp_path) is None, "only the exact value 1 turns it on"
    monkeypatch.setenv("FLAMEGUARD_SERVE_FIXTURES", "1")
    assert default_fixtures_dir(tmp_path) == tmp_path / "contracts" / "examples"


# ---------------------------------------------------------------------------------------------
# The one command
# ---------------------------------------------------------------------------------------------


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # noqa: S310
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def test_python_m_flameguard_serve_starts_one_origin_and_reports_what_it_serves(scenario, site_dir):
    root = scenario.write()
    port = free_port()
    cmd = [
        sys.executable,
        "-m",
        "flameguard",
        "serve",
        "--port",
        str(port),
        "--data-root",
        str(root),
        "--frontend-dir",
        str(site_dir),
    ]
    proc = subprocess.Popen(  # noqa: S603
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8"
    )  # noqa: S603
    try:
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            try:
                status, body = fetch(f"http://127.0.0.1:{port}/api/health")
                if status == 200:
                    break
            except OSError:
                time.sleep(0.3)
        else:
            pytest.fail("the server did not start")
        assert fetch(f"http://127.0.0.1:{port}/")[1].startswith("<!doctype html>")
        assert fetch(f"http://127.0.0.1:{port}/api/findings")[0] == 200
        assert fetch(f"http://127.0.0.1:{port}/contracts/examples/health.example.json")[0] == 404
    finally:
        proc.terminate()
        out = proc.communicate(timeout=15)[0]
    assert f"OPEN THIS ADDRESS: http://127.0.0.1:{port}/" in out
    assert "evidence: 1 investigation(s)" in out and "HTTP 501" in out


def test_the_command_refuses_clearly_for_a_busy_port_or_a_missing_dashboard(
    scenario, site_dir, tmp_path, capsys
):
    from flameguard import __main__ as cli

    root = scenario.write()
    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    held.listen(128)
    try:
        port = held.getsockname()[1]
        args = ["serve", "--data-root", str(root), "--frontend-dir", str(site_dir)]
        assert cli.main([*args, "--port", str(port)]) == 2
        assert "already in use" in capsys.readouterr().out
        assert cli.pick_port(port) > port, "auto-port moves to a free neighbour"
    finally:
        held.close()
    assert cli.main(["serve", "--data-root", str(tmp_path)]) == 2
    assert "No dashboard found" in capsys.readouterr().out


# ---------------------------------------------------------------------------------------------
# The real dashboard (skipped where frontend/ is absent)
# ---------------------------------------------------------------------------------------------

real_frontend = pytest.mark.skipif(
    not (REAL_FRONTEND / "index.html").is_file(),
    reason="NOT VERIFIED: frontend/ is not present in this tree",
)


@real_frontend
def test_every_module_and_stylesheet_of_the_real_dashboard_resolves_on_one_origin():
    client = TestClient(create_app(EvidenceSource(REPO), REAL_FRONTEND))
    index = client.get("/")
    assert index.status_code == 200 and 'id="source-banner"' in index.text
    pattern = r'(?:src|href)="([^"#?]+\.(?:js|css))"'
    todo = [posixpath.normpath("/" + m) for m in re.findall(pattern, index.text)]
    seen: set[str] = set()
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        if path.endswith(".js"):
            base = posixpath.dirname(path)
            for spec in re.findall(
                r'(?:from|import)\s*\(?\s*["\'](\.{1,2}/[^"\']+\.js)["\']', r.text
            ):
                todo.append(posixpath.normpath(posixpath.join(base, spec)))
    assert len(seen) > 20, f"only {len(seen)} assets were reached"


@real_frontend
def test_the_real_dashboard_defaults_to_live_data_and_never_fixtures(scenario):
    client = TestClient(create_app(EvidenceSource(REPO), REAL_FRONTEND))
    assert client.get("/contracts/examples/health.example.json").status_code == 404
    page = client.get("/").text
    assert "FIXTURE PLACEHOLDER" not in page
