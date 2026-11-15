// Automated accessibility regression checks (WCAG 2.2 AA oriented) on all seven pages, in the
// dark and light themes, in real Chrome. Automated only: no screen reader is involved.
import { assert, test } from "./harness.js";
import {
  contrastFailures,
  controlBorderFailures,
  duplicateIds,
  headingProblems,
  loadPage,
  targetSizeFailures,
  textOutsideLandmarks,
  unnamedControls,
} from "./a11y-audit.js";

const ROUTES = ["#/", "#/explorer", "#/compare", "#/rank", "#/interpret", "#/tars", "#/integrations"];
const app = (route, query = "?fixtures=1") => new URL(`../index.html${query}${route}`, import.meta.url).href;

for (const theme of ["dark", "light"]) {
  test(`a11y ${theme}: text contrast >= 4.5:1 (3:1 large) on all 7 pages, details expanded`, async () => {
    const fails = [];
    for (const route of ROUTES) {
      const p = await loadPage(app(route), { theme });
      p.doc.querySelectorAll("details").forEach((d) => (d.open = true));
      await new Promise((r) => setTimeout(r, 50));
      fails.push(...contrastFailures(p.doc, p.win).map((f) => `${route} ${f}`));
      p.close();
    }
    assert.deepEqual(fails, [], `${fails.length} contrast failures: ${JSON.stringify(fails)}`);
  });

  test(`a11y ${theme}: form-control boundaries >= 3:1 (WCAG 1.4.11)`, async () => {
    const fails = [];
    for (const route of ["#/explorer", "#/compare", "#/rank", "#/tars"]) {
      const p = await loadPage(app(route), { theme });
      fails.push(...controlBorderFailures(p.doc, p.win).map((f) => `${route} ${f}`));
      p.close();
    }
    assert.deepEqual(fails, []);
  });
}

test("a11y: landmarks, one h1 with no skipped heading levels, names, unique ids, 24px targets (7 pages)", async () => {
  const problems = [];
  for (const route of ROUTES) {
    const p = await loadPage(app(route));
    p.doc.querySelectorAll("details").forEach((d) => (d.open = true));
    for (const [what, list] of [
      ["outside landmarks", textOutsideLandmarks(p.doc, p.win)],
      ["headings", headingProblems(p.doc)],
      ["no accessible name", unnamedControls(p.doc)],
      ["duplicate id", duplicateIds(p.doc)],
      ["target < 24px", targetSizeFailures(p.doc)],
    ]) {
      problems.push(...list.map((x) => `${route} ${what}: ${x}`));
    }
    p.close();
  }
  assert.deepEqual(problems, [], `${problems.length} problems: ${JSON.stringify(problems)}`);
});

test("a11y: reflow at 320 CSS px (WCAG 1.4.10), no horizontal scrolling on any page", async () => {
  const fails = [];
  for (const route of ROUTES) {
    const p = await loadPage(app(route), { width: 320, height: 640 });
    const w = p.doc.documentElement.scrollWidth;
    if (w > 320) {
      const over = [...p.doc.querySelectorAll("body *")]
        .filter((el) => el.getBoundingClientRect().right > 320.5 && !el.closest(".table-wrap"))
        .slice(0, 5)
        .map((el) => `${el.tagName.toLowerCase()}.${String(el.className).split(" ")[0]}(${Math.round(el.getBoundingClientRect().right)})`);
      fails.push(`${route} scrollWidth ${w} [${over.join(", ")}]`);
    }
    p.close();
  }
  assert.deepEqual(fails, []);
});

// ---------- Regression tests for the specific issues fixed on this branch ----------
import { accessibleName, waitFor } from "./a11y-audit.js";
import { statePanel } from "../static/js/ui/components.js";

test("a11y: notices live in a labelled region and the permanent fixture warning is preserved", async () => {
  const p = await loadPage(app("#/explorer"));
  const region = p.doc.getElementById("source-banner");
  assert.equal(region.getAttribute("role"), "region");
  assert.equal(region.getAttribute("aria-label"), "Data source notices");
  assert.includes(region.textContent, "FIXTURE DATA. NOT NASA DATA.");
  p.close();
});

test("a11y: Explorer results are not a live region; the result count is a status message", async () => {
  const p = await loadPage(app("#/explorer"));
  assert.equal(p.doc.querySelector(".results").hasAttribute("aria-live"), false);
  assert.equal(p.doc.querySelector(".result-count").getAttribute("role"), "status");
  p.close();
});

test("a11y: each Compare checkbox has a unique accessible name naming its investigation", async () => {
  const p = await loadPage(app("#/explorer"));
  const name = accessibleName(p.doc.querySelector(".compare-toggle input"));
  assert.includes(name, "Compare");
  assert.includes(name, "FIXTURE PLACEHOLDER INVESTIGATION");
  p.close();
});

test("a11y: theme button keeps the name 'Light theme' and reports state with aria-pressed", async () => {
  const p = await loadPage(app("#/"));
  const btn = p.doc.getElementById("theme-button");
  const before = btn.getAttribute("aria-pressed");
  btn.click();
  await new Promise((r) => setTimeout(r, 50));
  assert.equal(accessibleName(btn), "Light theme");
  assert.ok(btn.getAttribute("aria-pressed") !== before, "aria-pressed toggles");
  btn.click(); // restore
  try {
    p.win.localStorage.removeItem("flameguard.theme");
  } catch {
    // storage unavailable
  }
  p.close();
});

test("a11y: empty TARS question shows a text error, marks the field invalid and focuses it", async () => {
  const p = await loadPage(app("#/tars"));
  const input = p.doc.getElementById("ask-q");
  p.doc.querySelector("#main form button[type=submit]").click();
  await new Promise((r) => setTimeout(r, 50));
  const err = p.doc.getElementById("ask-q-error");
  assert.equal(err.hidden, false);
  assert.equal(err.getAttribute("role"), "alert");
  assert.includes(err.textContent, "Enter a question");
  assert.equal(input.getAttribute("aria-invalid"), "true");
  assert.equal(input.getAttribute("aria-describedby"), "ask-q-error");
  assert.equal(p.doc.activeElement, input);
  input.value = "q";
  input.dispatchEvent(new p.win.Event("input"));
  assert.equal(err.hidden, true);
  assert.equal(input.hasAttribute("aria-invalid"), false);
  p.close();
});

test("a11y: a comparison result is announced as one line through the shared status region", async () => {
  const p = await loadPage(app("#/compare"));
  assert.equal(p.doc.querySelector(".compare-body").hasAttribute("aria-live"), false);
  p.doc.querySelector(".compare-controls button[type=submit]").click();
  await waitFor(() => /Comparison loaded/.test(p.doc.getElementById("announcer").textContent), 5000, "announcement");
  assert.includes(p.doc.getElementById("announcer").textContent, "not comparable, 2 reasons given");
  assert.equal(p.doc.getElementById("announcer").getAttribute("role"), "status");
  p.close();
});

test("a11y: reduced motion turns off animations and transitions (CSS) and smooth scrolling (JS)", async () => {
  const p = await loadPage(app("#/"));
  const rules = [...p.doc.styleSheets].flatMap((s) => [...s.cssRules]);
  const media = rules.filter((r) => r.conditionText && r.conditionText.includes("prefers-reduced-motion: reduce"));
  const styles = media.flatMap((m) => [...m.cssRules]).map((r) => r.style).filter(Boolean);
  assert.ok(
    styles.some((s) => s.getPropertyValue("animation-name") === "none" && s.getPropertyValue("transition-property") === "none"),
    "a prefers-reduced-motion rule sets animation and transition to none",
  );
  const src = await (await fetch(new URL("../static/js/main.js", import.meta.url))).text();
  assert.includes(src, 'behavior: prefersReducedMotion() ? "auto" : "smooth"');
  p.close();
});

test("a11y: with the demo bar open, scroll padding keeps focused content clear of it (WCAG 2.4.11)", async () => {
  const p = await loadPage(app("#/"));
  p.doc.querySelector(".nav-demo").click();
  await waitFor(() => !p.doc.querySelector(".demo-bar").hidden, 3000, "demo bar");
  const html = p.doc.documentElement;
  assert.ok(html.classList.contains("demo-active"));
  const pad = parseFloat(p.win.getComputedStyle(html).scrollPaddingBottom);
  const bar = p.doc.querySelector(".demo-bar").getBoundingClientRect();
  const gap = p.win.innerHeight - bar.top;
  assert.ok(pad >= gap, `scroll-padding-bottom ${pad}px must cover the bar (${Math.round(gap)}px)`);
  assert.ok(parseFloat(p.win.getComputedStyle(html).scrollPaddingTop) >= p.doc.querySelector(".topbar").offsetHeight);
  p.doc.querySelector(".demo-bar [data-action=exit]").click();
  assert.equal(html.classList.contains("demo-active"), false);
  p.close();
});

test("a11y: loading, empty, error and 501 states are understandable without colour", () => {
  for (const kind of ["loading", "empty", "error", "not_implemented"]) {
    const el = statePanel({ kind, title: `TEST ${kind} title` });
    assert.includes(el.textContent, `TEST ${kind} title`);
    assert.ok(["status", "alert"].includes(el.getAttribute("role")), kind);
  }
});
