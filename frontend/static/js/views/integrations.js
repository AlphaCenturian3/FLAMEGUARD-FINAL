// Integration status page. Probes every contract endpoint and hosts the
// isolated assistant and simulation panels.

import { renderAssistantPanel } from "../integrations/assistant.js";
import { renderSimulationPanel } from "../integrations/simulation.js";
import { isNotImplemented } from "../api/errors.js";
import { h, mount } from "../ui/dom.js";

export const title = "Integrations";

const PROBES = [
  { label: "GET /api/health", owner: "Backend", run: (s) => s.health() },
  { label: "GET /api/investigations", owner: "Backend + data", run: (s) => s.listInvestigations() },
  { label: "GET /api/findings", owner: "Backend + data", run: (s) => s.listFindings() },
  { label: "GET /api/rankings?context=spacecraft", owner: "Backend (ranking)", run: (s) => s.getRankings("spacecraft") },
  { label: "GET /api/simulations/{id}", owner: "Backend (simulation)", run: (s) => s.getSimulation("fixture-sim-1") },
];

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  const tbody = h("tbody");
  const root = h(
    "section",
    { class: "view" },
    h("header", { class: "view-head" }, h("h1", { tabindex: "-1" }, title), h("p", { class: "lede" }, `Live status of each contract endpoint from ${ctx.store.source.description}.`)),
    h(
      "section",
      { class: "card" },
      h("h2", null, "Endpoint status"),
      h("div", { class: "table-wrap", tabindex: "0", role: "region", "aria-label": "Endpoint status" }, h("table", null, h("thead", null, h("tr", null, h("th", { scope: "col" }, "Endpoint"), h("th", { scope: "col" }, "Owner"), h("th", { scope: "col" }, "Status"))), tbody)),
      h("p", { class: "small muted" }, "POST /api/assistant/ask is exercised only when a question is submitted below."),
    ),
    h("div", { class: "two-col" }, renderAssistantPanel(ctx.store.source), renderSimulationPanel(ctx.store.source)),
  );

  for (const p of PROBES) {
    const status = h("td", null, h("span", { class: "badge" }, "checking…"));
    tbody.appendChild(h("tr", null, h("th", { scope: "row", class: "mono" }, p.label), h("td", null, p.owner), status));
    p.run(ctx.store.source).then(
      () =>
        mount(
          status,
          ctx.store.source.kind === "fixtures"
            ? h("span", { class: "badge fixture", title: "Served from contract fixtures, not the backend." }, "fixture only")
            : h("span", { class: "badge ok" }, "available"),
        ),
      (err) =>
        mount(status, isNotImplemented(err) ? h("span", { class: "badge planned" }, "501 planned") : h("span", { class: "badge err", title: err.message }, `error ${err.status || ""} ${err.code || ""}`.trim())),
    );
  }
  return root;
}
