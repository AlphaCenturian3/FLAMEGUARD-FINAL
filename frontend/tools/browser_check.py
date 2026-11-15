#!/usr/bin/env python3
"""Cross-platform browser checks for the FlameGuard-SI dashboard (Q4).

    python frontend/tools/browser_check.py [--chrome PATH] [--out-dir DIR] [--headed]

Drives a real Chrome / Chromium / Edge through the Chrome DevTools Protocol: real key
events (Input.dispatchKeyEvent), real device-metrics emulation, real network. It needs only
Python 3.10+ and a Chrome-family browser; no packages (the WebSocket client below is a small
RFC 6455 implementation over the standard library).

It starts three local servers on 127.0.0.1, mirroring how the app is hosted:
  A  the repository root          -> /frontend/index.html, /contracts/examples/, test pages
  B  frontend/ at "/"             -> as FastAPI StaticFiles(directory="frontend") would serve it
  C  frontend/ at "/" plus a /contracts/examples/ mount

Fail closed: the exit code is 0 only if every check passed AND exactly the expected number
of checks ran (default 47). No browser, a crash, an exception, a skipped section or a missing
check is a failure. Each result prints as "ok   <name>" or "FAIL <name>  [detail]".

This is the portable successor of frontend/tools/browser-check.ps1 (same 47 checks).
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import fnmatch
import functools
import hashlib
import http.server
import json
import os
import posixpath
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CHECKS = 47
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
ROUTES = ["#/", "#/explorer", "#/compare", "#/rank", "#/interpret", "#/tars", "#/integrations"]


# --------------------------------------------------------------------------- results


class Results:
    """Collects checks. exit_code() is 0 only for a full, clean run."""

    def __init__(self, expected: int = EXPECTED_CHECKS, out=print) -> None:
        self.expected = expected
        self.items: list[tuple[bool, str, str]] = []
        self.aborted: str | None = None
        self._out = out

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        ok = bool(ok)
        self.items.append((ok, name, detail))
        self._out(f"{'ok  ' if ok else 'FAIL'} {name}{f'  [{detail}]' if detail else ''}")
        return ok

    def abort(self, reason: str) -> None:
        self.aborted = reason
        self._out(f"FAIL run aborted: {reason}")

    @property
    def failed(self) -> int:
        return sum(1 for ok, _, _ in self.items if not ok)

    def summary(self) -> str:
        total = len(self.items)
        line = f"{total - self.failed} passed, {self.failed} failed, {total} total"
        if self.expected and total != self.expected:
            line += f" (expected {self.expected} checks: INCOMPLETE)"
        if self.aborted:
            line += " (run aborted)"
        return line

    def exit_code(self) -> int:
        if self.aborted or self.failed or not self.items:
            return 1
        if self.expected and len(self.items) != self.expected:
            return 1
        return 0


def like(value: object, pattern: str) -> bool:
    """PowerShell `-like` semantics (case-insensitive glob), so the PS1 patterns port 1:1."""
    return fnmatch.fnmatchcase(str(value).lower(), pattern.lower())


# --------------------------------------------------------------------------- static servers

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".md": "text/plain; charset=utf-8",
}


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    """Serves `directory`; optionally mounts contracts/examples/ at /contracts/examples/.

    MIME types are fixed (Windows registry mappings can turn .js into text/plain, which
    browsers refuse for ES modules). Paths are normalised and confined to their root.
    """

    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME}
    contracts_dir: str | None = None

    def translate_path(self, path: str) -> str:
        clean = posixpath.normpath(urllib.parse.unquote(urllib.parse.urlsplit(path).path))
        if self.contracts_dir and clean.startswith("/contracts/examples/"):
            return confine(self.contracts_dir, clean[len("/contracts/examples/") :])
        return confine(self.directory, clean.lstrip("/"))

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args: object) -> None:  # keep output readable
        pass


def confine(root: str, rel: str) -> str:
    """Resolve `rel` under `root`; anything escaping the root maps to a path that 404s."""
    base = Path(root).resolve()
    target = (base / rel).resolve()
    if target != base and base not in target.parents:
        return str(base / "__outside_root__")
    return str(target)


def start_server(directory: Path, contracts: Path | None = None):
    handler = type(
        "Handler", (StaticHandler,), {"contracts_dir": str(contracts) if contracts else None}
    )
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(handler, directory=str(directory))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}/"


# --------------------------------------------------------------------------- browser


def find_chrome(explicit: str | None) -> str | None:
    """An explicit path (--chrome or CHROME) is authoritative: no silent fallback."""
    chosen = explicit or os.environ.get("CHROME")
    if chosen:
        return chosen if Path(chosen).exists() else None
    names = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
    paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in [*(shutil.which(n) for n in names), *paths]:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def launch_chrome(chrome: str, profile: str, headed: bool) -> tuple[subprocess.Popen, int]:
    args = [chrome, "--remote-debugging-port=0", f"--user-data-dir={profile}"]
    args += ["--no-first-run", "--no-default-browser-check", "--disable-gpu"]
    if not headed:
        args.insert(1, "--headless=new")
    if os.environ.get("CI"):
        args.append("--no-sandbox")  # CI containers; the pages are our own local files
    args.append("about:blank")
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
    port_file = Path(profile) / "DevToolsActivePort"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if port_file.exists():
            first = port_file.read_text(encoding="utf-8").splitlines()[:1]
            if first and first[0].strip().isdigit():
                return proc, int(first[0])
        if proc.poll() is not None:
            break
        time.sleep(0.1)
    proc.kill()
    raise RuntimeError("Chrome did not expose a DevTools port within 20 s")


def chrome_version(chrome: str) -> str:
    try:
        done = subprocess.run(  # noqa: S603
            [chrome, "--version"], capture_output=True, text=True, timeout=30, check=False
        )
        return (done.stdout or done.stderr).strip() or "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown (Windows Chrome does not print --version; see DevTools below)"


# --------------------------------------------------------------------------- websocket


def accept_key(key: str) -> str:
    digest = hashlib.sha1((key + WS_GUID).encode(), usedforsecurity=False).digest()
    return base64.b64encode(digest).decode()


def encode_frame(payload: bytes, opcode: int = 0x1, mask: bytes | None = None) -> bytes:
    """A single, final, masked client frame (RFC 6455 section 5.2)."""
    mask = mask if mask is not None else os.urandom(4)
    head = bytes([0x80 | opcode])
    n = len(payload)
    if n < 126:
        head += bytes([0x80 | n])
    elif n < 1 << 16:
        head += bytes([0x80 | 126]) + struct.pack("!H", n)
    else:
        head += bytes([0x80 | 127]) + struct.pack("!Q", n)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return head + mask + masked


def decode_frame(read) -> tuple[bool, int, bytes]:
    """Read one frame with `read(n)`. Returns (fin, opcode, payload); unmasks if masked."""
    b0, b1 = read(2)
    fin, opcode = bool(b0 & 0x80), b0 & 0x0F
    n = b1 & 0x7F
    if n == 126:
        (n,) = struct.unpack("!H", read(2))
    elif n == 127:
        (n,) = struct.unpack("!Q", read(8))
    mask = read(4) if b1 & 0x80 else None
    payload = read(n) if n else b""
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return fin, opcode, payload


class WebSocket:
    def __init__(self, url: str, timeout: float = 60) -> None:
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "ws":
            raise ValueError(f"only ws:// DevTools URLs are supported: {url}")
        self.sock = socket.create_connection((parts.hostname, parts.port or 80), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        path = parts.path + (f"?{parts.query}" if parts.query else "")
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {parts.hostname}:{parts.port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("DevTools closed the connection during the handshake")
            response += chunk
        head, self._buf = response.split(b"\r\n\r\n", 1)
        lines = head.decode("latin-1").split("\r\n")
        if " 101 " not in lines[0] + " ":
            raise ConnectionError(f"WebSocket handshake failed: {lines[0]}")
        headers = {
            k.strip().lower(): v.strip()
            for k, v in (h.split(":", 1) for h in lines[1:] if ":" in h)
        }
        if headers.get("sec-websocket-accept") != accept_key(key):
            raise ConnectionError("WebSocket handshake: bad Sec-WebSocket-Accept")

    def _read(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self.sock.recv(max(65536, n - len(self._buf)))
            if not chunk:
                raise ConnectionError("DevTools connection closed")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def send(self, text: str) -> None:
        self.sock.sendall(encode_frame(text.encode()))

    def recv(self) -> str:
        parts: list[bytes] = []
        while True:
            fin, opcode, payload = decode_frame(self._read)
            if opcode == 0x8:
                raise ConnectionError("DevTools sent a close frame")
            if opcode == 0x9:
                self.sock.sendall(encode_frame(payload, opcode=0xA))
                continue
            if opcode in (0x1, 0x2, 0x0):
                parts.append(payload)
                if fin:
                    return b"".join(parts).decode("utf-8")

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self.sock.sendall(encode_frame(b"", opcode=0x8))
        with contextlib.suppress(OSError):
            self.sock.close()


# --------------------------------------------------------------------------- CDP session

KEYS = {
    "Tab": ("Tab", 9, None),
    "Enter": ("Enter", 13, "\r"),
    "Escape": ("Escape", 27, None),
    "Space": ("Space", 32, " "),
}
SHIFT = 8

ACTIVE_JS = (
    "(() => { const e = document.activeElement; if (!e || e === document.body) return 'BODY';"
    " const s = getComputedStyle(e); const r = e.getBoundingClientRect();"
    " return [e.tagName, e.getAttribute('href') || e.id || e.dataset.action || e.name || e.type "
    "|| '',"
    " (e.getAttribute('aria-label') || e.textContent || e.value || '').trim().replace(/\\s+/g, ' "
    "').slice(0, 40),"
    " s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0 ? 'ring' : 'NO-RING',"
    " r.width > 0 && r.height > 0 && r.right > 0 && r.left < innerWidth ? 'visible' : "
    "'HIDDEN'].join(' | '); })()"
)


class Page:
    def __init__(self, ws: WebSocket, out_dir: Path) -> None:
        self.ws = ws
        self.out_dir = out_dir
        self._id = 0

    def cdp(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method} failed: {msg['error']}")
                return msg.get("result", {})

    def js(self, expression: str):
        res = self.cdp(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        if res.get("exceptionDetails"):
            return "JS-ERROR: " + str(res["exceptionDetails"].get("text"))
        return res.get("result", {}).get("value")

    def wait_for(self, expression: str, ms: int = 6000) -> bool:
        deadline = time.monotonic() + ms / 1000
        while time.monotonic() < deadline:
            if self.js(f"!!({expression})") is True:
                return True
            time.sleep(0.1)
        return False

    def press(self, key: str, modifiers: int = 0) -> None:
        code, vk, text = KEYS[key]
        name = " " if key == "Space" else key
        down = {
            "type": "keyDown" if text else "rawKeyDown",
            "key": name,
            "code": code,
            "windowsVirtualKeyCode": vk,
            "nativeVirtualKeyCode": vk,
            "modifiers": modifiers,
        }
        if text:
            down |= {"text": text, "unmodifiedText": text}
        self.cdp("Input.dispatchKeyEvent", down)
        self.cdp(
            "Input.dispatchKeyEvent",
            {
                "type": "keyUp",
                "key": name,
                "code": code,
                "windowsVirtualKeyCode": vk,
                "nativeVirtualKeyCode": vk,
                "modifiers": modifiers,
            },
        )
        time.sleep(0.08)

    def active(self) -> str:
        return str(self.js(ACTIVE_JS))

    def go(self, url: str) -> None:
        self.cdp("Page.navigate", {"url": url})
        time.sleep(0.3)
        self.wait_for("document.readyState === 'complete' && document.querySelector('#main h1')")
        time.sleep(0.4)

    def metrics(self, width: int, height: int, scale: float, mobile: bool) -> None:
        self.cdp(
            "Emulation.setDeviceMetricsOverride",
            {"width": width, "height": height, "deviceScaleFactor": scale, "mobile": mobile},
        )

    def shot(self, name: str) -> None:
        data = self.cdp("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})[
            "data"
        ]
        (self.out_dir / f"{name}.png").write_bytes(base64.b64decode(data))


# --------------------------------------------------------------------------- the 47 checks


def run_checks(p: Page, r: Results, repo: str, at_root: str, mounted: str) -> None:
    check = r.check
    base = f"{repo}frontend/index.html"

    # ---- desktop keyboard ----
    p.metrics(1280, 900, 1, False)
    p.go(f"{base}?fixtures=1#/")
    p.js(
        "sessionStorage.clear(); document.activeElement && document.activeElement.blur(); "
        "window.scrollTo(0,0); true"
    )
    p.go(f"{base}?fixtures=1#/")

    p.press("Tab")
    a = p.active()
    check(
        "Tab 1 focuses the skip link with a visible focus ring",
        like(a, "A | #main*ring*visible"),
        a,
    )
    p.press("Enter")
    a, h = p.active(), p.js("location.hash")
    check(
        "Skip link moves focus to main without changing the route",
        like(a, "MAIN*") and h == "#/",
        f"{a} ; hash={h}",
    )

    p.js("document.querySelector('.skip-link').focus(); true")
    seen, no_ring = [], []
    for _ in range(20):
        p.press("Tab")
        a = p.active()
        if a == "BODY":
            break  # tabbed past the last focusable element
        seen.append(a)
        if not like(a, "*| ring |*"):
            no_ring.append(a)
    for href in ROUTES:
        check(f"Nav link {href} reachable by Tab", any(like(s, f"A | {href} |*") for s in seen))
    check("Judge demo button reachable by Tab", any(like(s, "BUTTON*Judge demo*") for s in seen))
    check("Every Tab stop shows a visible focus ring", not no_ring, " / ".join(no_ring))
    print("     tab order: " + ", ".join(s.split(" | ")[1] for s in seen if " | " in s))

    p.js("document.querySelector('#nav a[href=\"#/explorer\"]').focus(); true")
    p.press("Enter")
    p.wait_for("location.hash === '#/explorer' && document.querySelector('.investigation')")
    a = p.active()
    check(
        "Enter on nav link opens Explorer and focuses its heading",
        p.js("location.hash") == "#/explorer" and like(a, "H1*Evidence Explorer*"),
        a,
    )

    p.js("document.querySelector('input[type=search]').focus(); true")
    p.cdp("Input.insertText", {"text": "zzzz-no-match"})
    empty = p.wait_for("document.querySelector('.results .state-empty')")
    check(
        "Typing a non-matching search shows the empty state",
        empty,
        str(p.js("document.querySelector('.result-count').textContent")),
    )
    p.js("const i = document.querySelector('input[type=search]'); i.select(); true")
    p.cdp("Input.insertText", {"text": "fixture"})
    found = p.wait_for("document.querySelectorAll('.results .investigation').length === 1")
    check(
        "Typing a matching search shows the record",
        found,
        str(p.js("document.querySelector('.result-count').textContent")),
    )

    p.js("document.querySelector('.compare-toggle input').focus(); true")
    p.press("Space")
    check(
        "Space toggles the Compare checkbox",
        p.js("document.querySelector('.compare-toggle input').checked") is True,
    )

    p.js("document.querySelector('.nav-demo').focus(); true")
    p.press("Enter")
    bar = p.wait_for(
        "!document.querySelector('.demo-bar').hidden && location.hash === '#/explorer'"
    )
    check("Enter on Judge demo starts the walkthrough at Discover", bar, str(p.js("location.hash")))
    p.js("document.querySelector('.demo-bar [data-action=exit]').focus(); true")
    p.press("Tab", SHIFT)
    p.press("Tab", SHIFT)
    a = p.active()
    check("Shift+Tab reaches the demo Next button", like(a, "BUTTON | next*"), a)
    p.press("Enter")
    p.wait_for("location.hash === '#/compare'")
    a, h = p.active(), p.js("location.hash")
    check(
        "Enter on Next advances to Compare and keeps focus in the demo bar",
        h == "#/compare" and like(a, "BUTTON | next*"),
        f"{a} ; hash={h}",
    )
    for _ in range(3):
        p.press("Enter")
        time.sleep(0.2)
    a = p.active()
    check(
        "Keyboard reaches the final Safety Insight step (button becomes Restart)",
        like(a, "BUTTON | next | Restart*") and p.js("location.hash") == "#/interpret",
        a,
    )
    p.shot("desktop-demo-insight")
    p.press("Enter")
    p.wait_for("location.hash === '#/explorer'")
    check("Restart returns to Discover", p.js("location.hash") == "#/explorer")
    p.js("document.querySelector('.demo-bar [data-action=exit]').focus(); true")
    p.press("Enter")
    check("Exit closes the demo bar", p.js("document.querySelector('.demo-bar').hidden") is True)

    # F8: theme toggle by keyboard
    p.js(
        "try { localStorage.removeItem('flameguard.theme') } catch (e) {} ; "
        "document.getElementById('theme-button').focus(); true"
    )
    before = p.js("getComputedStyle(document.body).backgroundColor")
    p.press("Enter")
    time.sleep(0.15)
    after = str(
        p.js(
            "[document.documentElement.dataset.theme, "
            "getComputedStyle(document.body).backgroundColor, "
            "document.getElementById('theme-button').getAttribute('aria-pressed')].join('|')"
        )
    )
    check(
        "Theme button toggles light/dark by keyboard and changes the page colours",
        not like(after, "|*") and after.split("|")[1] != before,
        f"{before} -> {after}",
    )
    p.shot("desktop-theme-toggled")
    p.press("Enter")
    p.js("try { localStorage.removeItem('flameguard.theme') } catch (e) {} ; true")

    # P3: backend comparison in fixture mode, operated by keyboard
    p.go(f"{base}?fixtures=1#/compare")
    p.wait_for("document.querySelector('#cmp-quantity')")
    p.js("document.querySelector('.compare-controls button[type=submit]').focus(); true")
    p.press("Enter")
    cmp_ok = p.wait_for(
        "/Backend decision/.test(document.querySelector('.compare-body').textContent)"
    )
    txt = str(p.js("document.querySelector('.compare-body').textContent"))
    check(
        "Compare: Enter requests /api/compare and shows the backend decision with its reasons "
        "verbatim, no chart",
        cmp_ok
        and like(txt, "*Not comparable*")
        and like(txt, "*pressure_kpa not reported for either row*")
        and p.js("!!document.querySelector('.compare-body svg')") is False,
    )

    # P4: ranking in fixture mode
    p.go(f"{base}?fixtures=1#/rank")
    rk = p.wait_for("document.querySelector('.ranking .rank-item')")
    txt = str(p.js("document.querySelector('main').textContent"))
    check(
        "Rank: fixture ranking shows criteria weights, criterion inputs and the not-ranked "
        "investigation",
        rk
        and like(txt, "*FIXTURE criterion A*")
        and like(txt, "*fixture-finding-interp-1*")
        and like(txt, "*Not ranked for Spacecraft*"),
    )

    # ---- mobile layout ----
    p.metrics(360, 780, 2, True)
    p.cdp("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
    for route in ROUTES:
        p.go(f"{base}?fixtures=1{route}")
        time.sleep(0.3)
        w = str(
            p.js(
                "[document.documentElement.scrollWidth, 360, [...document.querySelectorAll('body "
                "*')].filter(e => e.getBoundingClientRect().right > 360.5).slice(0, 4).map(e => "
                "e.tagName + '.' + (e.className || '')).join(',')].join('/')"
            )
        )
        check(
            f"Mobile 360px {route} has no horizontal scroll (page width <= 360 px)",
            int(w.split("/")[0]) <= 360,
            f"scrollWidth/limit/overflowing={w}",
        )
        banner = str(p.js("(document.querySelector('.banner-fixture') || {}).textContent || ''"))
        check(
            f"Fixture mode {route} shows the permanent 'FIXTURE DATA. NOT NASA DATA.' banner",
            like(banner, "*FIXTURE DATA. NOT NASA DATA.*"),
        )
        p.shot("mobile-" + (route.replace("#", "").replace("/", "") or "overview"))
    p.go(f"{base}?fixtures=1#/explorer")
    hidden_nav = p.js("getComputedStyle(document.getElementById('sidebar')).visibility")
    check(
        "Mobile: closed sidebar is hidden from Tab order", hidden_nav == "hidden", str(hidden_nav)
    )
    p.js("document.getElementById('menu-button').focus(); true")
    p.press("Enter")
    time.sleep(0.3)
    opened = p.js(
        "document.body.classList.contains('nav-open') + '/' + "
        "document.getElementById('menu-button').getAttribute('aria-expanded') + '/' + "
        "getComputedStyle(document.getElementById('sidebar')).visibility"
    )
    check(
        "Mobile: Enter on menu opens the sidebar (aria-expanded=true)",
        opened == "true/true/visible",
        str(opened),
    )
    p.shot("mobile-nav-open")
    p.press("Escape")
    time.sleep(0.3)
    a = p.active()
    closed = p.js("document.body.classList.contains('nav-open')")
    check(
        "Mobile: Escape closes the sidebar and returns focus to the menu button",
        closed is False and like(a, "BUTTON | menu-button*"),
        a,
    )

    # P2: FLEX-sized investigation (40 findings, 10 rows) at 360 px; test page, test records only.
    p.go(f"{repo}frontend/tests/layout.html")
    p.wait_for("document.body.dataset.ready === '1'")
    p.js("document.querySelectorAll('details.row-group').forEach(d => d.open = true); true")
    time.sleep(0.2)
    w = str(
        p.js(
            "[document.documentElement.scrollWidth, innerWidth, "
            "document.querySelectorAll('details.row-group').length, "
            "document.querySelectorAll('article.finding').length].join('/')"
        )
    )
    parts = w.split("/")
    check(
        "Mobile 360px: 40-finding investigation grouped into 10 rows, no horizontal scroll with "
        "every row open",
        len(parts) == 4 and int(parts[0]) <= 360 and parts[2] == "10" and parts[3] == "40",
        f"scrollWidth/innerWidth/rows/findings={w}",
    )
    p.shot("mobile-grouped-40")

    # ---- served at / (as FastAPI StaticFiles(directory="frontend") would) ----
    p.metrics(1280, 900, 1, False)
    p.go(f"{at_root}#/")
    assets = str(
        p.js(
            "[getComputedStyle(document.body).backgroundColor, document.querySelectorAll('#nav "
            "a').length].join('/')"
        )
    )
    check("Served at /: CSS and JS load via relative paths", like(assets, "*/7"), assets)
    api = p.wait_for(
        "document.querySelector('#health .badge') && "
        "/API/.test(document.querySelector('#health').textContent) && "
        "!/checking/.test(document.querySelector('#health').textContent)"
    )
    check(
        "Served at /: API mode calls /api/health at the same origin",
        api,
        str(p.js("document.querySelector('#health').textContent")),
    )

    # No fixture leak: without ?fixtures=1, every route never requests contracts/examples/.
    p.go(f"{mounted}#/")
    for route in [
        "#/explorer",
        "#/compare",
        "#/rank",
        "#/interpret",
        "#/tars",
        "#/integrations",
        "#/",
    ]:
        p.js(f"location.hash = '{route}'; true")
        time.sleep(0.5)
    leak = p.js(
        "performance.getEntriesByType('resource').filter(e => "
        "e.name.includes('contracts/examples')).map(e => e.name).join(' ')"
    )
    api_calls = p.js(
        "performance.getEntriesByType('resource').filter(e => e.name.includes('/api/')).length"
    )
    check(
        "No fixture leak: API mode on every route makes no request to contracts/examples/ (while "
        "/contracts/examples is reachable)",
        leak == "" and isinstance(api_calls, int) and api_calls > 0,
        f"leaked=[{leak}] apiRequests={api_calls}",
    )

    p.go(f"{at_root}?fixtures=1#/explorer")
    p.wait_for("document.querySelector('.results .state')")
    msg = str(p.js("(document.querySelector('.results .state') || {}).textContent || ''"))
    check(
        "Served at / with ?fixtures=1 and no /contracts/examples mount: explicit error, no data "
        "shown",
        like(msg, "*Fixture file could not be loaded*") and like(msg, "*HTTP 404*"),
        msg,
    )
    p.shot("served-at-root-fixtures-unmounted")
    p.go(f"{mounted}?fixtures=1#/explorer")
    ok = p.wait_for("document.querySelectorAll('.results .investigation').length === 1")
    check(
        "Served at / with /contracts/examples/ mounted: default fixture URL works unchanged",
        ok,
        str(p.js("location.href")),
    )


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--chrome", help="browser binary (authoritative; also CHROME env var)")
    ap.add_argument(
        "--out-dir", type=Path, default=Path(tempfile.gettempdir()) / "flameguard-browser-check"
    )
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    ap.add_argument(
        "--expected", type=int, default=EXPECTED_CHECKS, help="required number of checks (0 = any)"
    )
    ap.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = ap.parse_args(argv)

    results = Results(expected=args.expected)
    chrome = find_chrome(args.chrome)
    if not chrome:
        print("FAIL: no Chrome, Chromium or Edge found (set CHROME or pass --chrome)")
        return 2
    if not (args.root / "frontend" / "index.html").is_file():
        print(f"FAIL: {args.root / 'frontend' / 'index.html'} not found")
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"browser: {chrome}")
    print(f"version: {chrome_version(chrome)}")

    servers = []
    proc = None
    ws = None
    with tempfile.TemporaryDirectory(
        prefix="flameguard-cdp-", ignore_cleanup_errors=True
    ) as profile:
        try:
            repo_srv, repo = start_server(args.root)
            root_srv, at_root = start_server(args.root / "frontend")
            mount_srv, mounted = start_server(
                args.root / "frontend", contracts=args.root / "contracts" / "examples"
            )
            servers = [repo_srv, root_srv, mount_srv]
            proc, port = launch_chrome(chrome, profile, args.headed)
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/version", timeout=10
            ) as resp:  # noqa: S310
                print(f"devtools: {json.loads(resp.read()).get('Browser')}")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10) as resp:  # noqa: S310
                target = next(t for t in json.loads(resp.read()) if t.get("type") == "page")
            ws = WebSocket(target["webSocketDebuggerUrl"])
            page = Page(ws, args.out_dir)
            page.cdp("Page.enable")
            run_checks(page, results, repo, at_root, mounted)
        except Exception as exc:  # noqa: BLE001 - any error must fail the run, never pass it
            results.abort(f"{type(exc).__name__}: {exc}")
        finally:
            if ws:
                ws.close()
            if proc:
                proc.kill()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=10)
            for srv in servers:
                srv.shutdown()
    print()
    print(f"{results.summary()}. Screenshots: {args.out_dir}")
    return results.exit_code()


if __name__ == "__main__":
    sys.exit(main())
