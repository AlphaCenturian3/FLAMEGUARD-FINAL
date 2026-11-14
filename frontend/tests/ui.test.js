import { assert, test } from "./harness.js";
import { interpretation, measured, simulation } from "./samples.js";
import { evidenceBadge, findingCard, provenanceBlock, resourcePanel, sourceItem } from "../static/js/ui/components.js";
import { ApiError } from "../static/js/api/errors.js";
import { safeHttpUrl } from "../static/js/ui/dom.js";
import { DEMO_STEPS, DEMO_TARGET_SECONDS, createDemo } from "../static/js/demo.js";
import { interpretationCard } from "../static/js/views/interpret.js";

test("ui: every finding card shows its evidence class label and fixture badge", () => {
  for (const [f, label] of [
    [measured("m", "a"), "Measured"],
    [interpretation("i", "a", ["m"]), "Interpretation"],
    [simulation("s", "a"), "Illustrative simulation"],
  ]) {
    const el = findingCard(f);
    assert.includes(el.textContent, label);
    assert.includes(el.textContent, "Fixture · not NASA data");
  }
});

test("ui: simulation card always shows the required label", () => {
  assert.includes(findingCard(simulation("s", "a")).textContent, "Fluid and thermal transport model. No combustion chemistry.");
  assert.ok(!findingCard(measured("m", "a")).textContent.includes("No combustion chemistry"));
});

test("ui: missing values are shown as 'Not reported', not blank or zero", () => {
  const el = findingCard(measured("m", "a"));
  assert.includes(el.textContent, "Not reported");
  assert.includes(el.textContent, "Missing from record");
  const withValue = findingCard(measured("m", "a", { value: 3.2, unit: "mm/s", uncertainty: "±0.1 mm/s" }));
  assert.includes(withValue.textContent, "3.2 mm/s");
  assert.includes(withValue.textContent, "±0.1 mm/s (as reported)");
});

test("ui: qualitative interpretation is labelled as such, not as missing data", () => {
  const el = findingCard(interpretation("i", "a", ["m"]));
  assert.includes(el.textContent, "Qualitative statement; no numerical value.");
  assert.ok(!el.textContent.includes("Missing from record"));
  const valued = findingCard(interpretation("i", "a", ["m"], { value: 2, unit: "x" }));
  assert.includes(valued.textContent, "Missing from record");
});

test("ui: interpretation provenance links derived-from ids and attribution", () => {
  const m = measured("m1", "a");
  const el = provenanceBlock(interpretation("i", "a", ["m1", "ghost"]), new Map([["m1", m]]));
  assert.includes(el.textContent, "m1");
  assert.includes(el.textContent, "ghost (not loaded)");
  assert.includes(el.textContent, "FlameGuard-SI");
});

test("ui: bad provenance raises a visible warning", () => {
  const el = provenanceBlock(measured("m", "a", { provenance: {} }));
  assert.includes(el.textContent, "Provenance problems");
});

test("ui: unsafe source URLs are not turned into links; data is not parsed as HTML", () => {
  assert.equal(safeHttpUrl("javascript:alert(1)"), null);
  assert.equal(safeHttpUrl("https://ntrs.nasa.gov/x"), "https://ntrs.nasa.gov/x");
  const el = sourceItem({ title: "<img src=x onerror=alert(1)>", url: "javascript:alert(1)", retrieved: "2026-11-14" });
  assert.equal(el.querySelector("a"), null);
  assert.equal(el.querySelector("img"), null);
  assert.includes(el.textContent, "<img src=x");
});

test("ui: 501 resource panel says not implemented and shows nothing invented", () => {
  const el = resourcePanel({ state: "not_implemented", error: new ApiError(501, "not_implemented", "planned") }, "Rankings", "GET /api/rankings");
  assert.includes(el.textContent, "not implemented by the backend yet");
  assert.includes(el.textContent, "HTTP 501");
  const err = resourcePanel({ state: "error", error: new ApiError(0, "network_error", "down") }, "Rankings", "GET /api/rankings");
  assert.equal(err.getAttribute("role"), "alert");
});

test("interpret: fully traced interpretation is shown with its statement and evidence", () => {
  const m = measured("m1", "a");
  const i = interpretation("i1", "a", ["m1"]);
  const el = interpretationCard(i, new Map([m, i].map((f) => [f.id, f])), undefined);
  assert.equal(el.dataset.support, "supported");
  assert.includes(el.textContent, "TEST interpretation i1");
  assert.includes(el.textContent, "Traced to 1 measured record");
  assert.ok(!el.textContent.includes("Withheld"));
});

test("interpret: unsupported interpretations are withheld with a reason and hidden statement", () => {
  const m = measured("m1", "a");
  const badM = measured("m-bad", "a", { provenance: { manifest_id: "x", sources: [] } });
  const sim = simulation("s1", "a");
  const cases = [
    [interpretation("i-missing", "a", ["ghost"]), "ghost"],
    [interpretation("i-sim", "a", ["m1", "s1"]), "Depends on illustrative simulation s1"],
    [interpretation("i-badm", "a", ["m-bad"]), "cites no source"],
    [interpretation("i-nasa", "a", ["m1"], { provenance: { derived_from: ["m1"], method: "x", generated_by: "NASA" } }), "not attributed to FlameGuard-SI"],
    [interpretation("i-nomethod", "a", ["m1"], { provenance: { derived_from: ["m1"], generated_by: "FlameGuard-SI" } }), "does not state its method"],
  ];
  for (const [i, reason] of cases) {
    const byId = new Map([m, badM, sim, i].map((f) => [f.id, f]));
    const el = interpretationCard(i, byId, undefined);
    assert.equal(el.dataset.support, "withheld", `${i.id} should be withheld`);
    assert.includes(el.textContent, "Withheld");
    assert.includes(el.textContent, reason);
    assert.ok(!el.textContent.includes(`TEST interpretation ${i.id}`), `${i.id} statement must not be presented`);
  }
});

test("ui: unknown evidence class badge is flagged", () => {
  assert.includes(evidenceBadge("quoted").textContent, "Unknown evidence class");
});

test("demo: five steps in order, fit 90 s, restart returns to step 1", async () => {
  assert.deepEqual(DEMO_STEPS.map((s) => s.title), ["Discover", "Compare", "Rank", "Interpret", "Safety Insight"]);
  assert.equal(DEMO_STEPS.reduce((n, s) => n + s.seconds, 0), DEMO_TARGET_SECONDS);
  const visited = [];
  const demo = createDemo({ go: (r, a) => visited.push(a ? `${r}#${a}` : r), selectAll: async () => {} });
  demo.start();
  await Promise.resolve();
  demo.next();
  await Promise.resolve();
  assert.equal(demo.currentStep().key, "compare");
  demo.restart();
  await Promise.resolve();
  assert.equal(demo.currentStep().key, "discover");
  demo.stop();
  assert.equal(demo.active(), false);
  assert.equal(visited[0], "#/explorer");
});
