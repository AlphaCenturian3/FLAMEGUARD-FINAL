"""FastAPI application.

Only ``/api/health`` is implemented. Endpoints planned in contract v0 (master spec
section 5.1) return HTTP 501 with an ``Error`` body so clients can code against them.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from flameguard import CONTRACT_VERSION

app = FastAPI(title="FlameGuard-SI", version=CONTRACT_VERSION)

PLANNED_ENDPOINTS: list[tuple[str, str]] = [
    ("GET", "/api/investigations"),
    ("GET", "/api/investigations/{investigation_id}"),
    ("GET", "/api/findings"),
    ("GET", "/api/compare"),
    ("GET", "/api/rankings"),
    ("POST", "/api/assistant/ask"),
    ("GET", "/api/simulations/{simulation_id}"),
]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "flameguard-si", "contract_version": CONTRACT_VERSION}


def _not_implemented() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "error": {
                "code": "not_implemented",
                "message": (
                    f"This endpoint is planned in contract v{CONTRACT_VERSION} "
                    "and not implemented yet."
                ),
            }
        },
    )


for _method, _path in PLANNED_ENDPOINTS:
    app.add_api_route(
        _path,
        _not_implemented,
        methods=[_method],
        status_code=501,
        include_in_schema=True,
        name=f"planned:{_method} {_path}",
    )
