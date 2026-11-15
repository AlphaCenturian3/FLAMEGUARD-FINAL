// Tiny dependency-free test harness for browser ES modules.
// Results are written to #results and summarised in document.title as
// "PASS n/n" or "FAIL k/n" so a headless browser run can be checked.

const tests = [];

export function test(name, fn) {
  tests.push({ name, fn });
}

export class AssertionError extends Error {}

export const assert = {
  ok(value, msg = "expected truthy") {
    if (!value) throw new AssertionError(msg);
  },
  equal(actual, expected, msg) {
    if (actual !== expected) throw new AssertionError(msg || `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  },
  deepEqual(actual, expected, msg) {
    const a = JSON.stringify(actual);
    const b = JSON.stringify(expected);
    if (a !== b) throw new AssertionError(msg || `expected ${b}, got ${a}`);
  },
  includes(haystack, needle, msg) {
    if (!haystack || !haystack.includes(needle)) throw new AssertionError(msg || `expected ${JSON.stringify(haystack)} to include ${JSON.stringify(needle)}`);
  },
  async rejects(promiseOrFn, check, msg = "expected rejection") {
    try {
      await (typeof promiseOrFn === "function" ? promiseOrFn() : promiseOrFn);
    } catch (err) {
      if (check) check(err);
      return;
    }
    throw new AssertionError(msg);
  },
};

export async function run() {
  const out = document.getElementById("results");
  let passed = 0;
  const lines = [];
  for (const t of tests) {
    try {
      await t.fn();
      passed += 1;
      lines.push(`ok   ${t.name}`);
    } catch (err) {
      lines.push(`FAIL ${t.name}\n     ${err && err.stack ? err.stack.split("\n").slice(0, 3).join("\n     ") : err}`);
    }
  }
  const failed = tests.length - passed;
  lines.push("", `${passed} passed, ${failed} failed, ${tests.length} total`);
  out.textContent = lines.join("\n");
  document.title = failed ? `FAIL ${failed}/${tests.length}` : `PASS ${passed}/${tests.length}`;
  document.body.dataset.status = failed ? "fail" : "pass";
}
