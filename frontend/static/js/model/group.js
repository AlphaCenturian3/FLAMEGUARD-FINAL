// Explorer grouping for large investigations (P2). Pure functions; no DOM.
//
// Findings from the same test row share one `provenance.locator` (S10a relies
// on the locator identifying the row), so the Explorer groups measured
// findings by locator and shows that row's conditions once. Grouping is only
// presentation: it never merges, fills or reorders values within a finding.

export const GROUP_THRESHOLD = 6;

function conditionsKey(f) {
  return JSON.stringify(f.conditions || null);
}

/**
 * @param {import("../api/types.js").Finding[]} findings  one investigation's findings
 * @returns {{ grouped: boolean, groups: Array<{ key: string, label: string, findings: any[], sharedConditions: object|null }>, interpretations: any[] }}
 */
export function groupFindingsByRow(findings, threshold = GROUP_THRESHOLD) {
  const measured = findings.filter((f) => f.evidence_class === "measured");
  const interpretations = findings.filter((f) => f.evidence_class !== "measured");
  if (measured.length <= threshold) {
    return { grouped: false, groups: [{ key: "", label: "", findings: measured, sharedConditions: null }], interpretations };
  }
  const order = [];
  const byKey = new Map();
  for (const f of measured) {
    const locator = (f.provenance && f.provenance.locator) || "(no locator)";
    if (!byKey.has(locator)) {
      byKey.set(locator, []);
      order.push(locator);
    }
    byKey.get(locator).push(f);
  }
  const groups = order.map((key) => {
    const fs = byKey.get(key);
    const same = fs.every((f) => conditionsKey(f) === conditionsKey(fs[0]));
    return { key, label: key, findings: fs, sharedConditions: same ? fs[0].conditions || null : null };
  });
  return { grouped: true, groups, interpretations };
}
