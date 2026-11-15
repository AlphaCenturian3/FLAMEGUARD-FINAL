// Dashboard against the staged FLEX derivation (40 Findings, contract v0.2.2). STAGED, NOT REGISTERED:
// the data is a test fixture (tests/fixtures/frontend/STAGED_FLEX_README.md), never production evidence.
import { assert, test } from "./harness.js";
import { measured as sampleMeasured, stubFetch } from "./samples.js";
import { CONTRACT_VERSION, SUPPORTED_CONTRACT_VERSIONS, versionMismatch } from "../static/js/config.js";
import { groupFindingsByRow } from "../static/js/model/group.js";
import { findingCard, testIdentity } from "../static/js/ui/components.js";
import { findingsSection } from "../static/js/views/explorer.js";
import { createHttpSource } from "../static/js/api/http.js";
import { createStore, listWarnings } from "../static/js/store.js";

const FIX = new URL("../../tests/fixtures/frontend/", import.meta.url);
const load = async (name) => (await fetch(new URL(name, FIX))).json();
const FINDINGS = await load("flex-staged-candidate.json");
const INVESTIGATIONS = await load("flex-staged-investigation.json");
const BY_ID = new Map(FINDINGS.map((f) => [f.id, f]));
const PRINTED_EXCLUDED = /(?<![\d.])0?\.37(?!\d)/; // the excluded burning-rate value, as printed in the source
const OUTCOME_LABELS = new Set(["Extinction", "Disruption", "Completion"]);
const render = (findings = FINDINGS) => findingsSection(findings, new Map(findings.map((f) => [f.id, f])));
const tally = (key) => FINDINGS.reduce((acc, f) => ((acc[f[key]] = (acc[f[key]] || 0) + 1), acc), {});

// ---------- the data this suite is about ----------
test("flex fixture: 40 findings (31 reported, 8 not_reported, 1 excluded), unique ids, one investigation", () => {
  assert.equal(FINDINGS.length, 40);
  assert.equal(new Set(FINDINGS.map((f) => f.id)).size, 40);
  assert.deepEqual(tally("value_status"), { reported: 31, not_reported: 8, excluded: 1 });
  assert.ok(FINDINGS.every((f) => f.evidence_class === "measured" && f.test_id && OUTCOME_LABELS.has(f.test_outcome)));
  assert.equal(INVESTIGATIONS.length, 1);
  assert.equal(INVESTIGATIONS[0].id, "flex");
});

// ---------- contract version tolerance ----------
test("version: exactly the explicitly tested versions are accepted without a warning", () => {
  assert.deepEqual([...SUPPORTED_CONTRACT_VERSIONS], ["0.2.0", "0.2.1", "0.2.2"]);
  assert.ok(SUPPORTED_CONTRACT_VERSIONS.includes(CONTRACT_VERSION));
  for (const v of SUPPORTED_CONTRACT_VERSIONS) assert.equal(versionMismatch(v), null, v);
  for (const v of ["0.1.0", "0.2.3", "0.3.0", "1.0.0", "0.2", "0.2.2-rc1", "0.2.20", ""]) assert.includes(versionMismatch(v), `reports contract ${v}`, v);
  assert.equal(versionMismatch(undefined), null, "an absent version is not a mismatch (the shape checks report missing fields)");
});

test("version: lists of the 40 findings under each supported version raise no warning, and an unsupported one does", () => {
  for (const v of SUPPORTED_CONTRACT_VERSIONS) assert.deepEqual(listWarnings({ contract_version: v, items: FINDINGS, total: 40 }, "Finding list"), [], v);
  assert.includes(listWarnings({ contract_version: "0.2.3", items: FINDINGS, total: 40 }, "Finding list").join(" "), "supports 0.2.0, 0.2.1, 0.2.2");
  assert.includes(listWarnings({ contract_version: "0.2.2", items: FINDINGS, total: 39 }, "Finding list").join(" "), "S7", "S7 is still checked");
});

test("version: a store loading the 40 findings from a v0.2.2 API shows no warning and loses nothing", async () => {
  const body = { contract_version: "0.2.2" };
  const routes = { "/api/investigations": { ...body, items: INVESTIGATIONS, total: 1 }, "/api/findings": { ...body, items: FINDINGS, total: 40 } };
  const fetchImpl = async (url) => new Response(JSON.stringify(routes[new URL(url, "http://x.test").pathname]), { status: 200, headers: { "Content-Type": "application/json" } });
  const ev = await createStore(createHttpSource({ fetchImpl })).evidence();
  assert.deepEqual(ev.warnings, []);
  assert.equal(ev.findings.data.length, 40);
  assert.equal(ev.findingsByInvestigation.get("flex").length, 40);
});

// ---------- grouping by test_id ----------
test("grouping: 40 findings become 10 test rows keyed by test_id, 4 findings each, in source order", () => {
  const { grouped, groups, interpretations } = groupFindingsByRow(FINDINGS);
  assert.ok(grouped);
  assert.equal(interpretations.length, 0);
  assert.deepEqual(groups.map((g) => g.label), ["FLEX-001", "FLEX-002", "FLEX-003", "FLEX-004", "FLEX-005", "FLEX-006", "FLEX-007", "FLEX-008", "FLEX-009", "FLEX-010"]);
  for (const g of groups) {
    assert.equal(g.findings.length, 4, g.label);
    assert.equal(g.testId, g.label);
    assert.ok(g.findings.every((f) => f.test_id === g.testId), "every finding sits in its own test");
    assert.ok(g.sharedConditions, `${g.label}: conditions are shared by the row and shown once`);
    assert.equal(g.outcomeConflict, false);
  }
  assert.equal(groups.reduce((n, g) => n + g.findings.length, 0), 40, "nothing dropped or duplicated");
});

test("grouping: each test shows the outcome label exactly as printed; FLEX-001 stays Disruption", () => {
  const outcome = Object.fromEntries(groupFindingsByRow(FINDINGS).groups.map((g) => [g.testId, g.outcome]));
  assert.deepEqual(outcome, {
    "FLEX-001": "Disruption",
    "FLEX-002": "Extinction",
    "FLEX-003": "Extinction",
    "FLEX-004": "Extinction",
    "FLEX-005": "Extinction",
    "FLEX-006": "Extinction",
    "FLEX-007": "Disruption",
    "FLEX-008": "Disruption",
    "FLEX-009": "Disruption",
    "FLEX-010": "Extinction",
  });
  const f = BY_ID.get("flex.flex-001.visible_flame_extinction_diameter");
  assert.equal(f.value, 0.89);
  assert.equal(f.test_outcome, "Disruption", "a reported extinction diameter does not change the printed outcome");
});

test("grouping: findings without a test_id fall back to the exact locator, as before", () => {
  const legacy = FINDINGS.map((f) => {
    const { test_id, test_outcome, ...rest } = f;
    return rest;
  });
  const { groups } = groupFindingsByRow(legacy);
  assert.equal(groups.length, 40, "per-field locators give one group each, which is why test_id is preferred");
  assert.ok(groups.every((g) => g.testId === null && g.outcome === null && g.label === g.findings[0].provenance.locator));
  const small = [sampleMeasured("a", "inv"), sampleMeasured("b", "inv")];
  assert.equal(groupFindingsByRow(small).grouped, false, "small investigations stay flat");
});

test("grouping: a mix of identified and unidentified findings keeps both, never merges them", () => {
  const mixed = FINDINGS.map((f, i) => (i % 4 === 3 ? (({ test_id, test_outcome, ...rest }) => rest)(f) : f));
  const { groups } = groupFindingsByRow(mixed);
  assert.equal(groups.reduce((n, g) => n + g.findings.length, 0), 40);
  assert.equal(groups.filter((g) => g.testId).length, 10);
  assert.equal(groups.filter((g) => !g.testId).length, 10, "one locator-keyed group per unidentified finding");
});

test("grouping: two outcomes inside one test are a visible conflict, never silently resolved", () => {
  const broken = structuredClone(FINDINGS);
  broken.find((f) => f.id === "flex.flex-004.burn_time").test_outcome = "Disruption";
  const g = groupFindingsByRow(broken).groups.find((x) => x.testId === "FLEX-004");
  assert.ok(g.outcomeConflict);
  assert.equal(g.outcome, null);
  const dom = render(broken);
  assert.includes(dom.textContent, "Findings of this test report different outcomes");
  assert.includes(dom.textContent, "Test end as printed: CONFLICT");
});

// ---------- display: test identity and outcome ----------
test("display: the Explorer shows 10 test rows with identifier, printed outcome and counts", () => {
  const dom = render();
  const rows = dom.querySelectorAll("details.row-group");
  assert.equal(rows.length, 10);
  const summaries = [...rows].map((r) => r.querySelector("summary").textContent);
  assert.includes(summaries[0], "FLEX-001");
  assert.includes(summaries[0], "Test end as printed: Disruption");
  assert.includes(summaries[9], "FLEX-010");
  assert.includes(summaries[9], "Test end as printed: Extinction");
  assert.includes(summaries[8], "4 not reported", "FLEX-009 prints dashes for its four quantities");
  assert.includes(summaries[9], "1 excluded");
  const shown = new Set([...dom.querySelectorAll(".test-outcome")].map((e) => e.textContent.replace("Test end as printed: ", "")));
  assert.deepEqual([...shown].sort(), ["Disruption", "Extinction"], "only the source's own labels appear");
  assert.ok([...shown].every((s) => OUTCOME_LABELS.has(s)));
});

test("display: a single card shows the test and its printed outcome, and says so when the outcome is missing", () => {
  const card = findingCard(BY_ID.get("flex.flex-007.burn_time"), BY_ID);
  assert.includes(card.textContent, "Test FLEX-007");
  assert.includes(card.textContent, "Test end as printed: Disruption");
  assert.ok(card.querySelector(".test-outcome").getAttribute("title").includes("Not a FlameGuard-SI classification"));
  const noOutcome = { ...BY_ID.get("flex.flex-007.burn_time"), test_outcome: null };
  assert.includes(testIdentity(noOutcome).textContent, "Test end as printed: Not reported");
  const legacy = { ...BY_ID.get("flex.flex-007.burn_time") };
  delete legacy.test_id;
  delete legacy.test_outcome;
  assert.equal(testIdentity(legacy), null, "legacy findings show nothing extra");
});

// ---------- excluded and missing values ----------
test("excluded: the withheld measurement never shows a number anywhere in the 40 findings", () => {
  const dom = render();
  assert.ok(!PRINTED_EXCLUDED.test(dom.textContent), "the excluded printed value must appear nowhere on the page");
  const excluded = dom.querySelector('[data-value-status="excluded"]');
  assert.ok(excluded, "the excluded value cell is marked");
  assert.includes(excluded.textContent, "value not shown");
  assert.equal(dom.querySelectorAll('[data-value-status="excluded"]').length, 1);
  const f = BY_ID.get("flex.flex-010.burning_rate_constant");
  assert.equal(f.value, null);
  const card = findingCard(f, BY_ID);
  assert.includes(card.textContent, "Excluded by FlameGuard-SI");
  assert.includes(card.textContent, "pending reconciliation with PSI data", "the curated number-free note is shown");
  assert.ok(!PRINTED_EXCLUDED.test(card.textContent));
});

test("excluded: a tampered record that carries the number still never prints it", () => {
  const tampered = { ...BY_ID.get("flex.flex-010.burning_rate_constant"), value: 0.37, statement: "TEST statement" };
  assert.ok(!PRINTED_EXCLUDED.test(findingCard(tampered, BY_ID).querySelector('[data-value-status="excluded"]').textContent));
});

test("missing: the 8 dashes show 'Not reported', never 0 or blank, and carry no value", () => {
  const missing = FINDINGS.filter((f) => f.value_status === "not_reported");
  assert.equal(missing.length, 8);
  for (const f of missing) {
    assert.equal(f.value, null);
    const cell = findingCard(f, BY_ID).querySelector('[data-value-status="not_reported"]');
    assert.ok(cell, f.id);
    assert.includes(cell.textContent, "Not reported");
    assert.ok(!/\b0\b/.test(cell.textContent), `${f.id} must not read as zero`);
  }
  assert.equal(missing.filter((f) => f.test_id === "FLEX-009").length, 4);
});

test("reported: every reported value is shown exactly as in the finding, with its unit", () => {
  for (const f of FINDINGS.filter((x) => x.value_status === "reported")) {
    const cell = findingCard(f, BY_ID).querySelector('[data-value-status="reported"]');
    assert.ok(cell, f.id);
    assert.includes(cell.textContent, String(f.value), f.id);
    assert.includes(cell.textContent, f.unit, f.id);
  }
});

// ---------- provenance ----------
test("provenance: every finding shows its locator, the Table IX source, and each caution's recorded quote and source", () => {
  for (const f of FINDINGS) {
    const card = findingCard(f, BY_ID);
    const text = card.textContent;
    assert.includes(text, f.provenance.locator, `${f.id}: locator`);
    assert.includes(text, f.provenance.manifest_id, `${f.id}: manifest id`);
    assert.includes(text, "TABLE IX", `${f.id}: Table IX source`);
    for (const n of f.curation_notes || []) {
      assert.includes(text, n.note, `${f.id}: note text`);
      assert.includes(text, n.source.quote, `${f.id}: recorded quote`);
      assert.includes(text, n.flag_ref.flag_id, `${f.id}: flag reference`);
      assert.includes(text, n.source.title, `${f.id}: note source title`);
    }
  }
});

test("provenance: cautions are labelled as FlameGuard-SI assessments, and a recorded quote is never called verified", () => {
  const text = render().textContent;
  assert.includes(text, "FlameGuard-SI assessment, not source text");
  assert.ok(!/verified quote|authenticated quote/i.test(text));
});

test("safety: nothing in the rendered findings is a link except to http(s) sources", () => {
  const dom = render();
  for (const a of dom.querySelectorAll("a")) assert.ok(/^https?:/.test(a.getAttribute("href") || ""), a.outerHTML);
});
