"""One-command FlameGuard-SI development preview.

    python preview/run.py            # fetch, build, serve on http://127.0.0.1:8790/
    python preview/run.py --smoke    # same, then run API + browser smoke checks and stop

It exports two git refs (nothing is merged and no branch is changed) into `.preview/`
(git-ignored), installs that backend into `.preview/venv`, and serves it with
`preview/server.py`:

- backend + contracts from --backend-ref   (default origin/feat/backend-b2-explorer, PR #18)
- frontend/ only from --frontend-ref       (default origin/feat/frontend-dashboard, PR #2)

Safety: the AI key is forced blank, the server binds to 127.0.0.1, and unfinished endpoints
keep returning 501. Fixture data is shown only at `?fixtures=1` and is labelled there. The live
API serves only what the B1 loader accepts from the exported data/manifest.json (today: nothing,
so the lists are honestly empty). `--scenario` serves SYNTHETIC data for manual inspection only.
"""

from __future__ import annotations

import argparse
import io
import os
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request
import venv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenarios import SCENARIOS, make_scenario  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
WORK = REPO / ".preview"
DEFAULT_BACKEND = "origin/feat/backend-b2-explorer"
DEFAULT_FRONTEND = "origin/feat/frontend-dashboard"


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True).stdout  # noqa: S603, S607


def resolve(ref: str) -> str:
    return git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()


def export(sha: str, paths: list[str], dest: Path) -> None:
    data = git("archive", "--format=tar", sha, *paths)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")


def build(backend_sha: str, frontend_sha: str) -> Path:
    dest = WORK / f"build-{backend_sha[:12]}-{frontend_sha[:12]}"
    if not (dest / ".complete").exists():
        dest.mkdir(parents=True, exist_ok=True)
        paths = ["backend", "contracts", "data", "tools", "pyproject.toml", "README.md"]
        export(backend_sha, paths, dest)
        export(frontend_sha, ["frontend"], dest)
        (dest / ".complete").write_text(f"{backend_sha}\n{frontend_sha}\n", encoding="utf-8")
    return dest


def venv_python() -> Path:
    env_dir = WORK / "venv"
    py = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.exists():
        venv.create(env_dir, with_pip=True)
    return py


def install(py: Path, tree: Path) -> None:
    stamp = WORK / "venv" / "installed-from"
    if stamp.exists() and stamp.read_text(encoding="utf-8") == str(tree):
        return
    cmd = [str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check"]
    subprocess.run([*cmd, "--force-reinstall", str(tree)], check=True)  # noqa: S603
    stamp.write_text(str(tree), encoding="utf-8")


def serve(py: Path, tree: Path, port: int, data_root: Path | None = None) -> subprocess.Popen:
    env = {**os.environ, "FLAMEGUARD_PREVIEW_ROOT": str(tree), "FLAMEGUARD_AI_API_KEY": ""}
    # The backend is pip-installed, so its default data root would be inside site-packages.
    env["FLAMEGUARD_DATA_ROOT"] = str(data_root or tree)
    cmd = [str(py), "-m", "uvicorn", "server:app", "--app-dir", str(REPO / "preview")]
    cmd += ["--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"]
    return subprocess.Popen(cmd, env=env)  # noqa: S603


def require_free_port(port: int) -> None:
    """Fail clearly instead of silently talking to some other server already on the port."""
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(
                f"Port {port} is already in use (an older preview may still be running).\n"
                f"Stop it, or choose another port:  python preview/run.py --port {port + 1}"
            )


def wait_ready(url: str, seconds: float = 30) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url + "api/health", timeout=2):  # noqa: S310
                return
        except OSError:
            time.sleep(0.3)
    raise SystemExit(f"preview server did not start at {url}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--backend-ref", default=DEFAULT_BACKEND)
    ap.add_argument("--frontend-ref", default=DEFAULT_FRONTEND)
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--no-fetch", action="store_true", help="use refs as they are locally")
    ap.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS),
        help="serve SYNTHETIC evidence for manual inspection (never NASA data)",
    )
    ap.add_argument("--smoke", action="store_true", help="run smoke checks, then stop")
    args = ap.parse_args()

    if sys.version_info < (3, 11):  # noqa: UP036 (run.py may be started by an older python)
        raise SystemExit("Python 3.11+ is required")
    if not args.no_fetch:
        subprocess.run(["git", "fetch", "--quiet", "origin"], cwd=REPO, check=True)  # noqa: S603, S607
    require_free_port(args.port)
    b, f = resolve(args.backend_ref), resolve(args.frontend_ref)
    tree = build(b, f)
    py = venv_python()
    install(py, tree)
    url = f"http://127.0.0.1:{args.port}/"
    print("FlameGuard-SI DEVELOPMENT PREVIEW (not production; unfinished endpoints return 501)")
    print(f"  backend  {args.backend_ref} @ {b[:12]}")
    print(f"  frontend {args.frontend_ref} @ {f[:12]}")
    print(f"  live API mode : {url}")
    print(f"  fixture mode  : {url}?fixtures=1   (placeholder data, labelled not NASA data)")
    data_root = None
    if args.scenario:
        data_root = WORK / f"scenario-{args.scenario}"
        make_scenario(args.scenario, tree, data_root)
        print(f"  !! SYNTHETIC scenario {args.scenario!r}: NOT NASA DATA.")
        print("  !! The page will NOT say so. Use for local inspection only; never demo it.")
    proc = serve(py, tree, args.port, data_root)
    try:
        wait_ready(url)
        if args.smoke:
            smoke = [sys.executable, str(REPO / "preview" / "smoke.py"), url, str(tree), str(py)]
            return subprocess.run(smoke, check=False).returncode  # noqa: S603
        print("Press Ctrl+C to stop.")
        return proc.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
