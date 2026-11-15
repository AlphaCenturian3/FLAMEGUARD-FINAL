"""FastAPI application.

Implemented: ``GET /api/health`` and the B2 evidence explorer (``explorer.py``). The other
endpoints of contract section 5.1 (compare, rankings, assistant, simulations) are planned and
return HTTP 501 with an ``Error`` body, so clients can code against them.

Every non-2xx response, including framework errors, is a contract ``Error`` object.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from flameguard import CONTRACT_VERSION
from flameguard.api.explorer import EvidenceSource, error, router

PLANNED_ENDPOINTS: list[tuple[str, str]] = [
    ("GET", "/api/compare"),
    ("GET", "/api/rankings"),
    ("POST", "/api/assistant/ask"),
    ("GET", "/api/simulations/{simulation_id}"),
]

_ERROR_CODES = {
    400: "invalid_request",
    404: "not_found",
    405: "invalid_request",
    422: "invalid_request",
}


def _not_implemented() -> JSONResponse:
    return error(
        501,
        "not_implemented",
        f"This endpoint is planned in contract v{CONTRACT_VERSION} and not implemented yet.",
    )


def create_app(evidence_source: EvidenceSource | None = None) -> FastAPI:
    """Build the application. Tests inject an `EvidenceSource` over a synthetic repository."""
    application = FastAPI(title="FlameGuard-SI", version=CONTRACT_VERSION)
    application.state.evidence_source = evidence_source or EvidenceSource()

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "flameguard-si", "contract_version": CONTRACT_VERSION}

    application.include_router(router)

    for method, path in PLANNED_ENDPOINTS:
        application.add_api_route(
            path,
            _not_implemented,
            methods=[method],
            status_code=501,
            include_in_schema=True,
            name=f"planned:{method} {path}",
        )

    @application.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _ERROR_CODES.get(exc.status_code, "unavailable")
        return error(exc.status_code, code, str(exc.detail))

    @application.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error(400, "invalid_request", "The request is not valid for this endpoint.")

    return application


app = create_app()
