// Test-only records. Every one is marked fixture: true, uses obviously fake
// IDs and example.invalid URLs, and is never loaded by the app.

export const SRC = { title: "TEST SOURCE", url: "https://example.invalid/test", retrieved: "2026-11-14" };

export function inv(id, extra = {}) {
  return { fixture: true, id, name: `TEST INVESTIGATION ${id}`, acronym: null, platform: null, objectives: [], relevant_environments: [], sources: [SRC], ...extra };
}

export function measured(id, investigationId, extra = {}) {
  return {
    fixture: true,
    id,
    investigation_id: investigationId,
    evidence_class: "measured",
    statement: `TEST measured ${id}`,
    value: null,
    unit: null,
    uncertainty: null,
    provenance: { manifest_id: "test-dataset", sources: [SRC] },
    ...extra,
  };
}

export function interpretation(id, investigationId, derivedFrom, extra = {}) {
  return {
    fixture: true,
    id,
    investigation_id: investigationId,
    evidence_class: "interpretation",
    statement: `TEST interpretation ${id}`,
    provenance: { derived_from: derivedFrom, method: "test-method v0", generated_by: "FlameGuard-SI" },
    ...extra,
  };
}

export function simulation(id, investigationId, extra = {}) {
  return {
    fixture: true,
    id,
    investigation_id: investigationId,
    evidence_class: "illustrative_simulation",
    statement: `TEST simulation ${id}`,
    label: "Fluid and thermal transport model. No combustion chemistry.",
    provenance: { model: "test-model", model_version: "0.0.0" },
    ...extra,
  };
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
