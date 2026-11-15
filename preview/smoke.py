"""Smoke checks for a running FlameGuard-SI development preview.

    python preview/smoke.py http://127.0.0.1:8790/ [EXPORTED_TREE PREVIEW_PYTHON]

With the two extra arguments (run.py --smoke passes them) it also starts throwaway servers on free
ports over SYNTHETIC evidence (preview/scenarios.py) to check excluded, rejected and 503 handling.
Those scenarios never touch the preview you are testing and are stopped afterwards.

API checks always run. Browser checks need Chrome, Chromium or Edge (set CHROME to override the
path); the judge-demo check also needs Node 22+. A check that cannot run is reported as SKIPPED
(not verified), never as passed. Exit code 1 means at least one check failed.
"""

from __future__ import annotations

import argparse
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import doc_check  # noqa: E402
import evidence_expect as ee  # noqa: E402
from scenarios import make_scenario  # noqa: E402

DEMO = doc_check.load_contract()

PLANNED = [
    ("GET", "api/compare?quantity=flame_spread_rate"),
    ("GET", "api/rankings?context=spacecraft"),
    ("POST", "api/assistant/ask"),
    ("GET", "api/simulations/x"),
]
ROUTES = ["", "explorer", "compare", "rank", "interpret", "integrations"]
FIXTURE_BANNER = DEMO["ui"]["fixture_banner"]
CONTRACT = "0.2.0"
REJECTED_HEADER = "x-flameguard-rejected-entries"
SCENARIO: dict = {"expect": "empty", "summary": None, "tree": None, "api_version": CONTRACT}
results: list[tuple[str, str, str]] = []  # (status, name, detail)


def record(ok: bool | None, name: str, detail: str = "") -> None:
    results.append(
        ("PASS" if ok else "SKIPPED (not verified)" if ok is None else "FAIL", name, detail)
    )


def http(method: str, url: str) -> tuple[int, bytes, dict[str, str]]:
    body = b'{"question": "smoke"}' if method == "POST" else None
    req = urllib.request.Request(  # noqa: S310 (http URL built from the preview base)
        url, data=body, method=method, headers={"content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
            return r.status, r.read(), {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, e.read(), {k.lower(): v for k, v in e.headers.items()}


def jget(url: str) -> tuple[int, dict, dict[str, str]]:
    code, body, headers = http("GET", url)
    try:
        return code, json.loads(body), headers
    except json.JSONDecodeError:
        return code, {}, headers


def err_code(doc: dict) -> str | None:
    return doc.get("error", {}).get("code")


def observe_evidence(base: str) -> dict:
    """What the live API serves right now (lists, statuses, header)."""
    _, inv, _ = jget(base + "api/investigations")
    code, fnd, headers = jget(base + "api/findings")
    items = fnd.get("items", [])
    by_status: dict[str, int] = {}
    for f in items:
        if f.get("evidence_class") == "measured":
            by_status[f["value_status"]] = by_status.get(f["value_status"], 0) + 1
    return {
        "investigations": {"total": inv.get("total"), "items": inv.get("items", [])},
        "findings": {"total": fnd.get("total"), "items": items},
        "ids": [f["id"] for f in items],
        "by_status": by_status,
        "excluded_values": [f.get("value") for f in items if f.get("value_status") == "excluded"],
        "rejected_header": headers.get(REJECTED_HEADER),
    }


def api_checks(base: str) -> None:
    code, doc, _ = jget(base + "api/health")
    record(code == 200 and doc.get("status") == "ok", "GET /api/health is 200 ok", f"{code} {doc}")
    SCENARIO["api_version"] = doc.get("contract_version", CONTRACT)
    for ok, name, detail in ee.api_verdicts(
        SCENARIO["expect"], SCENARIO["summary"], observe_evidence(base)
    ):
        record(ok, name, detail)
    code, doc, _ = jget(base + "api/investigations/x")
    record(code == 404 and err_code(doc) == "not_found", "unknown investigation is 404", str(code))
    for query, label in (
        ("?bogus=1", "unknown query parameter"),
        ("?evidence_class=illustrative_simulation", "simulation as evidence class"),
        ("?quantity=not_a_quantity", "unknown quantity"),
        ("?investigation_id=nope", "unknown investigation_id filter"),
    ):
        code, doc, _ = jget(base + "api/findings" + query)
        record(code == 400 and err_code(doc) == "invalid_request", f"{label} is 400", str(code))
    for method, path in PLANNED:
        code, body, _ = http(method, base + path)
        err = json.loads(body).get("error", {}) if body.startswith(b"{") else {}
        record(
            code == 501 and err.get("code") == "not_implemented",
            f"{method} /{path.split('?')[0]} stays 501 (no ranking, comparison or answer)",
            str(code),
        )
    code, _, _ = http("GET", base + "api/does-not-exist")
    record(code == 404, "unknown /api path is 404 (no static fallback)", str(code))
    code, body, _ = http("GET", base)
    record(code == 200 and b'id="source-banner"' in body, "GET / serves the frontend", str(code))
    code, _, _ = http("GET", base + "contracts/examples/health.example.json")
    record(code == 200, "contract fixtures served at /contracts/examples/", str(code))


def find_chrome() -> str | None:
    candidates = [
        os.environ.get("CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
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
    return subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=False).stdout  # noqa: S603


def text_of(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    return " ".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", html)).split())


def page(chrome: str, url: str, prof: str) -> tuple[str, str]:
    html = dump(chrome, url, prof)
    return html, text_of(html)


def browser_checks(base: str, chrome: str | None) -> None:
    if not chrome:
        record(None, "browser route checks", "no Chrome/Chromium found (set CHROME)")
        return
    with tempfile.TemporaryDirectory() as prof:
        for mode, query in (("fixture", "?fixtures=1"), ("live", "")):
            for route in ROUTES:
                html, t = page(chrome, f"{base}{query}#/{route}", prof)
                ok = "<h1" in html and "Page not found" not in t
                if mode == "fixture":
                    ok = ok and FIXTURE_BANNER in t
                else:  # live mode must never show fixtures as data
                    ok = ok and FIXTURE_BANNER not in t and "FIXTURE PLACEHOLDER" not in t
                    ok = ok and f"API · contract {SCENARIO['api_version']}" in t
                if route == "rank" and mode == "live":  # no ranking without approved evidence
                    ok = ok and "501" in t
                if route == "explorer" and mode == "live":
                    empty_state = "No investigations available" in t
                    ok = ok and (empty_state == (SCENARIO["expect"] == "empty"))
                h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
                record(ok, f"{mode} mode #/{route or ''}", text_of(h1.group(1)) if h1 else "no h1")
        _, t = page(chrome, f"{base}#/explorer", prof)
        foot = ee.footer_expectation(SCENARIO["tree"])
        declared, supported = foot["declared"], foot["supported"]
        api_v = SCENARIO["api_version"]
        ok = "Contract v0.1.0" not in t and "may be missing or misread" not in t
        ok = ok and re.search(r"[Cc]ontract v\d+\.\d+\.\d+", t) is not None
        if (
            declared
        ):  # the footer says what the dashboard itself declares, and tolerates the API's version
            ok = ok and f"contract v{declared}" in t and api_v in (supported or [])
        else:
            ok = ok and f"contract v{api_v}" in t
        record(
            ok,
            "footer states the contract version the API reports",
            f"api {api_v}, dashboard {declared}",
        )
        _, t = page(chrome, f"{base}?api=http://127.0.0.1:1#/explorer", prof)
        record(
            "could not be reached" in t and FIXTURE_BANNER not in t and "SYNTHETIC" not in t,
            "unreachable API: says so, never silently switches to fixtures",
            "",
        )


def doc_checks() -> None:
    """The demo documents must match the launcher and the demo contract (no browser needed)."""
    problems = doc_check.check(DEMO)
    record(
        not problems,
        "demo documents match the launcher and the demo contract",
        "; ".join(problems[:3]),
    )


def ui_contract_checks(base: str, chrome: str | None) -> None:
    """The running interface must still show the critical things the documents promise."""
    if not chrome:
        record(None, "demo contract against the interface", "no Chrome/Chromium found (set CHROME)")
        return
    ui = DEMO["ui"]
    with tempfile.TemporaryDirectory() as prof:
        for mode, query in (("live", ""), ("fixture", "?fixtures=1")):
            live_key = "live" if SCENARIO["expect"] == "empty" else "live_registered"
            for route, phrases in ui["fixture" if mode == "fixture" else live_key].items():
                _, t = page(chrome, f"{base}{query}{route}", prof)
                missing = [p for p in phrases if p not in t]
                record(
                    not missing,
                    f"contract, {mode} {route}: {', '.join(phrases)}",
                    f"missing {missing}" if missing else "",
                )
        _, t = page(chrome, f"{base}#/", prof)
        record(
            all(label in t for label in ui["nav_labels"]),
            "contract: documented navigation labels exist in the interface",
            "",
        )
        summary = SCENARIO["summary"]
        if SCENARIO["expect"] == "empty":
            record(
                re.search(r"\b0\s+Investigations loaded", t) is not None,
                "contract: live overview says 0 Investigations loaded",
                "",
            )
        elif summary is not None:
            record(
                re.search(rf"\b{summary['investigations']}\s+Investigations loaded", t) is not None
                and re.search(rf"\b{summary['measured']}\s+Measured findings", t) is not None,
                "contract: live overview counts equal the registered evidence",
                f"{summary['investigations']} investigation(s), {summary['measured']} finding(s)",
            )
        _, t = page(chrome, f"{base}?fixtures=1#/", prof)
        record(
            ui["demo_button"] in t and ui["fixture_banner"] in t,
            "contract: fixture overview shows the banner and the documented demo button",
            "",
        )
        _, t = page(chrome, f"{base}?fixtures=1#/explorer", prof)
        withheld = re.search(r"Excluded by FlameGuard-SI\s*[\u2014-]\s*value not shown", t)
        record(
            withheld is not None, "contract: a fixture excluded value is withheld, not shown", ""
        )
    code, body, _ = http("GET", base + "contracts/examples/finding.measured_excluded.example.json")
    record(
        code == 200 and json.loads(body).get("value") is None,
        "contract: the excluded fixture carries a null value",
        "",
    )


def illustration_checks(base: str, chrome: str | None) -> None:
    """The Blender images are served, labelled, and never presented as NASA data."""
    spec = DEMO["ui"]["illustrations"]
    code, body, _ = http("GET", base + "illustrations/")
    text = body.decode("utf-8", "replace")
    record(
        code == 200 and spec["banner"] in text,
        "illustrations page is served with the exact disclaimer",
        str(code),
    )
    for name in spec["images"]:
        code, body, _ = http("GET", base + "illustrations/" + name)
        record(
            code == 200 and body[:8] == b"\x89PNG\r\n\x1a\n" and name in text,
            f"illustration {name} is a PNG referenced by the labelled page",
            str(code),
        )
    if chrome:
        with tempfile.TemporaryDirectory() as prof:
            _, t = page(chrome, base + "illustrations/", prof)
            record(spec["banner"] in t, "browser: the illustrations page shows the disclaimer", "")


def registered_explorer_checks(base: str, chrome: str | None) -> None:
    """Registered scenario: the live Explorer shows exactly the registered evidence."""
    summary = SCENARIO["summary"]
    if SCENARIO["expect"] != "registered":
        return
    if not chrome or summary is None:
        record(None, "registered explorer checks", "needs Chrome and the exported tree")
        return
    with tempfile.TemporaryDirectory() as prof:
        html, t = page(chrome, f"{base}#/explorer", prof)
        rows = html.count('class="row-group"')
        record(
            rows == summary["groups"],
            "registered: one Explorer row per registered test",
            f"{rows} vs {summary['groups']}",
        )
        for status, n in sorted(summary["by_status"].items()):
            record(
                html.count(f'data-value-status="{status}"') == n,
                f"registered: Explorer shows {n} {status} value(s)",
                "",
            )
        record(
            all(f"Test end as printed: {o}" in t for o in summary["outcomes"]),
            "registered: the printed outcome labels appear verbatim",
            ", ".join(summary["outcomes"]),
        )
        record(
            FIXTURE_BANNER not in t
            and "FIXTURE PLACEHOLDER" not in t
            and "may be missing or misread" not in t,
            "registered: live mode shows no fixture banner and no version warning",
            "",
        )
        for ex in summary["excluded"]:
            printed = ex["printed"]
            if printed is None:
                record(
                    None,
                    f"registered: excluded value of {ex['id']} not disclosed",
                    "source value not found in the tree",
                )
                continue
            bare = printed[1:] if printed.startswith("0.") else printed
            leaked = any(re.search(rf"(?<![\d.]){re.escape(v)}(?!\d)", t) for v in {printed, bare})
            record(
                ex["value"] is None and not leaked,
                f"registered: excluded value of {ex['id']} is not disclosed",
                "",
            )


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def scenario_checks(tree: Path, py: Path, chrome: str | None) -> None:
    """SYNTHETIC evidence on throwaway ports: excluded, rejected and 503 handling end to end."""
    work = Path(tempfile.mkdtemp(prefix="fg-scenarios-"))
    procs: list[subprocess.Popen] = []
    try:
        urls = {}
        for name in ("synthetic", "rejected", "broken"):
            root = make_scenario(name, tree, work / name)
            port = free_port()
            env = {
                **os.environ,
                "FLAMEGUARD_PREVIEW_ROOT": str(tree),
                "FLAMEGUARD_DATA_ROOT": str(root),
                "FLAMEGUARD_AI_API_KEY": "",
            }
            cmd = [str(py), "-m", "uvicorn", "server:app", "--app-dir", str(HERE)]
            cmd += ["--host", "127.0.0.1", "--port", str(port), "--log-level", "critical"]
            procs.append(subprocess.Popen(cmd, env=env))  # noqa: S603
            urls[name] = f"http://127.0.0.1:{port}/"
        for base in urls.values():
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    http("GET", base + "api/health")
                    break
                except OSError:
                    time.sleep(0.3)

        base = urls["synthetic"]
        code, doc, hdr = jget(base + "api/findings")
        by_id = {f["id"]: f for f in doc.get("items", [])}
        ex = by_id.get("ex1", {})
        record(
            code == 200
            and ex.get("value_status") == "excluded"
            and ex.get("value") is None
            and by_id.get("mi1", {}).get("value_status") == "not_reported"
            and REJECTED_HEADER not in hdr,
            "synthetic: excluded value is null, missing stays not_reported, nothing rejected",
            f"ids={sorted(by_id)}",
        )
        code, doc, _ = jget(base + "api/findings?evidence_class=interpretation")
        record(
            code == 200 and [f["id"] for f in doc["items"]] == ["e1"],
            "synthetic: evidence_class filter returns only the exclusion explanation",
            "",
        )

        base = urls["rejected"]
        code, doc, hdr = jget(base + "api/findings")
        ids = sorted(f["id"] for f in doc.get("items", []))
        record(
            code == 200 and hdr.get(REJECTED_HEADER) == "1" and "e1" not in ids and "m1" in ids,
            "rejected: bad-checksum file withheld, rest served, header counts it",
            f"header={hdr.get(REJECTED_HEADER)} ids={ids}",
        )

        base = urls["broken"]
        for path in ("api/investigations", "api/investigations/x", "api/findings"):
            code, doc, _ = jget(base + path)
            record(code == 503 and err_code(doc) == "unavailable", f"broken: /{path} is 503", "")

        if not chrome:
            record(None, "scenario browser checks", "no Chrome/Chromium found (set CHROME)")
            return
        with tempfile.TemporaryDirectory() as prof:
            _, t = page(chrome, urls["synthetic"] + "#/explorer", prof)
            record(
                "Excluded by FlameGuard-SI" in t
                and "value not shown" in t
                and "SYNTHETIC investigation" in t
                and FIXTURE_BANNER not in t,
                "browser, synthetic evidence: excluded value is not shown",
                "",
            )
            _, t = page(chrome, urls["rejected"] + "#/explorer", prof)
            record(
                "SYNTHETIC investigation" in t and "Excluded by FlameGuard-SI" in t,
                "browser, rejected file: remaining evidence still renders",
                "",
            )
            _, main_js, _ = http("GET", urls["rejected"] + "static/js/main.js")
            if b"footer-contract" in main_js:  # frontend with the transparency fixes (PR #21)
                record(
                    "1 evidence file was rejected" in t and "incomplete" in t,
                    "browser, rejected file: the page says evidence was rejected and is incomplete",
                    "",
                )
                _, t = page(chrome, urls["synthetic"] + "#/explorer", prof)
                record(
                    "rejected by the backend" not in t,
                    "browser, nothing rejected: no rejected-files warning",
                    "",
                )
            else:
                record(None, "rejected-count display", "frontend predates PR #21")
            _, t = page(chrome, urls["broken"] + "#/explorer", prof)
            record(
                "HTTP 503" in t and "SYNTHETIC" not in t,
                "browser, 503: error shown, no data shown",
                "",
            )
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(work, ignore_errors=True)


def demo_checks(base: str, chrome: str | None) -> None:
    node = shutil.which("node")
    if not (chrome and node):
        record(None, "judge demo walkthrough", "needs Chrome and Node 22+")
        return
    for mode, query in (("fixture", "?fixtures=1"), ("live", "")):
        cmd = [node, str(HERE / "demo_check.mjs"), chrome, base + query]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)  # noqa: S603
        try:
            steps = json.loads(proc.stdout)
        except json.JSONDecodeError:
            record(False, f"judge demo ({mode})", (proc.stderr or proc.stdout)[-300:])
            continue
        titles = [s["title"] for s in steps]
        expected = DEMO["ui"]["demo_steps"]
        rank = next((s for s in steps if s["title"] == "Rank"), {})
        ok = titles == expected
        if mode == "fixture":  # the ranking shown here is a labelled contract example
            ok = ok and all(s["fixtureBanner"] for s in steps)
        else:  # live: the backend has no ranking, and the page must say so
            ok = ok and rank.get("shows501") is True
            ok = ok and not any(s["fixtureBanner"] for s in steps)
        record(ok, f"judge demo ({mode})", " -> ".join(f"{s['title']}@{s['hash']}" for s in steps))


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("base", nargs="?", default="http://127.0.0.1:8790/")
    ap.add_argument("tree", nargs="?", type=Path)
    ap.add_argument("py", nargs="?", type=Path)
    ap.add_argument(
        "--expect",
        choices=ee.EXPECTATIONS,
        default="auto",
        help="empty: live evidence must be honestly empty; registered: it must equal what the "
        "tree registers; auto (default): decide from the tree, or the API without a tree",
    )
    return ap.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    base = args.base.rstrip("/") + "/"
    _, probe, _ = jget(base + "api/findings")
    scenario, summary = ee.decide(args.expect, args.tree, probe.get("total"))
    SCENARIO.update(expect=scenario, summary=summary, tree=args.tree)
    print(f"evidence scenario: {scenario} (--expect {args.expect})")
    doc_checks()
    api_checks(base)
    chrome = find_chrome()
    browser_checks(base, chrome)
    ui_contract_checks(base, chrome)
    registered_explorer_checks(base, chrome)
    illustration_checks(base, chrome)
    if args.tree is not None and args.py is not None:
        scenario_checks(args.tree, args.py, chrome)
    else:
        record(None, "synthetic scenario checks", "pass EXPORTED_TREE and PREVIEW_PYTHON")
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
