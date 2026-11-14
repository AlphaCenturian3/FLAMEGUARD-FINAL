import { assert, test } from "./harness.js";
import { inv, interpretation, measured, simulation } from "./samples.js";
import { filterInvestigations, facetOptions, groupFindings } from "../static/js/model/filter.js";
import { assessCompatibility, buildComparison, INCOMPATIBILITY } from "../static/js/model/compare.js";
import {
  evidenceInfo,
  formatValue,
  missingFindingFields,
  missingInvestigationFields,
  missingSourceFields,
  provenanceIssues,
  SIMULATION_LABEL,
} from "../static/js/model/evidence.js";
import { reviewRankings } from "../static/js/model/ranking.js";
import { traceSupport } from "../static/js/model/trace.js";

// ---------- Filtering ----------
const INVS = [
  inv("a", { name: "Alpha flame spread", platform: "ISS", relevant_environments: ["spacecraft", "space_station"], objectives: ["Study opposed flow"] }),
  inv("b", { name: "Bravo droplet", platform: "drop tower", relevant_environments: ["lunar_base"] }),
  inv("c", { name: "Charlie smolder", platform: "ISS", relevant_environments: ["martian_base"] }),
];
const FINDINGS = [measured("fa", "a", { value: 1.5, unit: "mm/s" }), interpretation("fi", "a", ["fa"]), measured("fb", "b"), simulation("fs", "c")];
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

test("filter: platform and environment", () => {
  assert.deepEqual(filterInvestigations(INVS, { platform: "ISS" }, BY_INV).map((i) => i.id), ["a", "c"]);
  assert.deepEqual(filterInvestigations(INVS, { environment: "lunar_base" }, BY_INV).map((i) => i.id), ["b"]);
  assert.deepEqual(filterInvestigations(INVS, { platform: "ISS", environment: "martian_base" }, BY_INV).map((i) => i.id), ["c"]);
});

test("filter: evidence class and reported-value filters", () => {
  assert.deepEqual(filterInvestigations(INVS, { evidenceClass: "interpretation" }, BY_INV).map((i) => i.id), ["a"]);
  assert.deepEqual(filterInvestigations(INVS, { evidenceClass: "illustrative_simulation" }, BY_INV).map((i) => i.id), ["c"]);
  assert.deepEqual(filterInvestigations(INVS, { withValuesOnly: true }, BY_INV).map((i) => i.id), ["a"]);
});

test("filter: facets come only from loaded data", () => {
  const f = facetOptions(INVS);
  assert.deepEqual(f.platforms, ["ISS", "drop tower"]);
  assert.deepEqual(f.environments, ["lunar_base", "martian_base", "space_station", "spacecraft"]);
  assert.deepEqual(facetOptions([inv("x")]), { platforms: [], environments: [] });
});

// ---------- Comparison compatibility ----------
test("compare: fewer than two investigations gives explicit message", () => {
  const m = buildComparison([INVS[0]], BY_INV);
  assert.equal(m.chartsAvailable, false);
  assert.equal(m.message, INCOMPATIBILITY.TOO_FEW_INVESTIGATIONS);
});

test("compare: contract v0.1.0 findings without quantity id are never charted", () => {
  const m = buildComparison(INVS, BY_INV);
  assert.equal(m.chartsAvailable, false);
  assert.equal(m.groups.length, 0);
  assert.equal(m.message, INCOMPATIBILITY.NO_QUANTITY_ID);
});

test("compare: compatible measured values with same quantity and unit are charted", () => {
  const f = [measured("x1", "a", { quantity: "spread_rate", value: 1.2, unit: "mm/s" }), measured("x2", "b", { quantity: "spread_rate", value: 0.8, unit: "mm/s" })];
  const m = buildComparison(INVS.slice(0, 2), groupFindings(f));
  assert.equal(m.chartsAvailable, true);
  assert.equal(m.groups[0].compatible, true);
  assert.equal(m.message, null);
});

test("compare: unit mismatch, missing value, non-numeric, non-measured are each reported", () => {
  const unit = assessCompatibility([measured("1", "a", { value: 1, unit: "mm/s" }), measured("2", "b", { value: 1, unit: "cm/s" })]);
  assert.equal(unit.compatible, false);
  assert.includes(unit.reasons, INCOMPATIBILITY.UNIT_MISMATCH);

  const missing = assessCompatibility([measured("1", "a", { value: 1, unit: "s" }), measured("2", "b", { value: null, unit: "s" })]);
  assert.includes(missing.reasons, INCOMPATIBILITY.MISSING_VALUE);

  const text = assessCompatibility([measured("1", "a", { value: 1, unit: "s" }), measured("2", "b", { value: "about 2", unit: "s" })]);
  assert.includes(text.reasons, INCOMPATIBILITY.NON_NUMERIC);

  const interp = assessCompatibility([measured("1", "a", { value: 1, unit: "s" }), interpretation("2", "b", ["1"], { value: 2, unit: "s" })]);
  assert.includes(interp.reasons, INCOMPATIBILITY.NOT_MEASURED);

  const single = assessCompatibility([measured("1", "a", { value: 1, unit: "s" }), measured("2", "a", { value: 2, unit: "s" })]);
  assert.includes(single.reasons, INCOMPATIBILITY.SINGLE_INVESTIGATION);
});

test("compare: simulation findings never enter a comparison group", () => {
  const f = [measured("m", "a", { quantity: "q", value: 1, unit: "s" }), simulation("s", "b", { quantity: "q", value: 2, unit: "s" })];
  const m = buildComparison(INVS.slice(0, 2), groupFindings(f));
  assert.equal(m.groups[0].findings.length, 1);
  assert.equal(m.groups[0].compatible, false);
});

// ---------- Provenance labels ----------
test("provenance: evidence class labels and unknown class", () => {
  assert.equal(evidenceInfo("measured").label, "Measured");
  assert.equal(evidenceInfo("interpretation").label, "Interpretation");
  assert.equal(evidenceInfo("illustrative_simulation").label, "Illustrative simulation");
  assert.equal(evidenceInfo("quoted").valid, false);
  assert.equal(evidenceInfo(undefined).key, "unknown");
});

test("provenance: valid records have no issues", () => {
  assert.deepEqual(provenanceIssues(measured("m", "a")), []);
  assert.deepEqual(provenanceIssues(interpretation("i", "a", ["m"])), []);
  assert.deepEqual(provenanceIssues(simulation("s", "a")), []);
});

test("provenance: measured without manifest or sources is flagged", () => {
  const issues = provenanceIssues(measured("m", "a", { provenance: { sources: [] } }));
  assert.equal(issues.length, 2);
});

test("provenance: interpretation attributed to NASA is flagged", () => {
  const f = interpretation("i", "a", ["m"]);
  f.provenance.generated_by = "NASA";
  assert.includes(provenanceIssues(f).join(" "), "not attributed to FlameGuard-SI");
});

test("provenance: simulation without exact label is flagged", () => {
  assert.equal(SIMULATION_LABEL, "Fluid and thermal transport model. No combustion chemistry.");
  assert.includes(provenanceIssues(simulation("s", "a", { label: "Simulated flame" })).join(" "), "required label");
});

// ---------- Missing data ----------
test("missing: finding value/unit/uncertainty reported as missing, never formatted", () => {
  const f = measured("m", "a");
  assert.deepEqual(missingFindingFields(f), ["value", "unit", "uncertainty"]);
  assert.equal(formatValue(f), null);
  assert.equal(formatValue(measured("m", "a", { value: 0, unit: "K" })), "0 K", "zero is a value, not missing");
  assert.deepEqual(missingFindingFields(measured("m", "a", { value: 0, unit: "K", uncertainty: "±2 K" })), []);
});

test("missing: investigation and source fields", () => {
  assert.deepEqual(missingInvestigationFields(inv("x")), ["acronym", "platform", "objectives", "relevant_environments"]);
  assert.deepEqual(missingSourceFields({ title: "t", url: "u", retrieved: "d" }), ["page", "quote", "archive_id"]);
});

// ---------- Ranking guards ----------
test("ranking: items citing simulation inputs are withheld", () => {
  const byId = new Map(FINDINGS.map((f) => [f.id, f]));
  const res = reviewRankings(
    {
      items: [
        { investigation_id: "a", score: 0.4, rationale: "r", inputs: ["fa", "fi"] },
        { investigation_id: "c", score: 0.9, rationale: "r", inputs: ["fs"] },
        { investigation_id: "b", score: "high", rationale: "r", inputs: ["fb"] },
        { investigation_id: "b", score: 0.7, rationale: "", inputs: ["fb"] },
      ],
    },
    byId,
  );
  assert.deepEqual(res.accepted.map((e) => e.item.investigation_id), ["a"]);
  assert.equal(res.rejected.length, 3);
  assert.includes(res.rejected[0].problems.join(" "), "illustrative_simulation");
});

test("ranking: accepted items are sorted by score; empty response is empty", () => {
  const byId = new Map(FINDINGS.map((f) => [f.id, f]));
  const res = reviewRankings(
    { items: [{ investigation_id: "b", score: 1, rationale: "r", inputs: ["fb"] }, { investigation_id: "a", score: 2, rationale: "r", inputs: ["fa", "fi"] }] },
    byId,
  );
  assert.deepEqual(res.accepted.map((e) => e.item.investigation_id), ["a", "b"]);
  assert.deepEqual(reviewRankings({}, byId), { accepted: [], rejected: [] });
});

// Regression: unresolved supporting IDs used to be accepted with a warning.
test("ranking: item with an unresolved supporting finding ID is withheld", () => {
  const byId = new Map(FINDINGS.map((f) => [f.id, f]));
  const res = reviewRankings({ items: [{ investigation_id: "a", score: 2, rationale: "r", inputs: ["fa", "ghost"] }] }, byId);
  assert.equal(res.accepted.length, 0);
  assert.equal(res.rejected.length, 1);
  assert.includes(res.rejected[0].problems.join(" "), "ghost is not among the loaded findings");
});

// Regression: an interpretation derived from a simulation could carry it into a ranking.
test("ranking: simulation reaching a ranking through an interpretation is withheld", () => {
  const sim = simulation("s1", "a");
  const viaSim = interpretation("i-sim", "a", ["s1"]);
  const mixed = interpretation("i-mixed", "a", ["fa", "s1"]);
  const deep = interpretation("i-deep", "a", ["i-sim"]);
  const byId = new Map([...FINDINGS, sim, viaSim, mixed, deep].map((f) => [f.id, f]));
  const res = reviewRankings(
    {
      items: [
        { investigation_id: "a", score: 3, rationale: "r", inputs: ["i-sim"] },
        { investigation_id: "a", score: 2, rationale: "r", inputs: ["fa", "i-mixed"] },
        { investigation_id: "a", score: 1, rationale: "r", inputs: ["i-deep"] },
      ],
    },
    byId,
  );
  assert.equal(res.accepted.length, 0, "no item may be accepted");
  assert.equal(res.rejected.length, 3);
  for (const r of res.rejected) assert.includes(r.problems.join(" "), "Depends on illustrative simulation s1");
});

test("ranking: interpretation with broken parent, bad provenance, or cycle is withheld", () => {
  const orphan = interpretation("i-orphan", "a", ["missing-parent"]);
  const badMeasured = measured("m-bad", "a", { provenance: { sources: [] } });
  const onBad = interpretation("i-bad", "a", ["m-bad"]);
  const c1 = interpretation("c1", "a", ["c2"]);
  const c2 = interpretation("c2", "a", ["c1"]);
  const byId = new Map([...FINDINGS, orphan, badMeasured, onBad, c1, c2].map((f) => [f.id, f]));
  const res = reviewRankings(
    {
      items: [
        { investigation_id: "a", score: 1, rationale: "r", inputs: ["i-orphan"] },
        { investigation_id: "a", score: 1, rationale: "r", inputs: ["i-bad"] },
        { investigation_id: "a", score: 1, rationale: "r", inputs: ["c1"] },
        { investigation_id: "a", score: 1, rationale: "r", inputs: ["m-bad"] },
      ],
    },
    byId,
  );
  assert.equal(res.accepted.length, 0);
  assert.includes(res.rejected[0].problems.join(" "), "missing-parent");
  assert.includes(res.rejected[1].problems.join(" "), "no manifest_id");
  assert.includes(res.rejected[2].problems.join(" "), "Circular derivation");
  assert.includes(res.rejected[3].problems.join(" "), "cites no source");
});

// ---------- Evidence-chain tracing ----------
test("trace: interpretation chain ending in valid measured records is supported", () => {
  const i2 = interpretation("i2", "a", ["fi", "fb"]);
  const byId = new Map([...FINDINGS, i2].map((f) => [f.id, f]));
  const t = traceSupport(i2, byId);
  assert.equal(t.supported, true, t.reasons.join(" | "));
  assert.deepEqual(t.measuredRoots.map((f) => f.id).sort(), ["fa", "fb"]);
});

test("trace: simulation, unresolved parent, cycle, and no measured root are unsupported", () => {
  const sim = simulation("s1", "a");
  const viaSim = interpretation("i-sim", "a", ["s1"]);
  const orphan = interpretation("i-orphan", "a", ["nope"]);
  const self = interpretation("i-self", "a", ["i-self"]);
  const byId = new Map([...FINDINGS, sim, viaSim, orphan, self].map((f) => [f.id, f]));
  assert.includes(traceSupport(viaSim, byId).reasons.join(" "), "Depends on illustrative simulation s1");
  assert.includes(traceSupport(sim, byId).reasons.join(" "), "is an illustrative simulation, not evidence");
  assert.includes(traceSupport(orphan, byId).reasons.join(" "), "nope (cited by i-orphan) is not among the loaded findings");
  assert.includes(traceSupport(self, byId).reasons.join(" "), "Circular derivation");
  const noParents = interpretation("i-empty", "a", []);
  const t = traceSupport(noParents, byId);
  assert.equal(t.supported, false);
  assert.includes(t.reasons.join(" "), "does not list the findings it is derived from");
});
