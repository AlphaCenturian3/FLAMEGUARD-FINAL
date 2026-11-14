// Experiment comparison logic. Pure functions; no DOM.
//
// A chart is drawn only when FlameGuard-SI can show that the values measure
// the same quantity in the same unit. Contract v0.1.0 Findings have no
// quantity identifier, so the UI reads an optional `quantity` string when a
// record supplies one (proposed contract addition, see frontend/README.md).
// Without it, nothing is charted and the UI says why.

import { isMissing } from "./evidence.js";

export const INCOMPATIBILITY = Object.freeze({
  TOO_FEW_INVESTIGATIONS: "Select at least two investigations to compare.",
  NO_QUANTITY_ID:
    "Contract v0.1.0 findings carry no shared quantity identifier, so FlameGuard-SI cannot confirm that two values measure the same thing. Charts are disabled; compare the findings in the table instead.",
  SINGLE_INVESTIGATION: "Only one selected investigation reports this quantity.",
  NOT_MEASURED: "Includes findings that are not measured; only measured values are charted.",
  MISSING_VALUE: "At least one investigation does not report a value for this quantity.",
  NON_NUMERIC: "At least one value is not numeric.",
  UNIT_MISMATCH: "Units differ. Values are not converted or compared.",
  NEGATIVE: "Contains negative values; shown in the table only.",
});

/**
 * Assess whether a set of findings for one quantity can be charted.
 * @param {import("../api/types.js").Finding[]} findings
 * @returns {{ compatible: boolean, reasons: string[] }}
 */
export function assessCompatibility(findings) {
  const reasons = [];
  const investigations = new Set(findings.map((f) => f.investigation_id));
  if (investigations.size < 2) reasons.push(INCOMPATIBILITY.SINGLE_INVESTIGATION);
  if (findings.some((f) => f.evidence_class !== "measured")) reasons.push(INCOMPATIBILITY.NOT_MEASURED);
  if (findings.some((f) => isMissing(f.value))) reasons.push(INCOMPATIBILITY.MISSING_VALUE);
  else if (findings.some((f) => typeof f.value !== "number" || !Number.isFinite(f.value))) reasons.push(INCOMPATIBILITY.NON_NUMERIC);
  const units = new Set(findings.map((f) => (isMissing(f.unit) ? null : f.unit)));
  if (units.size > 1 || units.has(null)) reasons.push(INCOMPATIBILITY.UNIT_MISMATCH);
  if (findings.some((f) => typeof f.value === "number" && f.value < 0)) reasons.push(INCOMPATIBILITY.NEGATIVE);
  return { compatible: reasons.length === 0, reasons };
}

/**
 * Build the comparison model for the selected investigations.
 * @param {import("../api/types.js").Investigation[]} selected
 * @param {Map<string, import("../api/types.js").Finding[]>} findingsByInvestigation
 */
export function buildComparison(selected, findingsByInvestigation) {
  const columns = selected.map((inv) => {
    const findings = findingsByInvestigation.get(inv.id) || [];
    const counts = { measured: 0, interpretation: 0, illustrative_simulation: 0 };
    for (const f of findings) if (Object.hasOwn(counts, f.evidence_class)) counts[f.evidence_class] += 1;
    return { investigation: inv, findings, counts };
  });

  if (selected.length < 2) {
    return { columns, groups: [], chartsAvailable: false, message: INCOMPATIBILITY.TOO_FEW_INVESTIGATIONS };
  }

  // Group by the optional quantity identifier. Findings without one are not grouped.
  const byQuantity = new Map();
  for (const col of columns) {
    for (const f of col.findings) {
      if (f.evidence_class === "illustrative_simulation") continue; // never compared with evidence
      if (typeof f.quantity !== "string" || f.quantity.trim() === "") continue;
      if (!byQuantity.has(f.quantity)) byQuantity.set(f.quantity, []);
      byQuantity.get(f.quantity).push(f);
    }
  }

  const groups = [...byQuantity.entries()].map(([quantity, findings]) => ({
    quantity,
    findings,
    ...assessCompatibility(findings),
  }));

  if (groups.length === 0) {
    return { columns, groups, chartsAvailable: false, message: INCOMPATIBILITY.NO_QUANTITY_ID };
  }
  const chartsAvailable = groups.some((g) => g.compatible);
  return { columns, groups, chartsAvailable, message: chartsAvailable ? null : "No quantity is reported compatibly by two or more selected investigations." };
}
