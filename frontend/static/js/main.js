// App shell: hash router, navigation, data-source banner, and demo bar.

import { CONTRACT_VERSION, createDataSource, FIXTURE_BANNER, readConfig, urlWithFixtures, versionMismatch } from "./config.js";
import { createDemo } from "./demo.js";
import { createStore } from "./store.js";
import { prefersReducedMotion } from "./ui/announce.js";
import { h, mount } from "./ui/dom.js";
import * as compare from "./views/compare.js";
import * as dashboard from "./views/dashboard.js";
import * as explorer from "./views/explorer.js";
import * as integrations from "./views/integrations.js";
import * as interpret from "./views/interpret.js";
import * as rank from "./views/rank.js";
import * as tars from "./views/tars.js";

/**
 * @typedef {Object} ViewContext
 * @property {ReturnType<typeof createStore>} store
 * @property {URLSearchParams} params   query string inside the hash route
 * @property {ReturnType<typeof createDemo>} demo
 * @property {(fn: () => void) => void} onLeave  register cleanup for route change
 */

export const ROUTES = {
  "/": { view: dashboard, nav: "Overview", icon: "◎" },
  "/explorer": { view: explorer, nav: "Evidence Explorer", icon: "⌕" },
  "/compare": { view: compare, nav: "Compare", icon: "⇄" },
  "/rank": { view: rank, nav: "Rank", icon: "≡" },
  "/interpret": { view: interpret, nav: "Interpret & Insight", icon: "◈" },
  "/tars": { view: tars, nav: "TARS assistant", icon: "?" },
  "/integrations": { view: integrations, nav: "Integrations", icon: "⚙" },
};

const config = readConfig();
const source = createDataSource(config);
const store = createStore(source);

const main = document.getElementById("main");
const nav = document.getElementById("nav");
const banner = document.getElementById("source-banner");
const health = document.getElementById("health");
const menuButton = document.getElementById("menu-button");

let cleanups = [];

const demo = createDemo({
  go(route, anchor) {
    if (location.hash !== route) location.hash = route;
    else renderRoute();
    if (anchor) requestAnimationFrame(() => setTimeout(() => document.getElementById(anchor)?.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" }), 50));
  },
  async selectAll() {
    const ev = await store.evidence();
    if (ev.investigations.state === "ready") store.selection.set(ev.investigations.data.map((i) => i.id));
  },
});
document.body.appendChild(demo.element);

function parseHash() {
  const raw = location.hash.replace(/^#/, "") || "/";
  const [path, query = ""] = raw.split("?");
  return { path: ROUTES[path] ? path : null, params: new URLSearchParams(query) };
}

function renderNav(active) {
  mount(
    nav,
    h(
      "ul",
      null,
      Object.entries(ROUTES).map(([path, r]) =>
        h(
          "li",
          null,
          h("a", { href: `#${path}`, class: path === active ? "active" : null, "aria-current": path === active ? "page" : null }, h("span", { class: "nav-icon", "aria-hidden": "true" }, r.icon), r.nav),
        ),
      ),
      h("li", null, h("button", { type: "button", class: "nav-demo", onclick: () => demo.start() }, h("span", { class: "nav-icon", "aria-hidden": "true" }, "▶"), "Judge demo")),
    ),
  );
}

function renderRoute() {
  cleanups.forEach((fn) => fn());
  cleanups = [];
  const { path, params } = parseHash();
  document.body.classList.remove("nav-open");
  menuButton?.setAttribute("aria-expanded", "false");

  if (!path) {
    renderNav(null);
    mount(main, h("section", { class: "view" }, h("h1", { tabindex: "-1" }, "Page not found"), h("p", null, h("a", { href: "#/" }, "Back to overview"))));
    return;
  }
  const route = ROUTES[path];
  renderNav(path);
  document.title = `${route.view.title} · FlameGuard-SI`;
  /** @type {ViewContext} */
  const ctx = { store, params, demo, onLeave: (fn) => cleanups.push(fn) };
  mount(main, route.view.render(ctx));
  // On navigation (not the first page load, so the skip link stays the first
  // Tab stop), move focus to the new heading for keyboard and screen-reader users.
  const heading = main.querySelector("h1");
  if (heading && !demo.active() && !firstRender) heading.focus({ preventScroll: true });
  if (!demo.active()) window.scrollTo(0, 0);
  firstRender = false;
}
let firstRender = true;

const fixtureBanner = h("div", { id: "fixture-banner" });
const alerts = h("div", { id: "alerts" });
banner.append(fixtureBanner, alerts);
const alertMessages = new Set();

function addAlert(text, kind = "warn") {
  if (alertMessages.has(text)) return;
  alertMessages.add(text);
  alerts.appendChild(h("div", { class: `banner banner-${kind}`, role: kind === "error" ? "alert" : "status" }, text));
}

function renderFixtureBanner() {
  if (source.kind !== "fixtures") return;
  // Permanent on every page while fixture mode is on (spec §5.3).
  mount(
    fixtureBanner,
    h(
      "div",
      { class: "banner banner-fixture", role: "note" },
      h("strong", null, FIXTURE_BANNER),
      " Showing contract examples from contracts/examples/ with invented placeholder content. ",
      h("a", { href: urlWithFixtures(false) }, "Switch to live API"),
    ),
  );
}

async function checkHealth() {
  mount(health, h("span", { class: "badge" }, "API: checking…"));
  try {
    const res = await source.health();
    const mismatch = versionMismatch(res.contract_version);
    mount(
      health,
      h(
        "span",
        { class: `badge ${mismatch ? "err" : source.kind === "fixtures" ? "fixture" : "ok"}`, title: source.description },
        `${source.kind === "fixtures" ? "Fixtures" : "API"} · contract ${res.contract_version}`,
      ),
    );
    if (mismatch) addAlert(mismatch, "error");
  } catch (err) {
    mount(health, h("span", { class: "badge err", title: err.message }, "API unreachable"));
    if (source.kind === "api") {
      alerts.appendChild(
        h(
          "div",
          { class: "banner banner-error", role: "alert" },
          h("strong", null, "The FlameGuard-SI API is not reachable. "),
          `${err.message} `,
          "Start the backend, or ",
          h("a", { href: urlWithFixtures(true) }, "view the interface with contract fixtures (not NASA data)"),
          ".",
        ),
      );
    }
  }
}

store.evidence().then((ev) => ev.warnings.forEach((w) => addAlert(w)));

// The footer states the contract version this dashboard implements, from the single constant.
{
  const footer = document.getElementById("footer-contract");
  if (footer) footer.textContent = `Dashboard implements contract v${CONTRACT_VERSION}.`;
}

// ---- Theme (F8): follows the system unless the viewer picks one. ----
const THEME_KEY = "flameguard.theme";
function applyTheme(theme) {
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
  const btn = document.getElementById("theme-button");
  if (btn) {
    const effective = theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    btn.setAttribute("aria-pressed", String(effective === "light"));
    // The accessible name stays "Light theme"; aria-pressed carries the state (WCAG 4.1.2, 2.5.3).
  }
}
let savedTheme = null;
try {
  savedTheme = localStorage.getItem(THEME_KEY);
} catch {
  // storage unavailable
}
applyTheme(savedTheme);
document.getElementById("theme-button")?.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  const next = current === "light" ? "dark" : "light";
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    // storage unavailable; the choice lasts for this page only
  }
  applyTheme(next);
});

// The skip link must not change the hash (the router would treat "#main" as a route).
document.querySelector(".skip-link")?.addEventListener("click", (e) => {
  e.preventDefault();
  main.focus();
  main.scrollIntoView();
});

menuButton?.addEventListener("click", () => {
  const open = document.body.classList.toggle("nav-open");
  menuButton.setAttribute("aria-expanded", String(open));
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && document.body.classList.contains("nav-open")) {
    document.body.classList.remove("nav-open");
    menuButton?.setAttribute("aria-expanded", "false");
    menuButton?.focus();
  }
});

window.addEventListener("hashchange", renderRoute);
renderFixtureBanner();
checkHealth();
renderRoute();
