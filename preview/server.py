"""FlameGuard-SI DEVELOPMENT PREVIEW server. Not production, and not B7.

`/api/*` goes to the unmodified production FastAPI app (`flameguard.api.app`), so every
planned endpoint still returns its HTTP 501. Everything else is static files:

- `/contracts/examples/*` -> the contract fixtures (the frontend labels them "not NASA data")
- `/*`                    -> the frontend

This module adds no routes, scores, data or fallbacks, and nothing in `backend/` imports it.
`FLAMEGUARD_PREVIEW_ROOT` points at a tree exported by `preview/run.py` (git archive of the
chosen refs). It binds to 127.0.0.1 only through run.py.
"""

import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from flameguard.api.app import app as production_app

ROOT = Path(os.environ["FLAMEGUARD_PREVIEW_ROOT"]).resolve()

static_app = Starlette(
    routes=[
        Mount(
            "/contracts/examples",
            app=StaticFiles(directory=ROOT / "contracts" / "examples"),
        ),
        Mount("/", app=StaticFiles(directory=ROOT / "frontend", html=True)),
    ]
)


async def app(scope, receive, send):
    path = scope.get("path", "")
    if scope["type"] == "lifespan" or path == "/api" or path.startswith("/api/"):
        await production_app(scope, receive, send)
    else:
        await static_app(scope, receive, send)
