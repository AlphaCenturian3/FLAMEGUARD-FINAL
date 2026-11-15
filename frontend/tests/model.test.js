import { assert, test } from "./harness.js";
import { byId, excluded, interpretation, inv, measured, note, notReported, simulation } from "./samples.js";
import { facetOptions, filterInvestigations, groupFindings } from "../static/js/model/filter.js";
import * as compareModel from "../static/js/model/compare.js";
import { availableQuantities, reviewComparison } from "../static/js/model/compare.js";
import { GROUP_THRESHOLD, groupFindingsByRow } from "../static/js/model/group.js";
import {
  evidenceInfo,
  formatValue,
  missingFindingFields,
  missingInvestigationFields,
  missingSourceFields,
  provenanceIssues,
  unreportedConditions,
  VALUE_STATUS,
  valueStatusInfo,
} from "../static/js/model/evidence.js";
import { reviewRankings } from "../static/js/model/ranking.js";
import { exclusionContext, traceSupport } from "../static/js/model/trace.js";

// ---------- Filtering ----------
const INVS = [
  inv("a", { name: "Alpha flame spread", platform: "ISS", relevant_environments: ["spacecraft", "space_station"], objectives: ["Study opposed flow"] }),
  inv("b", { name: "Bravo droplet", platform: "drop tower", relevant_environments: ["lunar_base"] }),
  inv("c", { name: "Charlie smolder", platform: "ISS", relevant_environments: ["martian_base"] }),
];
const FINDINGS = [measured("fa", "a", { value: 1.5 }), interpretation("fi", "a", ["fa"]), notReported("fb", "b"), excluded("fx", "c")];
const BY_INV = groupFindings(FINDINGS);

test("filter: empty filters return everything", () => {
  assert.equal(filterInvestigations(INVS, {}, BY_INV).length, 3);
});

test("filter: free-text search matches name, objectives, and finding statements (all terms)", () => {
  assert.deepEqual(filterInvestigations(INVS, { query: "opposed" }, BY_INV).map((i) => i.id), ["a"]);
  assert.deepEqual(filterInvestigations(INVS, { query: "DROPLET" }, BY_INV).map((i) => i.id), ["b"]);
  assert.deepEqual(filterInvestigations(INVS, { query: "test measured fb" }, BY_INV).map((i) => i.id), ["b"]);
  assert.deepEqual(filterInvestigations(INVS, { query: "alpha droplet" }, BY_INV), []);
});

test("filter: platform, environment, evidence class", () => {
  assert.deepEqual(filterInvestigations(INVS, { platform: "ISS" }, BY_INV).map((i) => i.id), ["a", "c"]);
  assert.deepEqual(filterInvestigations(INVS, { environment: "lunar_base" }, BY_INV).map((i) => i.id), ["b"]);
  assert.deepEqual(filterInvestigations(INVS, { evidenceClass: "interpretation" }, BY_INV).map((i) => i.id), ["a"]);
});

test("filter: 'reports a value' counts only reported values, never excluded or missing ones", () => {
  assert.deepEqual(filterInvestigations(INVS, { withValuesOnly: true }, BY_INV).map((i) => i.id), ["a"]);
  assert.deepEqual(filterInvestigations(INVS, { valueStatus: "excluded" }, BY_INV).map((i) => i.id), ["c"]);
  assert.deepEqual(filterInvestigations(INVS, { valueStatus: "not_reported" }, BY_INV).map((i) => i.id), ["b"]);
});

test("filter: facets come only from loaded data", () => {
  const f = facetOptions(INVS);
  assert.deepEqual(f.platforms, ["ISS", "drop tower"]);
  assert.deepEqual(facetOptions([inv("x")]), { platforms: [], environments: [] });
});

// ---------- P2: grouping by test row ----------
function flexLike(rows = 10, perRow = 4) {
  const fs = [];
  for (let r = 1; r <= rows; r++) {
    const conditions = { ...measured("x", "f").conditions, oxygen_mole_fraction: 0.21, pressure_kpa: 100 + r, fuel_or_material: r < 7 ? "methanol" : "heptane" };
    for (let q = 0; q < perRow; q++) {
      const locator = `TEST Table IX, row ${r}`;
      const base = q === 3 && r === 10 ? excluded(`f-${r}-${q}`, "f") : q === 2 && r === 9 ? notReported(`f-${r}-${q}`, "f") : measured(`f-${r}-${q}`, "f", { value: r + q / 10 });
      base.conditions = structuredClone(conditions);
      base.provenance.locator = locator;
      fs.push(base);
    }
  }
  return fs;
}

test("group: small investigations stay flat; large ones group by locator row", () => {
  const small = [measured("m1", "a"), measured("m2", "a")];
  assert.equal(groupFindingsByRow(small).grouped, false);
  const fs = flexLike();
  const g = groupFindingsByRow([...fs, interpretation("i1", "f", ["f-1-0"])]);
  assert.ok(fs.length > GROUP_THRESHOLD);
  assert.equal(g.grouped, true);
  assert.equal(g.groups.length, 10);
  assert.ok(g.groups.every((x) => x.findings.length === 4));
  assert.equal(g.interpretations.length, 1, "interpretations are listed separately, never merged into a row");
  assert.equal(g.groups[0].sharedConditions.pressure_kpa, 101);
});

test("group: conditions are shown once only when every finding in the row shares them", () => {
  const fs = flexLike(2, 4); // 8 findings, above the threshold
  fs[1].conditions.pressure_kpa = 999; // row 1 now disagrees within itself
  const g = groupFindingsByRow(fs);
  assert.equal(g.groups[0].sharedConditions, null, "row with differing conditions shows them per finding");
  assert.ok(g.groups[1].sharedConditions, "uniform row shows them once");
});

test("group: grouping never alters values or statuses", () => {
  const fs = flexLike();
  const before = JSON.stringify(fs.map((f) => [f.id, f.value, f.value_status]));
  const g = groupFindingsByRow(fs);
  const after = JSON.stringify(g.groups.flatMap((x) => x.findings).map((f) => [f.id, f.value, f.value_status]));
  assert.equal(after, before);
});

// ---------- P3: backend comparison, display review only ----------
const CMP = (extra = {}) => ({
  contract_version: "0.2.0",
  quantity: "flame_spread_rate",
  unit: "mm/s",
  rows: [
    { investigation_id: "a", finding_id: "fa", evidence_class: "measured", value: 1.5, value_status: "reported", conditions: measured("x", "a").conditions },
    { investigation_id: "b", finding_id: "fb2", evidence_class: "measured", value: 0.8, value_status: "reported", conditions: measured("x", "a").conditions },
  ],
  comparable: true,
  non_comparable_reasons: [],
  ...extra,
});

test("compare: the frontend has no comparability decision code", () => {
  assert.equal(compareModel.assessCompatibility, undefined);
  assert.equal(compareModel.buildComparison, undefined);
});

test("compare: a consistent comparable response is chartable", () => {
  const r = reviewComparison(CMP(), byId([measured("fa", "a", { value: 1.5 }), measured("fb2", "b", { value: 0.8 })]));
  assert.equal(r.chartable, true);
  assert.deepEqual(r.problems, []);
});

test("compare: not comparable is shown with the backend's reasons, never charted", () => {
  const r = reviewComparison(CMP({ comparable: false, non_comparable_reasons: ["pressure_kpa not reported for either row"] }));
  assert.equal(r.chartable, false);
  assert.deepEqual(r.problems, []);
  const noReason = reviewComparison(CMP({ comparable: false, non_comparable_reasons: [] }));
  assert.includes(noReason.problems.join(" "), "no reason");
});

test("compare: 'comparable' with a missing or excluded value fails closed (no chart, no filling)", () => {
  const missing = CMP();
  missing.rows[1] = { ...missing.rows[1], value: null, value_status: "not_reported" };
  const r1 = reviewComparison(missing);
  assert.equal(r1.chartable, false);
  assert.includes(r1.problems.join(" "), "no reported numeric value");
  const r2 = reviewComparison(CMP(), byId([excluded("fa", "a"), measured("fb2", "b", { value: 0.8 })]));
  assert.equal(r2.chartable, false);
  assert.includes(r2.problems.join(" "), "excluded");
});

test("compare: quantity picker lists only quantities of loaded measured findings", () => {
  assert.deepEqual(availableQuantities(FINDINGS), [{ quantity: "flame_spread_rate", unit: "mm/s" }]);
  assert.deepEqual(availableQuantities([interpretation("i", "a", ["x"])]), []);
});

// ---------- Evidence classes, value status, provenance ----------
test("evidence: classes and the four value statuses have exact wording", () => {
  assert.equal(evidenceInfo("measured").label, "Measured");
  assert.equal(evidenceInfo("interpretation").label, "Interpretation");
  assert.equal(evidenceInfo("quoted").valid, false);
  assert.deepEqual(Object.keys(VALUE_STATUS), ["reported", "not_reported", "not_applicable", "excluded"]);
  assert.equal(valueStatusInfo("not_reported").label, "Not reported");
  assert.equal(valueStatusInfo("not_applicable").label, "Not applicable");
  assert.equal(valueStatusInfo("excluded").label, "Excluded by FlameGuard-SI");
  assert.equal(valueStatusInfo("withheld").valid, false, "withheld is not a v0.2.0 value status");
});

test("evidence: only a reported value is ever formatted; an excluded value never is", () => {
  assert.equal(formatValue(measured("m", "a", { value: 0 })), "0 mm/s", "zero is a value, not missing");
  assert.equal(formatValue(notReported("m", "a")), null);
  assert.equal(formatValue(excluded("e", "a")), null);
  assert.equal(formatValue(excluded("e", "a", { value: 0.37 })), null, "malformed excluded record with a number still shows none");
});

test("provenance: valid v0.2.0 records have no issues", () => {
  assert.deepEqual(provenanceIssues(measured("m", "a")), []);
  assert.deepEqual(provenanceIssues(measured("m", "a", { curation_notes: [note("caution")] })), []);
  assert.deepEqual(provenanceIssues(excluded("e", "a")), []);
  assert.deepEqual(provenanceIssues(interpretation("i", "a", ["m"])), []);
});

test("provenance: v0.2.0 rule violations are each flagged", () => {
  const cases = [
    [measured("m", "a", { provenance: { manifest_id: "d", sources: [{ title: "t", url: "https://example.invalid", retrieved: "2026-11-14" }] } }), "no locator"],
    [interpretation("i", "a", ["m"], { provenance: { derived_from: ["m"], method: "x", generated_by: "FlameGuard-SI" } }), "method version"],
    [interpretation("i", "a", ["m"], { limitations: [] }), "no limitations"],
    [measured("m", "a", { curation_notes: [note("caution", { generated_by: "NASA" })] }), "not attributed to FlameGuard-SI"],
    [measured("m", "a", { curation_notes: [note("caution", { source: { title: "t", url: "https://example.invalid", retrieved: "2026-11-14", quote: null } })] }), "no source quote"],
    [measured("m", "a", { curation_notes: [note("caution", { flag_ref: null })] }), "quality-flag reference"],
    [excluded("e", "a", { curation_notes: [note("caution")] }), "no exclusion note"],
    [measured("m", "a", { curation_notes: [note("exclusion")] }), "not excluded"],
    [interpretation("i", "a", ["m"], { curation_notes: [note("caution")] }), "not allowed on interpretations"],
    [notReported("m", "a", { value: 3 }), "carries a value"],
    [simulation("s", "a"), "not a Finding"],
  ];
  for (const [f, fragment] of cases) assert.includes(provenanceIssues(f).join(" "), fragment, `expected "${fragment}" for ${f.id}`);
});

test("missing: value, uncertainty and unreported conditions are listed, never filled", () => {
  assert.deepEqual(missingFindingFields(notReported("m", "a")), ["value", "uncertainty"]);
  assert.deepEqual(missingFindingFields(measured("m", "a", { uncertainty: "±0.1 mm/s" })), []);
  assert.deepEqual(missingFindingFields(excluded("e", "a", { uncertainty: "x" })), [], "excluded is not 'missing'");
  assert.equal(unreportedConditions(measured("m", "a")).length, 7);
  assert.deepEqual(missingInvestigationFields(inv("x")), ["acronym", "platform", "objectives", "relevant_environments"]);
  assert.deepEqual(missingSourceFields({ title: "t", url: "u", retrieved: "d" }), ["page", "quote", "archive_id"]);
});

// ---------- S9: transitive exclusion ----------
test("trace: a clean chain to measured evidence is supported", () => {
  const t = traceSupport(interpretation("i2", "a", ["i1", "m2"]), byId([measured("m1", "a"), measured("m2", "a"), interpretation("i1", "a", ["m1"])]));
  assert.equal(t.supported, true, t.reasons.join(" | "));
  assert.deepEqual(t.measuredRoots.map((f) => f.id).sort(), ["m1", "m2"]);
});

test("trace: an excluded value blocks support directly, at depth 2, and through one of mixed parents", () => {
  const fs = [excluded("e", "a"), measured("m", "a"), interpretation("i1", "a", ["e"]), interpretation("i2", "a", ["i1"]), interpretation("i3", "a", ["m", "e"])];
  const map = byId(fs);
  for (const id of ["e", "i1", "i2", "i3"]) {
    const t = traceSupport(map.get(id), map);
    assert.equal(t.supported, false, `${id} must not be supported`);
    assert.equal(t.problems.length, 0, `${id}: exclusion is not a provenance problem`);
    assert.ok(t.exclusionReasons.length > 0, `${id} carries an S9 reason`);
    assert.deepEqual(t.excludedAncestors.map((f) => f.id), ["e"]);
  }
  assert.equal(exclusionContext(map.get("i2"), map)[0].notes[0].note, "TEST exclusion reason for e");
});

test("trace: unresolved parents, cycles and simulations are problems, not exclusions", () => {
  const fs = [simulation("s", "a"), interpretation("i-sim", "a", ["s"]), interpretation("i-orphan", "a", ["nope"]), interpretation("i-self", "a", ["i-self"])];
  const map = byId(fs);
  assert.includes(traceSupport(map.get("i-sim"), map).problems.join(" "), "imulation");
  assert.includes(traceSupport(map.get("i-orphan"), map).problems.join(" "), "nope (cited by i-orphan)");
  assert.includes(traceSupport(map.get("i-self"), map).problems.join(" "), "Circular derivation");
});

// ---------- P4: ranking display guard ----------
function ranking(items, extra = {}) {
  return {
    contract_version: "0.2.0",
    context: "spacecraft",
    criteria_version: "test",
    criteria: [{ id: "c-a", description: "A", weight: 0.5 }, { id: "c-b", description: "B", weight: 0.5 }],
    items,
    excluded: [{ investigation_id: "z", reason: "TEST: no reported value" }],
    generated_by: "FlameGuard-SI",
    ...extra,
  };
}
const item = (rank, inv, score, inputs, cid = "c-a") => ({ rank, investigation_id: inv, score, rationale: "r", criterion_scores: [{ criterion_id: cid, score, inputs }] });
const RANK_FINDINGS = [measured("fa", "a"), interpretation("fi", "a", ["fa"]), measured("fb", "b"), excluded("fx", "c"), interpretation("ix", "c", ["fx"]), interpretation("ix2", "c", ["ix"])];

test("ranking: accepted items follow the backend rank field, not the score", () => {
  const res = reviewRankings(
    ranking([item(2, "b", 0.9, [{ finding_id: "fb", evidence_class: "measured" }]), item(1, "a", 0.1, [{ finding_id: "fa", evidence_class: "measured" }, { finding_id: "fi", evidence_class: "interpretation" }])]),
    byId(RANK_FINDINGS),
  );
  assert.deepEqual(res.accepted.map((e) => e.item.investigation_id), ["a", "b"]);
  assert.equal(res.criteria.length, 2);
  assert.deepEqual(res.notRanked, [{ investigation_id: "z", reason: "TEST: no reported value" }]);
});

test("ranking: scores are never recomputed or checked against weights", () => {
  // Score 0.99 does not equal 0.5 x 0.1; S6 is Member 5's check, not the dashboard's.
  const res = reviewRankings(ranking([item(1, "a", 0.99, [{ finding_id: "fa", evidence_class: "measured" }])]), byId(RANK_FINDINGS));
  assert.equal(res.accepted.length, 1);
});

test("ranking: unresolved, mis-declared, unknown-criterion, excluded and exclusion-dependent inputs are withheld", () => {
  const cases = [
    [item(1, "a", 0.5, [{ finding_id: "ghost", evidence_class: "measured" }]), "not among the loaded findings"],
    [item(1, "a", 0.5, [{ finding_id: "fi", evidence_class: "measured" }]), "declared measured"],
    [item(1, "a", 0.5, [{ finding_id: "fa", evidence_class: "measured" }], "c-zzz"), "not among the listed criteria"],
    [item(1, "c", 0.5, [{ finding_id: "fx", evidence_class: "measured" }]), "excluded"],
    [item(1, "c", 0.5, [{ finding_id: "ix2", evidence_class: "interpretation" }]), "Depends on excluded finding fx"],
  ];
  for (const [it, fragment] of cases) {
    const res = reviewRankings(ranking([it]), byId(RANK_FINDINGS));
    assert.equal(res.accepted.length, 0, `should withhold: ${fragment}`);
    assert.includes(res.rejected[0].problems.join(" "), fragment);
  }
  assert.deepEqual(reviewRankings({}, byId(RANK_FINDINGS)).accepted, []);
});

// ---------- Pre-merge review follow-up (S5): a comparable response must resolve to loaded measured findings ----------
test("compare S5: 'comparable' with a row whose finding_id is not loaded is not charted", () => {
  const r = reviewComparison(CMP(), byId([measured("fa", "a")])); // fb2 is absent
  assert.equal(r.chartable, false);
  assert.includes(r.problems.join(" "), "fb2");
  assert.equal(reviewComparison(CMP(), new Map()).chartable, false, "nothing loaded: fail closed");
});

test("compare S5: a row must match its loaded finding's class, quantity, unit and reported value", () => {
  const ok = byId([measured("fa", "a", { value: 1.5 }), measured("fb2", "b", { value: 0.8 })]);
  assert.equal(reviewComparison(CMP(), ok).chartable, true);
  const cases = [
    [byId([measured("fa", "a", { value: 1.5 }), measured("fb2", "b", { value: 0.8, quantity: "flame_length", unit: "mm" })]), "quantity"],
    [byId([measured("fa", "a", { value: 1.5 }), measured("fb2", "b", { value: 0.8, unit: "cm/s" })]), "unit"],
    [byId([measured("fa", "a", { value: 1.5 }), measured("fb2", "b", { value: 9.9 })]), "value"],
    [byId([measured("fa", "a", { value: 1.5 }), interpretation("fb2", "b", ["fa"])]), "measured"],
  ];
  for (const [map, fragment] of cases) {
    const r = reviewComparison(CMP(), map);
    assert.equal(r.chartable, false, fragment);
    assert.includes(r.problems.join(" "), fragment);
  }
});
