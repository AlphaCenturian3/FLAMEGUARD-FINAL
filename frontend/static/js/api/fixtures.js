// Fixture adapter (?fixtures=1). Reads the contract v0.2.0 examples in
// contracts/examples/ so the UI can be built before the backend serves data
// (spec §5.3).
//
// These files are FIXTURES with invented placeholder content. They are not
// NASA data, and the UI labels them as such on every page. Requests for which
// no example exists (another ranking context, another quantity) return a
// not_found error instead of an invented result.

import { ApiError } from "./errors.js";

export const FIXTURE_FILES = {
  health: "health.example.json",
  investigations: "investigation_list.example.json",
  findings: "finding_list.example.json",
  comparison: "comparison.example.json",
  ranking: "ranking.example.json",
  answer: "assistant_answer.example.json",
  simulation: "simulation_result.example.json",
};

/**
 * @param {{ baseUrl: string, fetchImpl?: typeof fetch }} options
 *   baseUrl: URL of the contracts/examples/ directory (trailing slash optional).
 * @returns {import("./types.js").DataSource}
 */
export function createFixtureSource({ baseUrl, fetchImpl }) {
  const doFetch = fetchImpl || ((...args) => fetch(...args));
  const root = baseUrl.endsWith("/") ? baseUrl : baseUrl + "/";
  const cache = new Map();

  async function load(name) {
    if (!cache.has(name)) {
      cache.set(
        name,
        (async () => {
          let res;
          try {
            res = await doFetch(root + name);
          } catch {
            throw new ApiError(0, "fixture_unavailable", `Could not load fixture ${name}. Serve the repository root over HTTP (see frontend/README.md).`);
          }
          if (!res.ok) throw new ApiError(res.status, "fixture_unavailable", `Fixture ${name} returned HTTP ${res.status}.`);
          return res.json();
        })(),
      );
    }
    // Return a copy so callers cannot mutate the cached fixture.
    return structuredClone(await cache.get(name));
  }

  return {
    kind: "fixtures",
    description: "Contract fixtures from contracts/examples/ (placeholder content, not NASA data)",
    health: () => load(FIXTURE_FILES.health),
    listInvestigations: () => load(FIXTURE_FILES.investigations),
    async getInvestigation(id) {
      const inv = (await load(FIXTURE_FILES.investigations)).items.find((i) => i.id === id);
      if (!inv) throw new ApiError(404, "not_found", `No fixture investigation with id ${id}.`);
      return inv;
    },
    async listFindings(investigationId) {
      const list = await load(FIXTURE_FILES.findings);
      if (!investigationId) return list;
      const items = list.items.filter((f) => f.investigation_id === investigationId);
      return { ...list, items, total: items.length };
    },
    async compare(quantity) {
      const cmp = await load(FIXTURE_FILES.comparison);
      if (cmp.quantity !== quantity) throw new ApiError(404, "not_found", `No fixture comparison for quantity ${quantity}. The only fixture is ${cmp.quantity}.`);
      return cmp;
    },
    async getRankings(context) {
      const r = await load(FIXTURE_FILES.ranking);
      if (r.context !== context) throw new ApiError(404, "not_found", `No fixture ranking for context ${context}. The only fixture is ${r.context}.`);
      return r;
    },
    ask: () => load(FIXTURE_FILES.answer),
    async getSimulation(id) {
      const sim = await load(FIXTURE_FILES.simulation);
      if (sim.id !== id) throw new ApiError(404, "not_found", `No fixture simulation with id ${id}.`);
      return sim;
    },
  };
}
