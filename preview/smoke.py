"""Smoke checks for a running FlameGuard-SI development preview.

    python preview/smoke.py http://127.0.0.1:8790/

API checks always run. Browser checks need Chrome or Chromium (set CHROME to override the
path); the judge-demo check also needs Node 22+. A check that cannot run is reported as
SKIPPED (not verified), never as passed. Exit code 1 means at least one check failed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLANNED = [
    ("GET", "api/investigations"),
    ("GET", "api/investigations/x"),
    ("GET", "api/findings"),
    ("GET", "api/compare?quantity=flame_spread_rate"),
    ("GET", "api/rankings?context=spacecraft"),
    ("POST", "api/assistant/ask"),
    ("GET", "api/simulations/x"),
]
ROUTES = ["", "explorer", "compare", "rank", "interpret", "integrations"]
FIXTURE_BANNER = "This is not NASA data"
results: list[tuple[str, str, str]] = []  # (status, name, detail)


def record(ok: bool | None, name: str, detail: str = "") -> None:
    results.append(
        ("PASS" if ok else "SKIPPED (not verified)" if ok is None else "FAIL", name, detail)
    )


def http(method: str, url: str) -> tuple[int, bytes]:
    body = b'{"question": "smoke"}' if method == "POST" else None
    req = urllib.request.Request(  # noqa: S310 (http URL built from the preview base)
        url, data=body, method=method, headers={"content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def api_checks(base: str) -> None:
    code, body = http("GET", base + "api/health")
    doc = json.loads(body) if code == 200 else {}
    record(code == 200 and doc.get("status") == "ok", "GET /api/health is 200 ok", f"{code} {doc}")
    for method, path in PLANNED:
        code, body = http(method, base + path)
        err = json.loads(body).get("error", {}) if body.startswith(b"{") else {}
        record(
            code == 501 and err.get("code") == "not_implemented",
            f"{method} /{path} is 501",
            str(code),
        )
    code, _ = http("GET", base + "api/does-not-exist")
    record(code == 404, "unknown /api path is 404 (no static fallback)", str(code))
    code, body = http("GET", base)
    record(code == 200 and b'id="source-banner"' in body, "GET / serves the frontend", str(code))
    code, _ = http("GET", base + "contracts/examples/health.example.json")
    record(code == 200, "contract fixtures served at /contracts/examples/", str(code))


def find_chrome() -> str | None:
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


def dump(chrome: str, url: str, profile: str) -> str:
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        f"--user-data-dir={profile}",
    ]
    cmd += ["--virtual-time-budget=8000", "--dump-dom", url]
    done = subprocess.run(  # noqa: S603
        cmd, capture_output=True, text=True, encoding="utf-8", timeout=90, check=False
    )
    return done.stdout


def text_of(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def browser_checks(base: str, chrome: str | None) -> None:
    if not chrome:
        record(None, "browser route checks", "no Chrome/Chromium found (set CHROME)")
        return
    with tempfile.TemporaryDirectory() as prof:
        for mode, query in (("fixture", "?source=fixtures"), ("live", "")):
            for route in ROUTES:
                html = dump(chrome, f"{base}{query}#/{route}", prof)
                t = text_of(html)
                name = f"{mode} mode #/{route or ''}"
                ok = "<h1" in html and "Page not found" not in t
                if mode == "fixture":
                    ok = ok and FIXTURE_BANNER in t
                else:  # live mode must never show fixtures as data
                    ok = (
                        ok
                        and FIXTURE_BANNER not in t
                        and "FIXTURE PLACEHOLDER" not in t
                        and "API ok" in t
                    )
                if route == "rank":
                    ok = ok and "501" in t
                h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
                record(ok, name, text_of(h1.group(1)) if h1 else "no h1")


def demo_checks(base: str, chrome: str | None) -> None:
    node = shutil.which("node")
    if not (chrome and node):
        record(None, "judge demo walkthrough", "needs Chrome and Node 22+")
        return
    for mode, query in (("fixture", "?source=fixtures"), ("live", "")):
        cmd = [node, str(HERE / "demo_check.mjs"), chrome, base + query]
        proc = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, encoding="utf-8", timeout=180, check=False
        )
        try:
            steps = json.loads(proc.stdout)
        except json.JSONDecodeError:
            record(False, f"judge demo ({mode})", (proc.stderr or proc.stdout)[-300:])
            continue
        titles = [s["title"] for s in steps]
        expected = ["Discover", "Compare", "Rank", "Interpret", "Safety Insight"]
        rank = next((s for s in steps if s["title"] == "Rank"), {})
        ok = titles == expected and rank.get("shows501") is True
        if mode == "fixture":
            ok = ok and all(s["fixtureBanner"] for s in steps)
        else:
            ok = ok and not any(s["fixtureBanner"] for s in steps)
        record(ok, f"judge demo ({mode})", " -> ".join(f"{s['title']}@{s['hash']}" for s in steps))


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8790/").rstrip("/") + "/"
    api_checks(base)
    chrome = find_chrome()
    browser_checks(base, chrome)
    demo_checks(base, chrome)
    width = max(len(n) for _, n, _ in results)
    for status, name, detail in results:
        print(f"{status:<22} {name:<{width}}  {detail}")
    failed = sum(s == "FAIL" for s, _, _ in results)
    skipped = sum(s.startswith("SKIPPED") for s, _, _ in results)
    passed = len(results) - failed - skipped
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped (not verified)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
