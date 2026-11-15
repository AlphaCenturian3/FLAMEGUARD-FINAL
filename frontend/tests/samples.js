// Test record builders. The base records live in tests/fixtures/frontend/
// (spec §2.2: mock data only in tests/fixtures/). This module only clones
// them and applies per-test overrides such as an ID, a value or a status.

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

/** Reported measured finding (v0.2.0). */
export function measured(id, investigationId, extra = {}) {
  return { ...clone(BASE.measured), id, investigation_id: investigationId, statement: `TEST measured ${id}`, ...extra };
}

/** Measured finding the source does not report. */
export function notReported(id, investigationId, extra = {}) {
  return measured(id, investigationId, { value: null, value_status: "not_reported", ...extra });
}

export function note(kind = "caution", extra = {}) {
  return { ...clone(BASE.curation_note), kind, note: `TEST ${kind} note`, ...extra };
}

/** Measured finding excluded by FlameGuard-SI, with its exclusion note. */
export function excluded(id, investigationId, extra = {}) {
  return measured(id, investigationId, { value: null, value_status: "excluded", curation_notes: [note("exclusion", { note: `TEST exclusion reason for ${id}` })], ...extra });
}

export function interpretation(id, investigationId, derivedFrom, extra = {}) {
  const base = clone(BASE.interpretation);
  base.provenance.derived_from = derivedFrom;
  return { ...base, id, investigation_id: investigationId, statement: `TEST interpretation ${id}`, ...extra };
}

/** A simulation dressed as a Finding: invalid in v0.2.0, used only to test rejection. */
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

export const byId = (fs) => new Map(fs.map((f) => [f.id, f]));
