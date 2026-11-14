// Comparison display rules (P3). The backend decides comparability
// (GET /api/compare; spec §4.2, §4.3). This module never decides whether
// values are comparable and never fills a missing value. It only checks that a
// response it is about to chart is consistent with the contract, and fails
// closed (no chart) when it is not.

import { traceSupport } from "./trace.js";

/**
 * @param {import("../api/types.js").Comparison} resp
 * @param {Map<string, import("../api/types.js").Finding>} [findingsById]
 * @returns {{ chartable: boolean, problems: string[] }}
 */
export function reviewComparison(resp, findingsById = new Map()) {
  const problems = [];
  const rows = resp && Array.isArray(resp.rows) ? resp.rows : [];
  if (!resp || typeof resp.comparable !== "boolean") problems.push("The response has no comparable decision.");
  if (resp && resp.comparable === false && !(resp.non_comparable_reasons || []).length) problems.push("The backend marked this not comparable but gave no reason.");

  if (resp && resp.comparable === true) {
    if (rows.length < 2) problems.push("Marked comparable with fewer than two rows.");
    for (const row of rows) {
      if (row.value_status !== "reported" || typeof row.value !== "number" || !Number.isFinite(row.value)) {
        problems.push(`Marked comparable, but row ${row.finding_id} has no reported numeric value.`);
      }
      if (row.evidence_class !== "measured") problems.push(`Row ${row.finding_id} is not measured evidence.`);
      // S5: every row's finding_id resolves to a measured finding with the same quantity and unit.
      // Consistency check only: comparability itself stays the backend's decision.
      const loaded = findingsById.get(row.finding_id);
      if (!loaded) {
        problems.push(`Row ${row.finding_id} does not resolve to a loaded finding (S5).`);
        continue;
      }
      if (loaded.evidence_class !== "measured") problems.push(`Row ${row.finding_id} resolves to a ${loaded.evidence_class} finding, not measured (S5).`);
      if (loaded.quantity !== resp.quantity) problems.push(`Row ${row.finding_id}: loaded finding quantity ${loaded.quantity} differs from ${resp.quantity} (S5).`);
      if (loaded.unit !== resp.unit) problems.push(`Row ${row.finding_id}: loaded finding unit ${loaded.unit} differs from ${resp.unit} (S5).`);
      if (loaded.value_status !== "reported" || loaded.value !== row.value) problems.push(`Row ${row.finding_id}: row value ${row.value} differs from the loaded finding's reported value.`);
      if (!traceSupport(loaded, findingsById).supported) problems.push(`Row ${row.finding_id} does not trace to usable measured evidence (e.g. it is excluded).`);
    }
  }
  return { chartable: resp && resp.comparable === true && problems.length === 0, problems };
}

/** Quantities that loaded measured findings report on, for the comparison picker. */
export function availableQuantities(findings) {
  const out = new Map();
  for (const f of findings) {
    if (f.evidence_class === "measured" && typeof f.quantity === "string" && f.quantity) {
      if (!out.has(f.quantity)) out.set(f.quantity, f.unit);
    }
  }
  return [...out.entries()].map(([quantity, unit]) => ({ quantity, unit })).sort((a, b) => a.quantity.localeCompare(b.quantity));
}
