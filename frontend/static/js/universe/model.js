// The Evidence Universe model: pure functions, no DOM, no WebGL (tested in tests/universe.test.js).
//
// It turns exactly what the data source serves (investigations and Findings) into a graph of
//   investigation -> test clusters (by structured test_id, else locator) -> Findings -> source records
// with three kinds of citation links: the Finding's provenance sources, its caution notes' source
// passages and its exclusion notes' source passages. Nothing is invented, filled, inferred or
// scored: a missing value stays "not reported", an excluded value is never carried (S9), and node
// sizes and colours encode only the record type and value status, never a measured magnitude.

export const STATUS_STYLE = Object.freeze({
  reported: { label: "Reported", color: "#ffb84d" },
  not_reported: { label: "Not reported", color: "#7d8aa3" },
  not_applicable: { label: "Not applicable", color: "#7d8aa3" },
  excluded: { label: "Excluded by FlameGuard-SI", color: "#ff5d6c" },
});

const LINK_KIND = { caution: "caution", exclusion: "exclusion" };

function sourceKey(s) {
  return [s.title || "", s.page ?? "", s.quote ?? ""].join("|");
}

function quantityLabel(q) {
  return q ? q.replace(/_/g, " ") : "qualitative statement";
}

/** The text shown for a Finding's value. An excluded value is never shown, whatever the record holds. */
export function valueText(f) {
  if (f.value_status === "excluded") return "Excluded by FlameGuard-SI — value withheld";
  if (f.value_status === "not_reported") return "Not reported by the source";
  if (f.value_status === "not_applicable") return "Not applicable";
  if (f.value === null || f.value === undefined) return "Not reported by the source";
  return f.unit ? `${f.value} ${f.unit}` : String(f.value);
}

/**
 * @param {{ investigations?: any[], findings?: any[], fixture?: boolean }} input
 */
export function buildUniverse({ investigations = [], findings = [], fixture = false } = {}) {
  const invById = new Map(investigations.map((i) => [i.id, i]));
  const tests = new Map();
  const sources = new Map();
  const links = [];
  const nodes = [];

  const addSource = (s, role, findingId) => {
    const key = sourceKey(s);
    if (!sources.has(key)) {
      sources.set(key, {
        key,
        title: s.title || "Untitled source",
        page: s.page ?? null,
        quote: s.quote ?? null,
        url: s.url || null,
        roles: new Set(),
        citedBy: new Set(),
      });
    }
    const rec = sources.get(key);
    rec.roles.add(role);
    rec.citedBy.add(findingId);
    return key;
  };

  for (const f of findings) {
    const measured = f.evidence_class === "measured";
    const testId = typeof f.test_id === "string" && f.test_id ? f.test_id : null;
    const locator = (f.provenance && f.provenance.locator) || "(no locator)";
    const groupKey = `${f.investigation_id}::${testId ? `test:${testId}` : `locator:${locator}`}`;
    if (measured) {
      if (!tests.has(groupKey)) {
        tests.set(groupKey, {
          key: groupKey,
          investigationId: f.investigation_id,
          testId,
          label: testId || locator,
          outcomes: new Set(),
          findings: [],
        });
      }
      const t = tests.get(groupKey);
      if (f.test_outcome) t.outcomes.add(f.test_outcome);
      t.findings.push(f.id);
    }
    const sourceKeys = [];
    for (const s of (f.provenance && f.provenance.sources) || []) {
      const key = addSource(s, "provenance", f.id);
      sourceKeys.push(key);
      links.push({ from: f.id, to: key, kind: "provenance" });
    }
    const notes = [];
    for (const n of f.curation_notes || []) {
      if (!n || !n.source) continue;
      const kind = LINK_KIND[n.kind] || "caution";
      const key = addSource(n.source, kind, f.id);
      links.push({ from: f.id, to: key, kind });
      notes.push({ kind, flag: n.flag_ref ? n.flag_ref.flag_id : null, note: n.note, sourceKey: key });
    }
    nodes.push({
      id: f.id,
      investigationId: f.investigation_id,
      testKey: measured ? groupKey : null,
      evidenceClass: f.evidence_class,
      quantity: f.quantity || null,
      quantityLabel: quantityLabel(f.quantity),
      status: f.value_status,
      valueText: valueText(f),
      uncertainty: f.uncertainty || null,
      testId,
      outcome: f.test_outcome || null,
      locator,
      label: `${testId || f.investigation_id} · ${quantityLabel(f.quantity)}`,
      statement: f.statement,
      sources: sourceKeys,
      notes,
      fixture: Boolean(f.fixture) || fixture,
    });
  }

  const testList = [...tests.values()].map((t) => {
    const outcomes = [...t.outcomes];
    return { ...t, outcome: outcomes.length === 1 ? outcomes[0] : null, outcomeConflict: outcomes.length > 1, outcomes };
  });
  const sourceList = [...sources.values()].map((s) => ({
    ...s,
    roles: [...s.roles].sort(),
    citedBy: [...s.citedBy].sort(),
    primaryRole: s.roles.has("provenance") ? "provenance" : s.roles.has("exclusion") ? "exclusion" : "caution",
  }));
  const invList = investigations.map((i) => ({
    id: i.id,
    name: i.name || i.id,
    acronym: i.acronym || null,
    platform: i.platform || null,
    fixture: Boolean(i.fixture) || fixture,
    findings: nodes.filter((n) => n.investigationId === i.id).length,
  }));
  // Findings of investigations that are not loaded still appear, under their investigation id.
  for (const id of new Set(nodes.map((n) => n.investigationId))) {
    if (!invById.has(id)) invList.push({ id, name: id, acronym: null, platform: null, fixture, findings: nodes.filter((n) => n.investigationId === id).length, unlisted: true });
  }
  const byStatus = {};
  for (const n of nodes) byStatus[n.status] = (byStatus[n.status] || 0) + 1;
  return {
    empty: nodes.length === 0 && invList.length === 0,
    fixture,
    investigations: invList,
    tests: testList,
    findings: nodes,
    sources: sourceList,
    links,
    stats: {
      investigations: invList.length,
      tests: testList.length,
      findings: nodes.length,
      sources: sourceList.length,
      links: links.length,
      byStatus,
    },
  };
}

/** Deterministic spiral of n points on a sphere (no randomness, so layouts are reproducible). */
function fibonacciSphere(i, n, radius) {
  const golden = Math.PI * (3 - Math.sqrt(5));
  const y = n === 1 ? 0 : 1 - (i / (n - 1)) * 2;
  const r = Math.sqrt(Math.max(0, 1 - y * y));
  const theta = golden * i;
  return [Math.cos(theta) * r * radius, y * radius, Math.sin(theta) * r * radius];
}

/**
 * Positions for every node, in scene units. Investigations sit on a ring, their test clusters on
 * a tilted orbit, Findings in a small ring around their test (one fixed angle per quantity, so the
 * same quantity sits in the same place in every test), and source records on an outer shell, with
 * provenance sources gathered near the top.
 */
export function layoutUniverse(model) {
  const pos = new Map();
  const invs = model.investigations;
  const invRing = invs.length > 1 ? 7 : 0;
  invs.forEach((inv, i) => {
    const a = (2 * Math.PI * i) / Math.max(1, invs.length);
    pos.set(`inv:${inv.id}`, [Math.cos(a) * invRing, 0, Math.sin(a) * invRing]);
  });
  const quantities = [...new Set(model.findings.map((f) => f.quantity || "~"))].sort();
  const tilt = 0.32;
  for (const inv of invs) {
    const center = pos.get(`inv:${inv.id}`);
    const ts = model.tests.filter((t) => t.investigationId === inv.id);
    const radius = ts.length > 1 ? 3.1 + ts.length * 0.06 : 0;
    ts.forEach((t, i) => {
      const a = (2 * Math.PI * i) / Math.max(1, ts.length) - Math.PI / 2;
      const x = Math.cos(a) * radius;
      const z = Math.sin(a) * radius;
      pos.set(`test:${t.key}`, [center[0] + x, center[1] + z * Math.sin(tilt), center[2] + z * Math.cos(tilt)]);
    });
    for (const f of model.findings.filter((n) => n.investigationId === inv.id)) {
      const anchor = f.testKey ? pos.get(`test:${f.testKey}`) : center;
      const qi = quantities.indexOf(f.quantity || "~");
      const a = (2 * Math.PI * qi) / Math.max(1, quantities.length);
      const r = f.testKey ? 0.62 : 1.4;
      pos.set(`finding:${f.id}`, [anchor[0] + Math.cos(a) * r, anchor[1] + Math.sin(a) * r * 0.55 + 0.05, anchor[2] + Math.sin(a) * r * 0.35]);
    }
  }
  const provenance = model.sources.filter((s) => s.primaryRole === "provenance");
  const passages = model.sources.filter((s) => s.primaryRole !== "provenance");
  provenance.forEach((s, i) => {
    const spread = provenance.length > 1 ? (i - (provenance.length - 1) / 2) * 1.6 : 0;
    pos.set(`source:${s.key}`, [spread, 4.6, -1.2]);
  });
  passages.forEach((s, i) => {
    const [x, y, z] = fibonacciSphere(i, Math.max(passages.length, 2), 7.2);
    pos.set(`source:${s.key}`, [x, y * 0.55 - 0.4, z]);
  });
  return pos;
}

/** One-line plain-text description used by screen readers and the accessible list. */
export function describeFinding(f) {
  const outcome = f.outcome ? `, test end as printed: ${f.outcome}` : "";
  return `${f.label}: ${f.valueText}${outcome}. ${f.notes.length} caution or exclusion note${f.notes.length === 1 ? "" : "s"}, ${f.sources.length} provenance source${f.sources.length === 1 ? "" : "s"}.`;
}
