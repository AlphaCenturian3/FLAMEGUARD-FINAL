import { assert, test } from "./harness.js";
import { stubFetch } from "./samples.js";
import { ApiError, isNotImplemented } from "../static/js/api/errors.js";
import { createHttpSource } from "../static/js/api/http.js";
import { createFixtureSource } from "../static/js/api/fixtures.js";
import { createStore } from "../static/js/store.js";
import { reviewAnswer } from "../static/js/integrations/assistant.js";
import { reviewSimulation } from "../static/js/integrations/simulation.js";

const NOT_IMPL = { error: { code: "not_implemented", message: "This endpoint is planned in contract v0.1.0 and not implemented yet." } };
const EXAMPLES = new URL("../../contracts/examples/", import.meta.url).href;

test("http: 501 Error body becomes a not_implemented ApiError", async () => {
  const src = createHttpSource({ fetchImpl: stubFetch(501, NOT_IMPL) });
  await assert.rejects(src.listInvestigations(), (err) => {
    assert.ok(err instanceof ApiError);
    assert.equal(err.status, 501);
    assert.equal(err.code, "not_implemented");
    assert.ok(isNotImplemented(err));
  });
});

test("http: non-JSON error and network failure are handled", async () => {
  await assert.rejects(createHttpSource({ fetchImpl: stubFetch(500, "<html>oops</html>") }).health(), (err) => {
    assert.equal(err.status, 500);
    assert.equal(err.code, "http_500");
    assert.ok(!isNotImplemented(err));
  });
  const failing = async () => {
    throw new TypeError("Failed to fetch");
  };
  await assert.rejects(createHttpSource({ fetchImpl: failing }).health(), (err) => assert.equal(err.code, "network_error"));
});

test("http: endpoints and query encoding follow spec §5.1", async () => {
  const f = stubFetch(200, { items: [] });
  const src = createHttpSource({ baseUrl: "http://api.test/", fetchImpl: f });
  await src.listFindings("inv 1&x");
  await src.getRankings("lunar_base");
  await src.ask("why?");
  assert.equal(f.calls[0].url, "http://api.test/api/findings?investigation_id=inv%201%26x");
  assert.equal(f.calls[1].url, "http://api.test/api/rankings?context=lunar_base");
  assert.equal(f.calls[2].url, "http://api.test/api/assistant/ask");
  assert.equal(f.calls[2].init.method, "POST");
});

test("store: 501 on investigations yields not_implemented state, not empty data", async () => {
  const store = createStore(createHttpSource({ fetchImpl: stubFetch(501, NOT_IMPL) }));
  const ev = await store.evidence();
  assert.equal(ev.investigations.state, "not_implemented");
  assert.equal(ev.findings.state, "not_implemented");
  assert.equal(ev.investigations.data, undefined);
});

test("fixtures: contract examples load and are all marked fixture", async () => {
  const src = createFixtureSource({ baseUrl: EXAMPLES });
  assert.equal(src.kind, "fixtures");
  const invs = await src.listInvestigations();
  assert.equal(invs.contract_version, "0.1.0");
  assert.ok(invs.items.length > 0);
  assert.ok(invs.items.every((i) => i.fixture === true));
  const findings = await src.listFindings();
  assert.ok(findings.items.every((f) => f.fixture === true));
  assert.deepEqual(findings.items.map((f) => f.evidence_class).sort(), ["interpretation", "measured"]);
  const only = await src.listFindings("no-such-investigation");
  assert.equal(only.items.length, 0);
});

test("fixtures: rankings and assistant return 501 instead of invented results", async () => {
  const src = createFixtureSource({ baseUrl: EXAMPLES });
  await assert.rejects(src.getRankings("spacecraft"), (err) => assert.ok(isNotImplemented(err)));
  await assert.rejects(src.ask("q"), (err) => assert.ok(isNotImplemented(err)));
});

test("fixtures: missing fixture directory gives a fixture_unavailable error", async () => {
  const src = createFixtureSource({ baseUrl: "http://fixtures.test/", fetchImpl: stubFetch(404, {}) });
  await assert.rejects(src.listInvestigations(), (err) => assert.equal(err.code, "fixture_unavailable"));
});

test("fixtures: simulation example passes the label check", async () => {
  const sim = await createFixtureSource({ baseUrl: EXAMPLES }).getSimulation("fixture-sim-1");
  assert.deepEqual(reviewSimulation(sim), []);
  assert.ok(reviewSimulation({ ...sim, label: "Simulated flame" }).length > 0);
  assert.ok(reviewSimulation({ ...sim, evidence_class: "measured" }).length > 0);
});

test("assistant: answers must cite sources and be attributed to FlameGuard-SI", () => {
  const good = { answer: "a", citations: [{ title: "t", url: "https://example.invalid", retrieved: "2026-11-14" }], generated_by: "FlameGuard-SI" };
  assert.deepEqual(reviewAnswer(good), []);
  assert.ok(reviewAnswer({ ...good, generated_by: "NASA" }).length === 1);
  assert.ok(reviewAnswer({ ...good, citations: [] }).length === 1);
});

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

test("isolation: ranking, interpretation, and assistant never reach a simulation module", async () => {
  for (const entry of ["../static/js/model/ranking.js", "../static/js/views/rank.js", "../static/js/views/interpret.js", "../static/js/integrations/assistant.js"]) {
    const graph = await importGraph(entry);
    const bad = graph.filter((u) => /simulation/i.test(new URL(u).pathname.split("/").pop()));
    assert.deepEqual(bad, [], `${entry} reaches ${bad.join(", ")}`);
  }
  // Sanity check: the crawler does find the simulation module where it is used.
  assert.ok((await importGraph("../static/js/views/integrations.js")).some((u) => u.endsWith("/integrations/simulation.js")));
});
