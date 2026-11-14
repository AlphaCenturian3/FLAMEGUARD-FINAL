// App shell: hash router, navigation, data-source banner, and demo bar.

import { createDataSource, readConfig, urlWithSource } from "./config.js";
import { createDemo } from "./demo.js";
import { createStore } from "./store.js";
import { h, mount } from "./ui/dom.js";
import * as compare from "./views/compare.js";
import * as dashboard from "./views/dashboard.js";
import * as explorer from "./views/explorer.js";
import * as integrations from "./views/integrations.js";
import * as interpret from "./views/interpret.js";
import * as rank from "./views/rank.js";

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
    if (anchor) requestAnimationFrame(() => setTimeout(() => document.getElementById(anchor)?.scrollIntoView({ behavior: "smooth", block: "start" }), 50));
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
  // Move focus to the new page heading for keyboard and screen-reader users.
  const heading = main.querySelector("h1");
  if (heading && !demo.active()) heading.focus({ preventScroll: true });
  if (!demo.active()) window.scrollTo(0, 0);
}

function renderBanner() {
  if (source.kind === "fixtures") {
    mount(
      banner,
      h(
        "div",
        { class: "banner banner-fixture", role: "note" },
        h("strong", null, "Fixture mode. "),
        "Showing contract examples from contracts/examples/ with invented placeholder content. This is not NASA data. ",
        h("a", { href: urlWithSource("api") }, "Switch to live API"),
      ),
    );
  } else {
    mount(banner);
  }
}

async function checkHealth() {
  mount(health, h("span", { class: "badge" }, "API: checking…"));
  try {
    const res = await source.health();
    mount(health, h("span", { class: `badge ${source.kind === "fixtures" ? "fixture" : "ok"}`, title: source.description }, source.kind === "fixtures" ? `Fixtures · contract ${res.contract_version}` : `API ok · contract ${res.contract_version}`));
  } catch (err) {
    mount(health, h("span", { class: "badge err", title: err.message }, "API unreachable"));
    if (source.kind === "api") {
      mount(
        banner,
        h(
          "div",
          { class: "banner banner-error", role: "alert" },
          h("strong", null, "The FlameGuard-SI API is not reachable. "),
          `${err.message} `,
          "Start the backend, or ",
          h("a", { href: urlWithSource("fixtures") }, "view the interface with contract fixtures (not NASA data)"),
          ".",
        ),
      );
    }
  }
}

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
renderBanner();
checkHealth();
renderRoute();
