"""B3 endpoint handler: GET /api/compare?quantity=<key>&investigation_ids=a,b.

NOT SERVED. `flameguard.api.app` does not import this module and keeps `/api/compare` at HTTP 501
until the comparability logic is independently validated and approved (spec 4: review by
Member 5). There is deliberately no flag or environment variable that mounts it: serving it is a
reviewed code change to `app.py`. Tests mount `router` on a private application.

Behaviour (spec 5.1), same conventions as the B2 explorer:
- `quantity` is required and must be a vocabulary key; `investigation_ids` is optional, a
  comma-separated list of known investigation ids without repeats
- an unknown parameter name or value returns 400 `invalid_request`
- evidence that cannot be loaded returns 503 `unavailable`; nothing partial is served
- rejected registered files are announced in `X-FlameGuard-Rejected-Entries`
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from flameguard.api.explorer import _bad_params, _loaded, _ok, _source, error
from flameguard.compare import ComparisonError, build_comparison

log = logging.getLogger("flameguard.api.compare")

COMPARE_PARAMS = frozenset({"quantity", "investigation_ids"})

router = APIRouter()


def _units(request: Request) -> dict[str, str]:
    path = _source(request).root / "contracts" / "vocabulary.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {key: spec["unit"] for key, spec in doc["quantities"].items()}


@router.get("/api/compare")
def compare(request: Request) -> JSONResponse:
    if (bad := _bad_params(request, COMPARE_PARAMS)) is not None:
        return bad
    params = request.query_params
    quantity = params.get("quantity")
    if not quantity:
        return error(400, "invalid_request", "The quantity parameter is required.")
    try:
        units = _units(request)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        log.exception("contracts/vocabulary.json unreadable")
        return error(503, "unavailable", "The quantity vocabulary could not be read.")
    if quantity not in units:
        return error(400, "invalid_request", f"Unknown quantity {quantity!r}.")

    result, failure = _loaded(request)
    if failure is not None:
        return failure
    store = result.store

    ids = None
    raw = params.get("investigation_ids")
    if raw is not None:
        ids = raw.split(",")
        known = {i["id"] for i in store.investigations} | {
            f["investigation_id"] for f in store.findings.values()
        }
        unknown = sorted({i for i in ids if i not in known})
        if unknown:
            shown = ", ".join(repr(i) for i in unknown)
            return error(400, "invalid_request", f"Unknown investigation_ids value(s): {shown}.")
        if len(set(ids)) != len(ids):
            return error(400, "invalid_request", "investigation_ids lists an id more than once.")

    try:
        body = build_comparison(store, quantity, units[quantity], ids)
    except ComparisonError:
        log.exception("comparison refused")
        return error(503, "unavailable", "The comparison could not be built; see the server log.")
    return _ok(result, body)
