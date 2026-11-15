"""Real-browser check of the running website (API + dashboard on one origin).

    python -m flameguard serve --fixtures          # in one terminal
    python frontend/tools/site_check.py http://127.0.0.1:8000/ [--excluded-value 0.37]

Drives Chrome through the DevTools Protocol (helpers from frontend/tools/browser_check.py,
standard library only) against the live server, not a static copy. Prints ok / FAIL / SKIP per
check and exits 0 only if no check failed. Screenshots go to --out-dir.

Checks: the seven routes in live and fixture mode (heading, no uncaught error, screenshot);
network isolation (live mode never requests contracts/examples, fixture mode never requests
/api data); the fixture banner text; API health and real /api responses; truthful 501 pages;
the excluded value withheld; 360 px layout and the mobile menu; the judge demo; an unreachable
API shows an error and never falls back to fixtures.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "frontend" / "tools"))

from browser_check import Page, WebSocket, find_chrome, launch_chrome  # noqa: E402

ROUTES = ["/", "/explorer", "/compare", "/rank", "/interpret", "/tars", "/integrations"]
BANNER = "FIXTURE DATA. NOT NASA DATA."


class Tally:
    def __init__(self) -> None:
        self.passed = self.failed = self.skipped = 0

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok or not detail else f"  [{detail}]"))
        return ok

    def skip(self, name: str, why: str) -> None:
        self.skipped += 1
        print(f"SKIP {name}  [{why}]")


class Session:
    """A page plus the network and console events seen since the last reset."""

    def __init__(self, page: Page) -> None:
        self.p = page
        self.requests: list[str] = []
        self.api: list[str] = []
        self.responses: dict[str, int] = {}
        self.errors: list[str] = []
        original = page.cdp

        def cdp(method, params=None):  # record events that arrive while waiting for replies
            page._id += 1
            page.ws.send(json.dumps({"id": page._id, "method": method, "params": params or {}}))
            while True:
                msg = json.loads(page.ws.recv())
                self._event(msg)
                if msg.get("id") == page._id:
                    if "error" in msg:
                        raise RuntimeError(f"CDP {method} failed: {msg['error']}")
                    return msg.get("result", {})

        page.cdp = cdp
        del original

    def _event(self, msg: dict) -> None:
        m, prm = msg.get("method"), msg.get("params", {})
        if m == "Network.requestWillBeSent":
            self.requests.append(prm["request"]["url"])
            if urlparse(prm["request"]["url"]).path.startswith("/api/"):
                self.api.append(prm["request"]["url"])
        elif m == "Network.responseReceived":
            self.responses[prm["response"]["url"]] = prm["response"]["status"]
        elif m == "Runtime.exceptionThrown":
            d = prm.get("exceptionDetails", {})
            self.errors.append((d.get("exception") or {}).get("description") or d.get("text", "?"))
        elif m == "Log.entryAdded" and prm["entry"].get("level") == "error":
            e = prm["entry"]
            self.errors.append(f"{e.get('source')}: {e.get('text')} {e.get('url', '')}")

    def go(self, url: str) -> None:
        """A full page load (a hash-only change would keep the app's cached evidence)."""
        self.p.cdp("Page.navigate", {"url": "about:blank"})
        time.sleep(0.2)
        self.reset()
        self.p.go(url)

    def real_errors(self) -> list[str]:
        """Console errors, except Chrome's resource line for an expected 501 (planned endpoint)."""
        return [e for e in self.errors if not (e.startswith("network:") and "status of 501" in e)]

    def reset(self) -> None:
        self.requests, self.responses, self.errors, self.api = [], {}, [], []

    def settle(self, ms: int = 6000) -> None:
        """Wait until the view has left its loading state."""
        self.p.wait_for(
            "document.querySelector('#main h1') && !document.querySelector('#main .state-loading')"
            " && !/Loading|Waiting/.test(document.querySelector('#main').innerText.slice(0, 400))",
            ms,
        )
        time.sleep(0.5)


def http_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:  # noqa: S310 - local server
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def run(s: Session, t: Tally, base: str, excluded_value: str | None) -> None:
    p = s.p
    status, health = http_json(base + "api/health")
    t.check(
        "GET /api/health is 200 with status ok",
        status == 200 and health.get("status") == "ok",
        str(health),
    )
    status, invs = http_json(base + "api/investigations")
    t.check(
        "GET /api/investigations is 200 with total == len(items)",
        status == 200 and invs.get("total") == len(invs.get("items", [])),
        str(invs)[:200],
    )
    if status != 200:
        return
    status, finds = http_json(base + "api/findings")
    t.check(
        "GET /api/findings is 200 with total == len(items)",
        status == 200 and finds.get("total") == len(finds.get("items", [])),
        str(finds)[:200],
    )
    if status != 200:
        return
    for path in ("api/compare?quantity=burn_time", "api/rankings"):
        status, body = http_json(base + path)
        t.check(
            f"GET /{path} is a truthful 501",
            status == 501 and body["error"]["code"] == "not_implemented",
        )
    n_findings = finds["total"]
    print(f"     (live evidence: {invs['total']} investigation(s), {n_findings} finding(s))")

    for mode, query in (("live", ""), ("fixture", "?fixtures=1")):
        for route in ROUTES:
            s.reset()
            s.go(f"{base}{query}#{route}")
            s.settle()
            name = route.strip("/") or "overview"
            h1 = p.js("document.querySelector('#main h1')?.textContent || ''")
            t.check(
                f"{mode} {route}: renders a page heading", bool(h1) and h1 != "Page not found", h1
            )
            t.check(
                f"{mode} {route}: no uncaught error or console error",
                not s.real_errors(),
                "; ".join(s.real_errors())[:300],
            )
            t.check(
                f"{mode} {route}: development-preview notice shown",
                p.js("document.body.innerText.includes('Development preview.')") is True,
            )
            banner = p.js(f"document.body.innerText.includes({json.dumps(BANNER)})")
            examples = [u for u in s.requests if "/contracts/examples/" in u]
            api = list(s.api)
            if mode == "live":
                t.check(f"live {route}: no fixture banner", banner is False)
                t.check(
                    f"live {route}: never requests contracts/examples",
                    not examples,
                    ", ".join(examples),
                )
                if route in ("/", "/explorer"):
                    t.check(
                        f"live {route}: data comes from the backend /api",
                        any(s.responses.get(u) == 200 for u in api),
                        ", ".join(f"{u}={s.responses.get(u)}" for u in api),
                    )
            else:
                t.check(f"fixture {route}: permanent banner '{BANNER}'", banner is True)
                t.check(
                    f"fixture {route}: no /api data request",
                    not [u for u in api if "/api/health" not in u],
                    ", ".join(api),
                )
            p.metrics(1280, 900, 1, False)
            p.shot(f"{mode}-{name}")
            p.cdp("Emulation.clearDeviceMetricsOverride")

    # Truthful 501 pages in live mode
    for route, word in (("/compare", "501"), ("/rank", "501")):
        s.reset()
        s.go(f"{base}#{route}")
        if route == "/compare":
            p.js(
                "document.querySelector('#main button.btn-primary, #main form button[type=submit]')"
                "?.click()"
            )
        s.settle()
        text = p.js("document.querySelector('#main').innerText")
        if n_findings == 0 and route == "/compare":
            t.check(
                "live /compare: with no evidence, says so and shows no fake comparison",
                "fixture" not in text.lower() or "not nasa" in text.lower(),
            )
        else:
            t.check(
                f"live {route}: states HTTP 501 / not implemented",
                word in text or "not implemented" in text.lower(),
                text[:200],
            )

    # Excluded value withheld (fixture explorer, and live if a value is given)
    s.reset()
    s.go(f"{base}?fixtures=1#/explorer")
    s.settle()
    text = p.js("document.body.innerText")
    t.check(
        "fixture explorer: excluded finding shown as excluded",
        "Excluded by FlameGuard-SI" in text or "excluded" in text.lower(),
    )
    if excluded_value:
        for mode, query in (("live", ""), ("fixture", "?fixtures=1")):
            for route in ("/", "/explorer", "/interpret"):
                s.go(f"{base}{query}#{route}")
                s.settle()
                p.js("document.querySelectorAll('details').forEach(d => d.open = true)")
                body = p.js("document.body.innerText")
                pat = r"(?<![\d.])0?" + re.escape(excluded_value.lstrip("0")) + r"(?!\d)"
                t.check(
                    f"{mode} {route}: excluded value {excluded_value} not on the page",
                    not re.search(pat, body),
                )
    else:
        t.skip(
            "live: excluded number absent from every page",
            "no excluded value registered (pass --excluded-value)",
        )

    # Mobile 360 px and the menu
    p.metrics(360, 780, 2, True)
    for route in ROUTES:
        s.go(f"{base}?fixtures=1#{route}")
        s.settle()
        over = p.js(
            "Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - 360"
        )
        t.check(
            f"360 px {route}: no horizontal overflow",
            isinstance(over, (int, float)) and over <= 1,
            f"overflow {over}px",
        )
    s.go(f"{base}#/")
    s.settle()
    p.js("document.getElementById('menu-button').click()")
    time.sleep(0.4)
    opened = p.js("document.getElementById('menu-button').getAttribute('aria-expanded')")
    p.shot("mobile-menu-open")
    p.js(
        "[...document.querySelectorAll('#sidebar a')]"
        ".find(a => a.getAttribute('href') === '#/explorer')?.click()"
    )
    time.sleep(0.8)
    t.check(
        "360 px: menu opens and navigates to the Explorer",
        opened == "true" and p.js("location.hash") == "#/explorer",
    )
    p.shot("mobile-explorer")
    p.cdp("Emulation.clearDeviceMetricsOverride")

    # Judge demo walkthrough in both modes
    for mode, query in (("live", ""), ("fixture", "?fixtures=1")):
        s.reset()
        s.go(f"{base}{query}#/")
        s.settle()
        p.js(
            "[...document.querySelectorAll('button')]"
            ".find(b => /Judge demo/.test(b.textContent)).click()"
        )
        time.sleep(0.6)
        steps = []
        for _ in range(8):
            steps.append(p.js("location.hash"))
            if not p.js("document.querySelector('[data-action=next]')?.textContent === 'Next'"):
                break
            p.js("document.querySelector('[data-action=next]').click()")
            time.sleep(0.9)
        p.shot(f"{mode}-demo-last-step")
        p.js("document.querySelector('[data-action=exit]')?.click()")
        t.check(
            f"{mode} judge demo: walks through five steps without errors",
            len(steps) == 5 and not s.real_errors(),
            f"{steps} {s.real_errors()[:2]}",
        )

    # Unreachable API: error shown, never a silent fixture fallback
    # Block the API only; "*/api/*" would also block the /static/js/api/ modules.
    p.cdp("Network.setBlockedURLs", {"urls": [base + "api/*"]})
    s.reset()
    s.go(f"{base}#/explorer")
    s.settle()
    text = p.js("document.querySelector('#main').innerText")
    p.shot("live-api-unreachable")
    examples = [u for u in s.requests if "/contracts/examples/" in u]
    t.check(
        "API unreachable: Explorer shows an error state",
        bool(re.search(r"error|unreachable|could not|failed", text, re.I)),
        text[:200],
    )
    t.check("API unreachable: no fallback to fixtures", not examples and BANNER not in text)
    p.cdp("Network.setBlockedURLs", {"urls": []})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("base", help="address the server printed, e.g. http://127.0.0.1:8000/")
    ap.add_argument("--chrome")
    ap.add_argument(
        "--out-dir", type=Path, default=Path(tempfile.gettempdir()) / "flameguard-site-check"
    )
    ap.add_argument("--excluded-value", help="a printed excluded number that must never appear")
    args = ap.parse_args(argv)
    base = args.base if args.base.endswith("/") else args.base + "/"
    chrome = find_chrome(args.chrome)
    if not chrome:
        print("FAIL: no Chrome or Edge found")
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t = Tally()
    with tempfile.TemporaryDirectory(prefix="fg-site-", ignore_cleanup_errors=True) as profile:
        proc, port = launch_chrome(chrome, profile, headed=False)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as r:  # noqa: S310
                target = next(x for x in json.loads(r.read()) if x.get("type") == "page")
            ws = WebSocket(target["webSocketDebuggerUrl"])
            page = Page(ws, args.out_dir)
            s = Session(page)
            for domain in ("Page", "Network", "Runtime", "Log"):
                page.cdp(f"{domain}.enable")
            run(s, t, base, args.excluded_value)
        except Exception as exc:  # noqa: BLE001 - an exception fails the run
            t.check("run completed", False, f"{type(exc).__name__}: {exc}")
        finally:
            proc.kill()
    print(
        f"\n{t.passed} passed, {t.failed} failed, {t.skipped} skipped. Screenshots: {args.out_dir}"
    )
    return 0 if t.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
