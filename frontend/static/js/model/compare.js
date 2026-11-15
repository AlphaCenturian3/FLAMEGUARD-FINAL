// Comparison display rules (P3). The backend decides comparability
// (GET /api/compare; spec §4.2, §4.3). This module never decides whether
// values are comparable and never fills a missing value. It only checks that
// what it is about to show is consistent with the contract and with the loaded
// evidence, and fails closed when it is not: no chart, and no number in the
// table for a row that does not match a usable measured finding.

import { valueStatusInfo } from "./evidence.js";
import { traceSupport } from "./trace.js";

/**
 * Consistency problems for one comparison row (S5 and S9). Empty when the row's
 * number may be displayed.
 * @param {import("../api/types.js").Comparison["rows"][number]} row
 * @param {import("../api/types.js").Comparison} resp
 * @param {Map<string, import("../api/types.js").Finding>} findingsById
 * @returns {string[]}
 */
export function rowIssues(row, resp, findingsById) {
  const issues = [];
  if (row.value_status !== "reported" || typeof row.value !== "number" || !Number.isFinite(row.value)) issues.push(`Row ${row.finding_id} has no reported numeric value.`);
  if (row.evidence_class !== "measured") issues.push(`Row ${row.finding_id} is not measured evidence.`);
  const loaded = findingsById.get(row.finding_id);
  if (!loaded) {
    issues.push(`Row ${row.finding_id}: finding not loaded, so it does not resolve (S5).`);
    return issues;
  }
  if (loaded.evidence_class !== "measured") issues.push(`Row ${row.finding_id} resolves to a ${loaded.evidence_class} finding, not measured (S5).`);
  if (loaded.quantity !== resp.quantity) issues.push(`Row ${row.finding_id}: loaded finding quantity ${loaded.quantity} differs from ${resp.quantity} (S5).`);
  if (loaded.unit !== resp.unit) issues.push(`Row ${row.finding_id}: loaded finding unit ${loaded.unit} differs from ${resp.unit} (S5).`);
  if (loaded.value_status !== "reported" || loaded.value !== row.value) {
    // The row's number is deliberately not echoed here: this text is shown in the table.
    issues.push(`Row ${row.finding_id}: the row's value differs from the loaded finding (${valueStatusInfo(loaded.value_status).label}).`);
  }
  if (!traceSupport(loaded, findingsById).supported) issues.push(`Row ${row.finding_id} does not trace to usable measured evidence (e.g. it is excluded).`);
  return issues;
}

/**
 * What the comparison table may show for one row. A number is shown only for a
 * fully consistent row; otherwise the status of the loaded finding (e.g.
 * "Excluded by FlameGuard-SI"), the row's own non-reported status, or
 * "withheld", with the reason.
 * @returns {{ show: true, value: number } | { show: false, status: string, reason: string }}
 */
export function rowDisplay(row, resp, findingsById) {
  const issues = rowIssues(row, resp, findingsById);
  if (!issues.length) return { show: true, value: row.value };
  const loaded = findingsById.get(row.finding_id);
  let status = "withheld";
  if (loaded && loaded.value_status && loaded.value_status !== "reported") status = loaded.value_status;
  else if (row.value_status && row.value_status !== "reported") status = row.value_status;
  return { show: false, status, reason: issues.join(" ") };
}

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
    for (const row of rows) problems.push(...rowIssues(row, resp, findingsById));
  }
  return { chartable: Boolean(resp && resp.comparable === true && problems.length === 0), problems };
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
