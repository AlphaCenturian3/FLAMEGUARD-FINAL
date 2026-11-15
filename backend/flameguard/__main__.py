"""One command for the complete application: API and dashboard on one origin.

    python -m flameguard serve                 # http://127.0.0.1:8000/
    python -m flameguard serve --auto-port --open
    python -m flameguard serve --fixtures      # also allow the labelled demo page ?fixtures=1

Only the evidence registered in data/manifest.json and accepted by the B1 loader is shown. If none
is registered, the dashboard says so. Fixtures are off unless `--fixtures` is given; even then the
dashboard needs `?fixtures=1`, labels every page, and the API never returns fixture data.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

DEFAULT_PORT = 8000


def port_is_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket() as sock:
        return sock.connect_ex((host, port)) != 0


def pick_port(start: int, tries: int = 10, host: str = "127.0.0.1") -> int:
    for port in range(start, start + tries):
        if port_is_free(port, host):
            return port
    raise SystemExit(f"No free port between {start} and {start + tries - 1}.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m flameguard", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="run the API and the dashboard on one origin")
    serve.add_argument("--host", default="127.0.0.1", help="default: this computer only")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--auto-port", action="store_true", help="use the next free port if busy")
    serve.add_argument("--open", action="store_true", help="open the dashboard once it is ready")
    serve.add_argument(
        "--fixtures", action="store_true", help="allow the labelled ?fixtures=1 demo"
    )
    serve.add_argument(
        "--data-root", type=Path, help="repository root holding data/ (default: this repo)"
    )
    serve.add_argument("--frontend-dir", type=Path, help="default: <repo>/frontend")
    return ap


def evidence_summary(source) -> str:
    result = source.load()
    report = result.report
    if not report.manifest_ok:
        return (
            "evidence: UNAVAILABLE ("
            + "; ".join(report.manifest_errors)[:200]
            + "); the API will answer 503"
        )
    parts = [
        f"{len(result.store.investigations)} investigation(s)",
        f"{len(result.store.findings)} finding(s)",
        f"{len(report.rejected)} rejected file(s)",
    ]
    note = "" if result.store.findings else "  (nothing registered: the dashboard will say so)"
    return "evidence: " + ", ".join(parts) + note


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)  # the address must appear even when piped
    import uvicorn

    from flameguard.api.app import create_app
    from flameguard.api.explorer import EvidenceSource
    from flameguard.api.frontend import FrontendError, default_frontend_dir
    from flameguard.data.loader import DEFAULT_ROOT

    root = (args.data_root or DEFAULT_ROOT).resolve()
    frontend = args.frontend_dir or default_frontend_dir(root)
    if frontend is None or not (Path(frontend) / "index.html").is_file():
        print(
            f"No dashboard found (looked for {root / 'frontend'}/index.html). Set --frontend-dir."
        )
        return 2
    fixtures = root / "contracts" / "examples" if args.fixtures else None
    if fixtures is not None and not fixtures.is_dir():
        print(f"--fixtures needs {fixtures}")
        return 2
    port = pick_port(args.port, host=args.host) if args.auto_port else args.port
    if port != args.port:
        print(f"Port {args.port} is busy; using {port} instead.")
    elif not port_is_free(port, args.host):
        print(f"Port {port} is already in use. Choose another with --port or use --auto-port.")
        return 2
    source = EvidenceSource(root)
    try:
        application = create_app(source, Path(frontend), fixtures)
    except FrontendError as exc:
        print(f"Cannot start: {exc}")
        return 2
    os.environ["FLAMEGUARD_AI_API_KEY"] = ""  # no AI is called by this application yet
    shown = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host  # noqa: S104
    url = f"http://{shown}:{port}/"
    print("FlameGuard-SI (complete application: API + dashboard, one origin)")
    print(f"  data root : {root}")
    print(f"  dashboard : {frontend}")
    print(f"  {evidence_summary(source)}")
    print(
        "  compare, rankings, assistant and simulations are not implemented: they answer HTTP 501"
    )
    if args.fixtures:
        print(f"  fixtures  : {url}?fixtures=1 (placeholder data, labelled NOT NASA DATA)")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"  WARNING: listening on {args.host}: reachable from other computers.")
    print(f"OPEN THIS ADDRESS: {url}")
    print("Press Ctrl+C to stop.")
    if args.open:

        def opener() -> None:
            for _ in range(100):
                try:
                    urllib.request.urlopen(url + "api/health", timeout=1)  # noqa: S310
                    webbrowser.open(url)
                    return
                except OSError:
                    time.sleep(0.2)

        threading.Thread(target=opener, daemon=True).start()
    uvicorn.run(application, host=args.host, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
