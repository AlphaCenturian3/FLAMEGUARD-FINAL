// Adapter for the FastAPI backend (master spec §5.1). Integration point for
// the backend workstream: when an endpoint is implemented, no change is
// needed here as long as it follows the contract.

import { ApiError, errorFromResponse } from "./errors.js";

/**
 * @param {{ baseUrl?: string, fetchImpl?: typeof fetch }} [options]
 * @returns {import("./types.js").DataSource}
 */
export function createHttpSource({ baseUrl = "", fetchImpl } = {}) {
  const doFetch = fetchImpl || ((...args) => fetch(...args));
  const root = baseUrl.replace(/\/+$/, "");

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
    health: () => request("GET", "/api/health"),
    listInvestigations: () => request("GET", "/api/investigations"),
    getInvestigation: (id) => request("GET", `/api/investigations/${enc(id)}`),
    listFindings: (investigationId) =>
      request("GET", investigationId ? `/api/findings?investigation_id=${enc(investigationId)}` : "/api/findings"),
    getRankings: (context) => request("GET", `/api/rankings?context=${enc(context)}`),
    ask: (question) => request("POST", "/api/assistant/ask", { question }),
    getSimulation: (id) => request("GET", `/api/simulations/${enc(id)}`),
  };
}
