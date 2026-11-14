// Test record builders. The base records live in tests/fixtures/frontend/
// (spec §2.2: mock data only in tests/fixtures/). This module only clones
// them and applies per-test overrides such as an ID or a value.

const RECORDS_URL = new URL("../../tests/fixtures/frontend/records.json", import.meta.url);
const res = await fetch(RECORDS_URL);
if (!res.ok) throw new Error(`Could not load ${RECORDS_URL} (HTTP ${res.status}). Serve the repository root.`);
const BASE = await res.json();

for (const key of ["investigation", "measured", "interpretation", "illustrative_simulation"]) {
  if (BASE[key].fixture !== true) throw new Error(`tests/fixtures/frontend/records.json: ${key} must be marked fixture: true`);
}

const clone = (x) => structuredClone(x);

export const SRC = clone(BASE.source);

export function inv(id, extra = {}) {
  return { ...clone(BASE.investigation), id, name: `TEST INVESTIGATION ${id}`, ...extra };
}

export function measured(id, investigationId, extra = {}) {
  return { ...clone(BASE.measured), id, investigation_id: investigationId, statement: `TEST measured ${id}`, ...extra };
}

export function interpretation(id, investigationId, derivedFrom, extra = {}) {
  const base = clone(BASE.interpretation);
  base.provenance.derived_from = derivedFrom;
  return { ...base, id, investigation_id: investigationId, statement: `TEST interpretation ${id}`, ...extra };
}

export function simulation(id, investigationId, extra = {}) {
  return { ...clone(BASE.illustrative_simulation), id, investigation_id: investigationId, statement: `TEST simulation ${id}`, ...extra };
}

/** fetch stub returning a fixed status and JSON body. */
export function stubFetch(status, body) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url, init });
    return new Response(typeof body === "string" ? body : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  };
  fn.calls = calls;
  return fn;
}
