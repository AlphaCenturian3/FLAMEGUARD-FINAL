"""B2 evidence explorer: the three read-only endpoints of contract section 5.1.

    GET /api/investigations
    GET /api/investigations/{id}
    GET /api/findings?investigation_id=&evidence_class=&quantity=

Everything served comes from the B1 loader (`flameguard.data.load_evidence`): only documents that
passed strict JSON, provenance, schema and S1 to S4 / transitive S9 checks, and never a fixture,
a contract example or simulation data. With no registered evidence the lists are honestly empty.

Behaviour fixed by the contract (spec 5.1):
- every query parameter is optional; an unknown parameter NAME or VALUE returns 400
  `invalid_request`
- an unknown investigation id returns 404 `not_found`
- every response validates against its schema (`investigation_list`, `finding_list`,
  `investigation`, `error`)

Fail closed and honest:
- if the evidence cannot be loaded at all (manifest unreadable or invalid), every endpoint returns
  503 `unavailable`; nothing partial is served
- if some registered files were rejected, the rest is served, the rejection is logged with its
  reasons, and the response carries `X-FlameGuard-Rejected-Entries: <n>` so the omission is
  visible. The contract has no field for it, so this is a plain HTTP header.

Excluded findings are listed as `excluded` with a null value, and missing values as `not_reported`;
nothing is filled in, hidden or recomputed. Comparison, ranking and answers are not here.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from flameguard import CONTRACT_VERSION
from flameguard.data import LoadResult, load_evidence
from flameguard.data.loader import DEFAULT_ROOT

log = logging.getLogger("flameguard.api.explorer")

EVIDENCE_CLASSES = ("measured", "interpretation")
FINDING_PARAMS = frozenset({"investigation_id", "evidence_class", "quantity"})
REJECTED_HEADER = "X-FlameGuard-Rejected-Entries"


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


class EvidenceSource:
    """Loads the registered evidence once, lazily and thread-safely, through the B1 loader."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or os.environ.get("FLAMEGUARD_DATA_ROOT") or DEFAULT_ROOT)
        self._lock = threading.Lock()
        self._result: LoadResult | None = None
        self._quantities: frozenset[str] | None = None

    def load(self) -> LoadResult:
        with self._lock:
            if self._result is None:
                self._result = load_evidence(self.root)
                self._log(self._result)
            return self._result

    def refresh(self) -> LoadResult:
        """Drop the cache and load again (for operators and tests; data changes only on deploy)."""
        with self._lock:
            self._result = None
            self._quantities = None
        return self.load()

    def quantities(self) -> frozenset[str]:
        """The quantity keys of contracts/vocabulary.json: the only valid `quantity` filters."""
        with self._lock:
            if self._quantities is None:
                path = self.root / "contracts" / "vocabulary.json"
                doc = json.loads(path.read_text(encoding="utf-8"))
                self._quantities = frozenset(doc["quantities"])
            return self._quantities

    @staticmethod
    def _log(result: LoadResult) -> None:
        report = result.report
        if not report.manifest_ok:
            log.error("evidence not served: %s", "; ".join(report.manifest_errors)[:500])
            return
        for entry in report.rejected:
            log.warning("evidence entry rejected: %s: %s", entry.id, "; ".join(entry.reasons)[:500])
        log.info(
            "evidence loaded: %d investigations, %d findings, %d entries rejected",
            len(result.store.investigations),
            len(result.store.findings),
            len(report.rejected),
        )


router = APIRouter()


def _source(request: Request) -> EvidenceSource:
    return request.app.state.evidence_source


def _loaded(request: Request) -> tuple[LoadResult | None, JSONResponse | None]:
    """The load result, or the 503 to return. Fails closed: never partial data."""
    try:
        result = _source(request).load()
    except Exception:  # noqa: BLE001 - any loader failure must become a clean 503, never a 500
        log.exception("evidence load crashed")
        return None, error(503, "unavailable", "Evidence could not be loaded; see the server log.")
    if not result.report.manifest_ok:
        return None, error(503, "unavailable", "Evidence could not be loaded; see the server log.")
    return result, None


def _bad_params(request: Request, allowed: frozenset[str]) -> JSONResponse | None:
    names = [k for k, _ in request.query_params.multi_items()]
    unknown = sorted({n for n in names if n not in allowed})
    if unknown:
        return error(400, "invalid_request", f"Unknown query parameter(s): {', '.join(unknown)}.")
    repeated = sorted({n for n in names if names.count(n) > 1})
    if repeated:
        return error(
            400, "invalid_request", f"Query parameter given more than once: {', '.join(repeated)}."
        )
    return None


def _ok(result: LoadResult, content: dict[str, Any]) -> JSONResponse:
    headers = {}
    rejected = len(result.report.rejected)
    if rejected:
        headers[REJECTED_HEADER] = str(rejected)
    return JSONResponse(content=content, headers=headers)


def _envelope(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"contract_version": CONTRACT_VERSION, "items": items, "total": len(items)}


@router.get("/api/investigations")
def list_investigations(request: Request) -> JSONResponse:
    if (bad := _bad_params(request, frozenset())) is not None:
        return bad
    result, failure = _loaded(request)
    if failure is not None:
        return failure
    items = sorted(result.store.investigations, key=lambda i: i["id"])
    return _ok(result, _envelope(items))


@router.get("/api/investigations/{investigation_id}")
def get_investigation(investigation_id: str, request: Request) -> JSONResponse:
    if (bad := _bad_params(request, frozenset())) is not None:
        return bad
    result, failure = _loaded(request)
    if failure is not None:
        return failure
    for inv in result.store.investigations:
        if inv["id"] == investigation_id:
            return _ok(result, dict(inv))
    return error(404, "not_found", f"No investigation with id {investigation_id!r}.")


@router.get("/api/findings")
def list_findings(request: Request) -> JSONResponse:
    if (bad := _bad_params(request, FINDING_PARAMS)) is not None:
        return bad
    result, failure = _loaded(request)
    if failure is not None:
        return failure
    params = request.query_params
    findings = list(result.store.findings.values())

    inv_id = params.get("investigation_id")
    if inv_id is not None:
        known = {i["id"] for i in result.store.investigations} | {
            f["investigation_id"] for f in findings
        }
        if inv_id not in known:
            return error(400, "invalid_request", f"Unknown investigation_id {inv_id!r}.")
        findings = [f for f in findings if f["investigation_id"] == inv_id]

    cls = params.get("evidence_class")
    if cls is not None:
        if cls not in EVIDENCE_CLASSES:
            hint = " Simulations are not evidence." if cls == "illustrative_simulation" else ""
            return error(
                400,
                "invalid_request",
                f"evidence_class must be one of {', '.join(EVIDENCE_CLASSES)}; got {cls!r}.{hint}",
            )
        findings = [f for f in findings if f["evidence_class"] == cls]

    quantity = params.get("quantity")
    if quantity is not None:
        try:
            quantities = _source(request).quantities()
        except (OSError, ValueError, KeyError):
            log.exception("contracts/vocabulary.json unreadable")
            return error(503, "unavailable", "The quantity vocabulary could not be read.")
        if quantity not in quantities:
            return error(400, "invalid_request", f"Unknown quantity {quantity!r}.")
        findings = [f for f in findings if f.get("quantity") == quantity]

    findings.sort(key=lambda f: f["id"])
    return _ok(result, _envelope(findings))
