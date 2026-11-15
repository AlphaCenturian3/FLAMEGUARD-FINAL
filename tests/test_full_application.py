"""The complete application in a real browser (`python -m flameguard serve`, one origin).

Whatever evidence the tree registers is what must be shown, no more and no less:
- nothing registered: the dashboard says so (and shows no data);
- FLEX registered: one investigation, one test group per `test_id`, and the exact reported /
  not_reported / excluded counts of the registered Findings, with no excluded number anywhere.
Skipped with "NOT VERIFIED" without the dashboard (frontend/) or a Chrome/Chromium/Edge.
"""

from __future__ import annotations

import csv
import html as html_lib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))


def find_chrome():
    candidates = [
        os.environ.get("CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    return next((c for c in candidates if c and Path(c).exists()), None)


CHROME = find_chrome()
pytestmark = [
    pytest.mark.skipif(
        not (REPO / "frontend" / "index.html").is_file(),
        reason="NOT VERIFIED: frontend/ is not present in this tree",
    ),
    pytest.mark.skipif(CHROME is None, reason="NOT VERIFIED: no Chrome, Chromium or Edge found"),
]


def registered():
    """(findings, investigations) the manifest registers, read from the files themselves."""
    findings, investigations = [], []
    for e in MANIFEST["datasets"]:
        if not e["path"].endswith(".json"):
            continue
        items = json.loads((REPO / e["path"]).read_text(encoding="utf-8"))
        if e["path"] == "data/curated/investigations.json":
            investigations += items
        elif e["path"].startswith(("data/curated/findings/", "data/curated/interpretations/")):
            findings += items
    return findings, investigations


FINDINGS, INVESTIGATIONS = registered()
MEASURED = [f for f in FINDINGS if f["evidence_class"] == "measured"]


def expected_groups():
    """Test rows the Explorer shows (grouping starts above 6 measured findings)."""
    total = 0
    for inv in INVESTIGATIONS:
        rows = [f for f in MEASURED if f["investigation_id"] == inv["id"]]
        if len(rows) > 6:
            total += len({f.get("test_id") or f["provenance"]["locator"] for f in rows})
    return total


def printed_value_of(finding):
    """The number printed in the registered source CSV for an excluded finding, via its locator."""
    loc = finding["provenance"]["locator"]
    m = re.search(r"field (\w+), CSV line (\d+)", loc)
    if not m:
        return None
    field, line = m.group(1), int(m.group(2))
    path = REPO / "data" / "curated" / "flex_tp2015216046_table_ix_001_010.csv"
    if not path.is_file():
        return None
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    return rows[line - 2][field] or None


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    def __init__(self, *extra):
        self.port = free_port()
        self.proc = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "flameguard", "serve", "--port", str(self.port), *extra],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(self.url + "api/health", timeout=2)  # noqa: S310
                return
            except OSError:
                time.sleep(0.3)
        self.stop()
        raise AssertionError("the application did not start")

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/"

    def stop(self):
        self.proc.terminate()
        try:
            return self.proc.communicate(timeout=15)[0]
        except subprocess.TimeoutExpired:
            self.proc.kill()
            return ""


def dom(url):
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={profile}",
            "--virtual-time-budget=8000",
            "--dump-dom",
            url,
        ]
        done = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, encoding="utf-8", timeout=90, check=False
        )
        return done.stdout


def text_of(page):
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S)
    return " ".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", page)).split())


@pytest.fixture(scope="module")
def app():
    server = Server()
    yield server
    server.stop()


def test_the_dashboard_loads_on_the_same_origin_with_no_banner_and_no_fixture_data(app):
    page = dom(app.url)
    text = text_of(page)
    assert 'id="source-banner"' in page
    assert "FIXTURE DATA. NOT NASA DATA." not in text and "FIXTURE PLACEHOLDER" not in text
    assert "may be missing or misread" not in text, (
        "no version-mismatch warning on the supported contract"
    )
    assert "API · contract" in text, "the health badge reports the API it is talking to"
    assert re.search(rf"\b{len(INVESTIGATIONS)}\s+Investigations loaded", text)
    assert re.search(rf"\b{len(MEASURED)}\s+Measured findings", text)


def test_the_explorer_shows_exactly_what_is_registered(app):
    page = dom(app.url + "#/explorer")
    text = text_of(page)
    if not INVESTIGATIONS:
        assert "No investigations available" in text
        assert 'data-value-status="' not in page
        return
    assert "No investigations available" not in text
    assert page.count('class="row-group"') == expected_groups(), "one row per test_id"
    for status in ("reported", "not_reported", "excluded"):
        expected = sum(f["value_status"] == status for f in MEASURED)
        assert page.count(f'data-value-status="{status}"') == expected, status
    outcomes = {f["test_outcome"] for f in MEASURED if f.get("test_outcome")}
    for label in outcomes:
        assert f"Test end as printed: {label}" in text, label


def test_no_excluded_measurement_is_disclosed_anywhere_on_the_page(app):
    excluded = [f for f in MEASURED if f["value_status"] == "excluded"]
    page = dom(app.url + "#/explorer")
    text = text_of(page)
    for f in excluded:
        assert f["value"] is None
        printed = printed_value_of(f)
        if printed is None:
            continue
        bare = printed.lstrip("0") if printed.startswith("0.") else printed
        assert not re.search(rf"(?<![\d.]){re.escape(printed)}(?!\d)", text), f["id"]
        assert not re.search(rf"(?<![\d.]){re.escape(bare)}(?!\d)", text), f["id"]
    assert page.count('data-value-status="excluded"') == len(excluded)
    assert ("Excluded by FlameGuard-SI" in text) or not excluded


def test_compare_and_rank_say_they_are_not_implemented_never_a_fixture_result(app):
    for route in ("#/rank", "#/integrations"):
        text = text_of(dom(app.url + route))
        assert "501" in text and "FIXTURE" not in text, route


def test_the_fixture_page_is_refused_not_silently_substituted_without_the_flag(app):
    text = text_of(dom(app.url + "?fixtures=1#/explorer"))
    assert "FIXTURE PLACEHOLDER" not in text, "fixture data must not appear when fixtures are off"
    assert "404" in text or "fixture" in text.lower(), "the page says why there is no data"


def test_with_the_fixtures_flag_the_demo_page_is_bannered_and_separate_from_live_data():
    server = Server("--fixtures")
    try:
        fixture_text = text_of(dom(server.url + "?fixtures=1#/explorer"))
        live_text = text_of(dom(server.url + "#/explorer"))
    finally:
        server.stop()
    assert "FIXTURE DATA. NOT NASA DATA." in fixture_text
    assert "FIXTURE DATA. NOT NASA DATA." not in live_text
    assert "FIXTURE PLACEHOLDER" not in live_text, (
        "live mode never shows fixtures, even when they are served"
    )


def test_the_api_on_the_same_origin_matches_the_registered_evidence(app):
    def get(path):
        with urllib.request.urlopen(app.url + path, timeout=10) as r:  # noqa: S310
            return r.status, json.loads(r.read())

    status, findings = get("api/findings")
    assert status == 200 and findings["total"] == len(FINDINGS)
    assert {f["id"] for f in findings["items"]} == {f["id"] for f in FINDINGS}
    for f in findings["items"]:
        if f["value_status"] == "excluded":
            assert f["value"] is None
    for path in ("api/compare?quantity=burn_time", "api/rankings?context=spacecraft"):
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(app.url + path, timeout=10)  # noqa: S310
        assert exc.value.code == 501
