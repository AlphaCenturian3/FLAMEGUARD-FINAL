// Fixture adapter. Reads the contract examples in contracts/examples/ so the
// UI can be built before the backend serves data (master spec §5.3).
//
// These files are FIXTURES with invented placeholder content. They are not
// NASA data, and the UI labels them as such everywhere they appear.
// No fixture exists for rankings or the assistant, so those return the
// contract's not_implemented error instead of invented results.

import { ApiError } from "./errors.js";

export const FIXTURE_FILES = {
  investigation: "investigation.example.json",
  findingMeasured: "finding.measured.example.json",
  findingInterpretation: "finding.interpretation.example.json",
  simulation: "simulation_result.example.json",
  health: "health.example.json",
  notImplemented: "error.not_implemented.example.json",
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
          } catch (err) {
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

  async function notImplemented() {
    const body = await load(FIXTURE_FILES.notImplemented);
    throw new ApiError(501, body.error.code, body.error.message);
  }

  async function findings() {
    return [await load(FIXTURE_FILES.findingMeasured), await load(FIXTURE_FILES.findingInterpretation)];
  }

  return {
    kind: "fixtures",
    description: "Contract fixtures from contracts/examples/ (placeholder content, not NASA data)",
    health: () => load(FIXTURE_FILES.health),
    async listInvestigations() {
      const health = await load(FIXTURE_FILES.health);
      return { items: [await load(FIXTURE_FILES.investigation)], contract_version: health.contract_version };
    },
    async getInvestigation(id) {
      const inv = await load(FIXTURE_FILES.investigation);
      if (inv.id !== id) throw new ApiError(404, "not_found", `No fixture investigation with id ${id}.`);
      return inv;
    },
    async listFindings(investigationId) {
      const health = await load(FIXTURE_FILES.health);
      const all = await findings();
      return {
        items: investigationId ? all.filter((f) => f.investigation_id === investigationId) : all,
        contract_version: health.contract_version,
      };
    },
    getRankings: notImplemented,
    ask: notImplemented,
    async getSimulation(id) {
      const sim = await load(FIXTURE_FILES.simulation);
      if (sim.id !== id) throw new ApiError(404, "not_found", `No fixture simulation with id ${id}.`);
      return sim;
    },
  };
}
