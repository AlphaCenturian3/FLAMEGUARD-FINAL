"""Run the frontend's in-browser test harness in headless Chrome and fail on any failure.

    python .github/scripts/run_frontend_tests.py [--require] [--chrome PATH]

The harness (frontend/tests/index.html) runs in the page and reports `PASS n/n` or
`FAIL k/n` in the document title. This script serves the repository root on a free
localhost port, loads the harness with headless Chrome, and reads that result. It adds no
dependency: it needs only Python's standard library and a Chrome or Chromium binary
(GitHub's ubuntu-latest runners include google-chrome).

Fail closed: no Chrome, an unreadable page, a missing result or zero tests is a failure,
never a pass. `--min-tests N` also fails a run in which fewer than N tests ran, so a harness
that silently shrinks (a test file dropped from its imports) cannot report a green PASS.

The one exception is a repository with no frontend at all: if the `frontend/` directory does
not exist the script prints "SKIPPED (not verified)" and exits 0 (unless --require is given).
As soon as `frontend/` exists, a missing harness is a FAILURE, so the harness can never be
deleted or renamed back into a silent skip, and no follow-up workflow change is needed.
"""

from __future__ import annotations

import argparse
import html
import http.server
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = "frontend/tests/index.html"
TITLE = re.compile(r"<title>\s*(PASS|FAIL)\s+(\d+)\s*/\s*(\d+)\s*</title>")
RESULTS = re.compile(r'id="results"[^>]*>(.*?)</pre>', re.S)


@dataclass(frozen=True)
class Outcome:
    ok: bool
    summary: str
    failures: tuple[str, ...] = ()
    total: int = 0  # tests the harness ran, when it reported


def parse_dom(dom: str) -> Outcome:
    """Turn the rendered harness page into an Outcome. Anything unexpected is a failure."""
    match = TITLE.search(dom)
    if not match:
        return Outcome(False, "no PASS/FAIL result in the page title (harness did not finish)")
    verdict, first, total = match.group(1), int(match.group(2)), int(match.group(3))
    block = RESULTS.search(dom)
    lines = html.unescape(block.group(1)).splitlines() if block else []
    failures = tuple(line.strip() for line in lines if line.startswith("FAIL"))
    if total == 0:
        return Outcome(False, "the harness ran 0 tests")
    if verdict == "FAIL" or failures:
        return Outcome(False, f"FAIL {first or len(failures)}/{total}", failures, total)
    if first != total:
        return Outcome(False, f"PASS {first}/{total}: not every test passed", (), total)
    return Outcome(True, f"PASS {first}/{total}", (), total)


def find_chrome(explicit: str | None) -> str | None:
    """An explicit path (--chrome or CHROME) is authoritative: if it is wrong, there is no
    fallback, so a misconfigured CI never quietly tests with a different browser."""
    chosen = explicit or os.environ.get("CHROME")
    if chosen:
        return chosen if Path(chosen).exists() else None
    names = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    candidates = [*(shutil.which(n) for n in names), mac]
    return next((c for c in candidates if c and Path(c).exists()), None)


def browser_version(chrome: str) -> str:
    """The browser build used, for traceability: runner images change under us."""
    try:
        done = subprocess.run(  # noqa: S603
            [chrome, "--version"], capture_output=True, text=True, timeout=30, check=False
        )
        return (done.stdout or done.stderr).strip() or "unknown version"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown version"


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:  # keep CI logs readable
        pass


def run(root: Path, chrome: str, timeout: int) -> Outcome:
    handler = partial(_Quiet, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{HARNESS}"
        with tempfile.TemporaryDirectory() as profile:
            cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run"]
            if os.environ.get("CI"):
                cmd.append("--no-sandbox")  # CI containers; the page is our own static harness
            cmd += [f"--user-data-dir={profile}", "--virtual-time-budget=60000", "--dump-dom", url]
            try:
                done = subprocess.run(  # noqa: S603
                    cmd, capture_output=True, text=True, timeout=timeout, check=False
                )
            except subprocess.TimeoutExpired:
                return Outcome(False, f"Chrome did not finish within {timeout}s")
        if done.returncode != 0 and not done.stdout:
            return Outcome(False, f"Chrome exited {done.returncode}: {done.stderr[-300:]}")
        return parse_dom(done.stdout)
    finally:
        server.shutdown()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--chrome")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--require", action="store_true", help="a missing frontend is a failure")
    ap.add_argument("--min-tests", type=int, default=0, help="fail if fewer tests ran")
    args = ap.parse_args(argv)

    if not (args.root / HARNESS).is_file():
        if (args.root / "frontend").is_dir():
            print(f"FAIL: frontend/ exists but {HARNESS} is missing: the harness was removed")
            return 1
        msg = "no frontend/ directory: frontend browser tests not run"
        if args.require:
            print(f"FAIL: {msg} (--require)")
            return 1
        print(f"SKIPPED (not verified): {msg}")
        print(f"::notice::{msg}; the job is skipped, not passed")
        return 0
    chrome = find_chrome(args.chrome)
    if not chrome:
        print("FAIL: no Chrome or Chromium found (set CHROME or pass --chrome)")
        return 1
    print(f"browser: {browser_version(chrome)}")
    outcome = run(args.root, chrome, args.timeout)
    if outcome.ok and outcome.total < args.min_tests:
        outcome = Outcome(
            False,
            f"only {outcome.total} tests ran; at least {args.min_tests} are required "
            "(a test file may have been dropped from the harness)",
            (),
            outcome.total,
        )
    for line in outcome.failures:
        print(f"  {line}")
    print(f"{'OK' if outcome.ok else 'FAIL'}: frontend browser tests: {outcome.summary}")
    return 0 if outcome.ok else 1


if __name__ == "__main__":
    sys.exit(main())
