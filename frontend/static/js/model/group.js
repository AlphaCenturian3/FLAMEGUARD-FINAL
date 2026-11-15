// Explorer grouping for large investigations (P2). Pure functions; no DOM.
//
// Findings of one test share a structured `test_id` (contract v0.2.2, S11), so the Explorer groups
// measured findings by `test_id` when they carry one and shows that test's printed outcome and its
// conditions once. Findings without a `test_id` (legacy and fixture data) fall back to the exact
// `provenance.locator`, as before. Grouping is only presentation: it never merges, fills, infers
// or reorders values within a finding, and it never decides comparability.

export const GROUP_THRESHOLD = 6;

function conditionsKey(f) {
  return JSON.stringify(f.conditions || null);
}

/**
 * @param {import("../api/types.js").Finding[]} findings  one investigation's findings
 * @returns {{ grouped: boolean, groups: Array<{ key: string, label: string, testId: string|null, outcome: string|null, outcomeConflict: boolean, findings: any[], sharedConditions: object|null }>, interpretations: any[] }}
 */
export function groupFindingsByRow(findings, threshold = GROUP_THRESHOLD) {
  const measured = findings.filter((f) => f.evidence_class === "measured");
  const interpretations = findings.filter((f) => f.evidence_class !== "measured");
  if (measured.length <= threshold) {
    return { grouped: false, groups: [{ key: "", label: "", testId: null, outcome: null, outcomeConflict: false, findings: measured, sharedConditions: null }], interpretations };
  }
  const order = [];
  const byKey = new Map();
  for (const f of measured) {
    const testId = typeof f.test_id === "string" && f.test_id ? f.test_id : null;
    const key = testId ? `test:${testId}` : `locator:${(f.provenance && f.provenance.locator) || "(no locator)"}`;
    if (!byKey.has(key)) {
      byKey.set(key, { testId, findings: [] });
      order.push(key);
    }
    byKey.get(key).findings.push(f);
  }
  const groups = order.map((key) => {
    const { testId, findings: fs } = byKey.get(key);
    const same = fs.every((f) => conditionsKey(f) === conditionsKey(fs[0]));
    const outcomes = [...new Set(fs.map((f) => f.test_outcome || null))];
    // Different outcomes inside one test are a data error: show it, never pick one.
    const outcomeConflict = outcomes.length > 1;
    const label = testId || (fs[0].provenance && fs[0].provenance.locator) || "(no locator)";
    return { key, label, testId, outcome: outcomeConflict ? null : outcomes[0], outcomeConflict, findings: fs, sharedConditions: same ? fs[0].conditions || null : null };
  });
  return { grouped: true, groups, interpretations };
}
