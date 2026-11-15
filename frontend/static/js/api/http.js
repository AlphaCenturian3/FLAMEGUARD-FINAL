// Adapter for the FastAPI backend (spec §5.1, contract v0.2.0). Integration
// point for Member 1: once an endpoint is implemented to the contract, no
// change is needed here.

import { ApiError, errorFromResponse } from "./errors.js";

/**
 * @param {{ baseUrl?: string, fetchImpl?: typeof fetch }} [options]
 * @returns {import("./types.js").DataSource}
 */
/** Response header the backend sets when it withheld evidence files that failed its checks. */
export const REJECTED_HEADER = "X-FlameGuard-Rejected-Entries";

/** @returns {number|null} 0 when absent, the count, or NaN when the header is present but unreadable */
export function parseRejectedHeader(value) {
  if (value === null || value === undefined) return 0;
  return /^\d+$/.test(String(value).trim()) ? Number(String(value).trim()) : NaN;
}

export function createHttpSource({ baseUrl = "", fetchImpl } = {}) {
  const doFetch = fetchImpl || ((...args) => fetch(...args));
  const root = baseUrl.replace(/\/+$/, "");
  /** Rejected-file count reported by the latest successful list responses (path -> count). */
  const rejectedByPath = new Map();

  async function request(method, path, body) {
    let res;
    try {
      res = await doFetch(root + path, {
        method,
        headers: body ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (err) {
      throw new ApiError(0, "network_error", `Could not reach the FlameGuard-SI API (${err && err.message ? err.message : "network error"}).`);
    }
    if (!res.ok) throw await errorFromResponse(res);
    if (method === "GET" && /^\/api\/(investigations|findings)(\?|$)/.test(path)) {
      rejectedByPath.set(path.split("?")[0], parseRejectedHeader(res.headers.get(REJECTED_HEADER)));
    }
    try {
      return await res.json();
    } catch {
      throw new ApiError(res.status, "invalid_json", "The API returned a response that is not valid JSON.");
    }
  }

  const enc = encodeURIComponent;
  return {
    kind: "api",
    description: root ? `FlameGuard-SI API at ${root}` : "FlameGuard-SI API (same origin)",
    /**
     * Files the backend withheld, as reported by the latest list responses. 0 means none were
     * reported. NaN means the header was present but unreadable. A browser only exposes this header
     * to a different-origin page if the backend sends Access-Control-Expose-Headers.
     */
    rejectedEntries() {
      const counts = [...rejectedByPath.values()];
      return counts.some(Number.isNaN) ? NaN : Math.max(0, ...counts);
    },
    health: () => request("GET", "/api/health"),
    listInvestigations: () => request("GET", "/api/investigations"),
    getInvestigation: (id) => request("GET", `/api/investigations/${enc(id)}`),
    listFindings: (investigationId) => request("GET", investigationId ? `/api/findings?investigation_id=${enc(investigationId)}` : "/api/findings"),
    compare(quantity, investigationIds = []) {
      const q = `quantity=${enc(quantity)}` + (investigationIds.length ? `&investigation_ids=${investigationIds.map(enc).join(",")}` : "");
      return request("GET", `/api/compare?${q}`);
    },
    getRankings: (context) => request("GET", `/api/rankings?context=${enc(context)}`),
    ask: (question, investigationIds = []) => request("POST", "/api/assistant/ask", investigationIds.length ? { question, investigation_ids: investigationIds } : { question }),
    getSimulation: (id) => request("GET", `/api/simulations/${enc(id)}`),
  };
}
