import { assert, test } from "./harness.js";
import { byId, excluded, interpretation, measured, stubFetch } from "./samples.js";
import { ApiError, isNotImplemented } from "../static/js/api/errors.js";
import { createHttpSource } from "../static/js/api/http.js";
import { createFixtureSource } from "../static/js/api/fixtures.js";
import { CONTRACT_VERSION, FIXTURE_BANNER, readConfig, urlWithFixtures, versionMismatch } from "../static/js/config.js";
import { createStore, listWarnings } from "../static/js/store.js";
import { answerView, reviewAnswer } from "../static/js/integrations/assistant.js";
import { reviewSimulation } from "../static/js/integrations/simulation.js";
import { reviewRankings } from "../static/js/model/ranking.js";
import { reviewComparison } from "../static/js/model/compare.js";
import { provenanceIssues } from "../static/js/model/evidence.js";

const NOT_IMPL = { error: { code: "not_implemented", message: "This endpoint is planned in contract v0.2.0 and not implemented yet." } };
const EXAMPLES = new URL("../../contracts/examples/", import.meta.url).href;
const example = async (name) => (await fetch(new URL(name, EXAMPLES))).json();

// ---------- Config: fixture mode and version (P6/P7) ----------
test("config: fixture mode only with ?fixtures=1; contract version is 0.2.0", () => {
  assert.equal(CONTRACT_VERSION, "0.2.0");
  assert.equal(FIXTURE_BANNER, "FIXTURE DATA. NOT NASA DATA.");
  assert.equal(readConfig("http://x.test/frontend/index.html").source, "api");
  assert.equal(readConfig("http://x.test/frontend/index.html?fixtures=1").source, "fixtures");
  assert.equal(readConfig("http://x.test/frontend/index.html?fixtures=0").source, "api");
  assert.equal(readConfig("http://x.test/frontend/index.html?source=fixtures").source, "api", "the v0.1 switch no longer enables fixtures");
  assert.equal(readConfig("http://x.test/frontend/index.html?fixtures=1").fixturesBase, "http://x.test/contracts/examples/");
  assert.equal(new URL(urlWithFixtures(true, "http://x.test/?a=1#/rank")).searchParams.get("fixtures"), "1");
  assert.equal(new URL(urlWithFixtures(false, "http://x.test/?fixtures=1")).searchParams.has("fixtures"), false);
});

test("config: a different API contract version produces a warning", () => {
  assert.equal(versionMismatch("0.2.0"), null);
  assert.includes(versionMismatch("0.1.0"), "reports contract 0.1.0");
  assert.equal(versionMismatch(undefined), null);
});

test("store: list display checks warn on total mismatch (S7) and version, never alter data", () => {
  assert.deepEqual(listWarnings({ contract_version: "0.2.0", items: [1, 2], total: 2 }, "L"), []);
  assert.includes(listWarnings({ contract_version: "0.2.0", items: [1], total: 2 }, "L").join(" "), "S7");
  assert.includes(listWarnings({ contract_version: "0.1.0", items: [], total: 0 }, "L").join(" "), "0.1.0");
  assert.includes(listWarnings({ items: [] }, "L").join(" "), "no total");
});

// ---------- HTTP adapter (F6) ----------
test("http: 501 Error body becomes a not_implemented ApiError", async () => {
  const src = createHttpSource({ fetchImpl: stubFetch(501, NOT_IMPL) });
  await assert.rejects(src.listInvestigations(), (err) => {
    assert.ok(err instanceof ApiError);
    assert.equal(err.status, 501);
    assert.ok(isNotImplemented(err));
  });
});

test("http: 400, 404, non-JSON errors and network failure are distinguished", async () => {
  await assert.rejects(createHttpSource({ fetchImpl: stubFetch(400, { error: { code: "invalid_request", message: "bad context" } }) }).getRankings("mars"), (err) => assert.equal(err.code, "invalid_request"));
  await assert.rejects(createHttpSource({ fetchImpl: stubFetch(404, { error: { code: "not_found", message: "no" } }) }).getInvestigation("x"), (err) => assert.equal(err.code, "not_found"));
  await assert.rejects(createHttpSource({ fetchImpl: stubFetch(500, "<html>oops</html>") }).health(), (err) => assert.equal(err.code, "http_500"));
  const failing = async () => {
    throw new TypeError("Failed to fetch");
  };
  await assert.rejects(createHttpSource({ fetchImpl: failing }).health(), (err) => assert.equal(err.code, "network_error"));
});

test("http: endpoints and query encoding follow spec §5.1 (v0.2.0)", async () => {
  const f = stubFetch(200, { items: [] });
  const src = createHttpSource({ baseUrl: "http://api.test/", fetchImpl: f });
  await src.listFindings("inv 1&x");
  await src.compare("flame_spread_rate", ["a", "b c"]);
  await src.compare("flame_spread_rate");
  await src.getRankings("lunar_base");
  await src.ask("why?", ["a"]);
  assert.equal(f.calls[0].url, "http://api.test/api/findings?investigation_id=inv%201%26x");
  assert.equal(f.calls[1].url, "http://api.test/api/compare?quantity=flame_spread_rate&investigation_ids=a,b%20c");
  assert.equal(f.calls[2].url, "http://api.test/api/compare?quantity=flame_spread_rate");
  assert.equal(f.calls[3].url, "http://api.test/api/rankings?context=lunar_base");
  assert.equal(f.calls[4].init.method, "POST");
  assert.deepEqual(JSON.parse(f.calls[4].init.body), { question: "why?", investigation_ids: ["a"] });
});

test("store: 501 on lists yields not_implemented state, not empty data", async () => {
  const store = createStore(createHttpSource({ fetchImpl: stubFetch(501, NOT_IMPL) }));
  const ev = await store.evidence();
  assert.equal(ev.investigations.state, "not_implemented");
  assert.equal(ev.investigations.data, undefined);
});

// ---------- Fixture adapter against the merged v0.2.0 examples ----------
test("fixtures: every v0.2.0 example loads, every record is a fixture, list totals hold", async () => {
  const src = createFixtureSource({ baseUrl: EXAMPLES });
  const invs = await src.listInvestigations();
  assert.equal(invs.contract_version, "0.2.0");
  assert.equal(invs.total, invs.items.length);
  assert.ok(invs.items.every((i) => i.fixture === true));
  const fl = await src.listFindings();
  assert.equal(fl.total, fl.items.length);
  assert.ok(fl.items.every((f) => f.fixture === true));
  assert.deepEqual([...new Set(fl.items.map((f) => f.value_status))].sort(), ["excluded", "not_applicable", "not_reported", "reported"]);
  const only = await src.listFindings("fixture-investigation-2");
  assert.equal(only.total, only.items.length);
});

test("fixtures: all example findings pass the frontend's v0.2.0 provenance check", async () => {
  const fl = await example("finding_list.example.json");
  for (const f of fl.items) assert.deepEqual(provenanceIssues(f), [], f.id);
  for (const name of ["finding.measured.example.json", "finding.measured_caution.example.json", "finding.measured_excluded.example.json", "finding.measured_missing.example.json", "finding.interpretation.example.json"]) {
    assert.deepEqual(provenanceIssues(await example(name)), [], name);
  }
});

test("fixtures: ranking, comparison and answer examples render through the display guards", async () => {
  const src = createFixtureSource({ baseUrl: EXAMPLES });
  const map = byId((await src.listFindings()).items);
  const r = reviewRankings(await src.getRankings("spacecraft"), map);
  assert.equal(r.accepted.length, 1, JSON.stringify(r.rejected.map((x) => x.problems)));
  assert.equal(r.notRanked.length, 1);
  const c = reviewComparison(await src.compare("flame_spread_rate"), map);
  assert.equal(c.chartable, false, "the example is not comparable; it must not be charted");
  assert.deepEqual(c.problems, []);
  assert.deepEqual(reviewAnswer(await src.ask("q"), map).problems, []);
});

test("fixtures: requests with no example return not_found instead of an invented result", async () => {
  const src = createFixtureSource({ baseUrl: EXAMPLES });
  await assert.rejects(src.getRankings("lunar_base"), (err) => assert.equal(err.code, "not_found"));
  await assert.rejects(src.compare("flame_temperature"), (err) => assert.equal(err.code, "not_found"));
});

test("fixtures: missing fixture directory gives a fixture_unavailable error", async () => {
  const src = createFixtureSource({ baseUrl: "http://fixtures.test/", fetchImpl: stubFetch(404, {}) });
  await assert.rejects(src.listInvestigations(), (err) => assert.equal(err.code, "fixture_unavailable"));
});

test("fixtures: simulation example passes the label check", async () => {
  const sim = await createFixtureSource({ baseUrl: EXAMPLES }).getSimulation("fixture-sim-1");
  assert.deepEqual(reviewSimulation(sim), []);
  assert.ok(reviewSimulation({ ...sim, label: "Simulated flame" }).length > 0);
});

// ---------- P5: TARS ----------
const SRC = { title: "TEST SOURCE", url: "https://example.invalid/t", retrieved: "2026-11-14" };
const ANSWER = (extra = {}) => ({ contract_version: "0.2.0", answer: "TEST answer.", mode: "fallback_quotes", citations: [{ finding_id: "m", evidence_class: "measured", source: SRC }], generated_by: "FlameGuard-SI", limitations: ["TEST limitation"], ...extra });
const TARS_FINDINGS = byId([measured("m", "a"), excluded("e", "a"), interpretation("i1", "a", ["e"]), interpretation("i2", "a", ["i1"])]);

test("tars: valid answers in each mode pass; attribution, citations and limitations are required", () => {
  assert.deepEqual(reviewAnswer(ANSWER(), TARS_FINDINGS).problems, []);
  assert.deepEqual(reviewAnswer(ANSWER({ mode: "ai" }), TARS_FINDINGS).problems, []);
  assert.deepEqual(reviewAnswer(ANSWER({ mode: "no_evidence", citations: [], limitations: [] }), TARS_FINDINGS).problems, []);
  assert.includes(reviewAnswer(ANSWER({ generated_by: "NASA" }), TARS_FINDINGS).problems.join(" "), "FlameGuard-SI");
  assert.includes(reviewAnswer(ANSWER({ citations: [] }), TARS_FINDINGS).problems.join(" "), "cites no findings");
  assert.includes(reviewAnswer(ANSWER({ limitations: [] }), TARS_FINDINGS).problems.join(" "), "no limitations");
  assert.includes(reviewAnswer(ANSWER({ citations: [{ finding_id: "ghost", evidence_class: "measured", source: SRC }] }), TARS_FINDINGS).problems.join(" "), "does not resolve");
});

test("tars: an exclusion-dependent citation is an exclusion explanation, and needs its exclusion reason (S9)", () => {
  for (const id of ["e", "i1", "i2"]) {
    const cls = id === "e" ? "measured" : "interpretation";
    const bad = reviewAnswer(ANSWER({ citations: [{ finding_id: id, evidence_class: cls, source: SRC }] }), TARS_FINDINGS);
    assert.includes(bad.problems.join(" "), "does not give the exclusion reason", id);
    const good = reviewAnswer(ANSWER({ answer: "One value is excluded: TEST exclusion reason for e", citations: [{ finding_id: id, evidence_class: cls, source: SRC }] }), TARS_FINDINGS);
    assert.deepEqual(good.problems, [], id);
    assert.equal(good.citations[0].role, "exclusion_explanation");
  }
  assert.equal(reviewAnswer(ANSWER(), TARS_FINDINGS).citations[0].role, "evidence");
});

test("tars: rendered answer shows mode, attribution, limitations and separates exclusion explanations", () => {
  const el = answerView(ANSWER({ answer: "TEST exclusion reason for e. Also evidence.", citations: [{ finding_id: "m", evidence_class: "measured", source: SRC }, { finding_id: "i2", evidence_class: "interpretation", source: SRC }] }), TARS_FINDINGS);
  const text = el.textContent;
  assert.includes(text, "Quotes only (no AI)");
  assert.includes(text, "Generated by FlameGuard-SI. Not a NASA statement.");
  assert.includes(text, "TEST limitation");
  assert.includes(text, "Evidence cited (1)");
  assert.includes(text, "Cited to explain exclusions (1)");
  assert.includes(text, "Cited only to explain an exclusion");
  const withheld = answerView(ANSWER({ generated_by: "NASA" }), TARS_FINDINGS);
  assert.includes(withheld.textContent, "Answer withheld by dashboard check");
  assert.ok(!withheld.textContent.includes("TEST answer."), "a withheld answer's text is not shown");
});

// ---------- Isolation ----------
/** All modules reachable from `entry` through static or dynamic imports. */
async function importGraph(entry) {
  const seen = new Set();
  const queue = [new URL(entry, import.meta.url).href];
  const specifier = /(?:import|export)\s[^;]*?from\s*["']([^"']+)["']|import\s*\(\s*["']([^"']+)["']\s*\)|import\s*["']([^"']+)["']/g;
  while (queue.length) {
    const url = queue.pop();
    if (seen.has(url)) continue;
    seen.add(url);
    // Strip comments first: JSDoc `import("...")` type annotations are not real imports.
    const text = (await (await fetch(url)).text()).replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");
    for (const m of text.matchAll(specifier)) queue.push(new URL(m[1] || m[2] || m[3], url).href);
  }
  return [...seen];
}

test("isolation: ranking, interpretation, compare and TARS never reach a simulation module", async () => {
  for (const entry of ["../static/js/model/ranking.js", "../static/js/views/rank.js", "../static/js/views/interpret.js", "../static/js/views/compare.js", "../static/js/integrations/assistant.js"]) {
    const graph = await importGraph(entry);
    const bad = graph.filter((u) => /simulation/i.test(new URL(u).pathname.split("/").pop()));
    assert.deepEqual(bad, [], `${entry} reaches ${bad.join(", ")}`);
  }
  assert.ok((await importGraph("../static/js/views/integrations.js")).some((u) => u.endsWith("/integrations/simulation.js")));
});

test("attribution: the phrase 'according to NASA' appears in no frontend module", async () => {
  const graph = await importGraph("../static/js/main.js");
  for (const url of graph) assert.ok(!/according to NASA/i.test(await (await fetch(url)).text()), url);
});
