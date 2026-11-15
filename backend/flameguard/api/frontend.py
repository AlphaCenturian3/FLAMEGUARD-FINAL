"""B7: serve the static dashboard from the same origin as the API.

One process, one origin: `/api/*` is the API and everything else is the dashboard in `frontend/`.
The dashboard is plain static files (HTML, CSS, ES modules) with relative asset paths, so it needs
no build step and no CORS.

Safety rules, each tested:
- API routes are registered first and always win; an unknown `/api/...` path is a contract `Error`
  (JSON), never the dashboard's `index.html`, so a client can never mistake a missing endpoint
  for a page.
- There is no single-page-app fallback: an unknown file is a JSON 404 as well.
- The directory must contain `index.html`, otherwise the app refuses to start rather than serving
  half a dashboard.
- Demonstration fixtures are never served by default. `/contracts/examples/` exists only when the
  operator asks for it (`serve_fixtures_dir`), and only that folder is exposed. The dashboard still
  needs an explicit `?fixtures=1` to read it, labels every fixture page, and the API never returns
  fixture data: nothing here can switch from live evidence to fixtures silently.
- Responses carry `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer`; API
  responses are `Cache-Control: no-store` so evidence is never served stale from a cache.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles

from flameguard.data.loader import DEFAULT_ROOT

FRONTEND_ENV = "FLAMEGUARD_FRONTEND_DIR"
FIXTURES_ENV = "FLAMEGUARD_SERVE_FIXTURES"


class FrontendError(ValueError):
    """The dashboard directory cannot be served safely."""


def default_frontend_dir(root: Path | None = None) -> Path | None:
    """`$FLAMEGUARD_FRONTEND_DIR`, else `<repo>/frontend`, if it has an index.html; else None."""
    candidate = Path(os.environ.get(FRONTEND_ENV) or (root or DEFAULT_ROOT) / "frontend")
    return candidate if (candidate / "index.html").is_file() else None


def default_fixtures_dir(root: Path | None = None) -> Path | None:
    """The contract examples, only when `FLAMEGUARD_SERVE_FIXTURES=1`."""
    if os.environ.get(FIXTURES_ENV) != "1":
        return None
    examples = (root or DEFAULT_ROOT) / "contracts" / "examples"
    return examples if examples.is_dir() else None


def mount_frontend(
    app: FastAPI, frontend_dir: Path, serve_fixtures_dir: Path | None = None
) -> None:
    """Mount the dashboard (and optionally the labelled fixtures). Call after the API routes."""
    frontend_dir = Path(frontend_dir)
    if not (frontend_dir / "index.html").is_file():
        raise FrontendError(
            f"{frontend_dir} has no index.html; refusing to serve a partial dashboard"
        )

    @app.middleware("http")
    async def _headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    if serve_fixtures_dir is not None:
        app.mount(
            "/contracts/examples",
            StaticFiles(directory=Path(serve_fixtures_dir)),
            name="fixtures",
        )
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
