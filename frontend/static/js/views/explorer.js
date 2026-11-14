import { environmentLabel, EVIDENCE_CLASSES, isFixture } from "../model/evidence.js";
import { EMPTY_FILTERS, facetOptions, filterInvestigations } from "../model/filter.js";
import {
  evidenceBadge,
  findingCard,
  fixtureBadge,
  investigationMeta,
  missingInvestigationFields,
  missingList,
  resourcePanel,
  sourceList,
  statePanel,
} from "../ui/components.js";
import { h, mount } from "../ui/dom.js";

export const title = "Evidence Explorer";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  const results = h("div", { class: "results", "aria-live": "polite" });
  const count = h("p", { class: "result-count muted", role: "status" });
  const filters = { ...EMPTY_FILTERS, query: ctx.params.get("q") || "" };

  const root = h(
    "section",
    { class: "view" },
    h(
      "header",
      { class: "view-head" },
      h("h1", { tabindex: "-1" }, title),
      h("p", { class: "lede" }, "Search NASA microgravity combustion investigations and inspect each finding with its evidence class, reported uncertainty, missing fields, and sources."),
    ),
    h("div", { class: "explorer" }, h("form", { class: "filters card", role: "search", "aria-label": "Filter investigations", onsubmit: (e) => e.preventDefault() }, statePanel({ kind: "loading", title: "Loading filters…" })), h("div", null, count, results)),
  );
  const form = root.querySelector("form.filters");
  mount(results, statePanel({ kind: "loading", title: "Loading investigations…" }));

  ctx.store.evidence().then((ev) => {
    if (ev.investigations.state !== "ready") {
      mount(form, h("p", { class: "muted" }, "Filters unavailable."));
      mount(results, resourcePanel(ev.investigations, "Investigations", "GET /api/investigations"));
      return;
    }
    const all = ev.investigations.data;
    const facets = facetOptions(all);

    const select = (name, label, options, renderLabel = (x) => x) =>
      h(
        "label",
        { class: "field" },
        h("span", null, label),
        h(
          "select",
          { name, onchange: (e) => update(name, e.target.value) },
          h("option", { value: "" }, "Any"),
          options.map((o) => h("option", { value: o }, renderLabel(o))),
        ),
      );

    mount(
      form,
      h("label", { class: "field" }, h("span", null, "Search"), h("input", { type: "search", name: "query", value: filters.query, placeholder: "Name, objective, statement…", oninput: (e) => update("query", e.target.value) })),
      select("platform", "Platform", facets.platforms),
      select("environment", "Relevant environment", facets.environments, environmentLabel),
      select("evidenceClass", "Has evidence class", Object.keys(EVIDENCE_CLASSES), (k) => EVIDENCE_CLASSES[k].label),
      h("label", { class: "check" }, h("input", { type: "checkbox", name: "withValuesOnly", onchange: (e) => update("withValuesOnly", e.target.checked) }), h("span", null, "Only investigations reporting a value")),
      h("button", { type: "reset", class: "btn btn-ghost", onclick: () => setTimeout(() => { Object.assign(filters, EMPTY_FILTERS); draw(); }) }, "Clear filters"),
      h(
        "p",
        { class: "small muted note" },
        "Contract v0.1.0 has no structured experimental parameters (oxygen fraction, pressure, flow speed, fuel). Parameter filters will be added when the contract defines them.",
      ),
    );

    function update(key, value) {
      filters[key] = value;
      draw();
    }

    function draw() {
      const shown = filterInvestigations(all, filters, ev.findingsByInvestigation);
      count.textContent = `${shown.length} of ${all.length} investigation${all.length === 1 ? "" : "s"}`;
      if (all.length === 0) {
        mount(results, statePanel({ kind: "empty", title: "No investigations available", message: "The data source returned no investigations. No records are invented to fill the gap." }));
        return;
      }
      if (shown.length === 0) {
        mount(results, statePanel({ kind: "empty", title: "No investigations match these filters", message: "Try clearing a filter." }));
        return;
      }
      mount(results, shown.map((inv) => investigationCard(ctx, inv, ev)));
    }
    draw();
  });

  return root;
}

function investigationCard(ctx, inv, ev) {
  const findings = ev.findingsByInvestigation.get(inv.id) || [];
  const selected = ctx.store.selection.has(inv.id);
  const checkboxId = `cmp-${inv.id}`;
  const classes = [...new Set(findings.map((f) => f.evidence_class))];

  let findingsBody;
  if (ev.findings.state !== "ready") findingsBody = resourcePanel(ev.findings, "Findings", "GET /api/findings");
  else if (findings.length === 0) findingsBody = statePanel({ kind: "empty", title: "No findings recorded for this investigation" });
  else findingsBody = h("div", { class: "findings" }, findings.map((f) => findingCard(f, ev.findingsById)));

  return h(
    "article",
    { class: `card investigation ${isFixture(inv) ? "is-fixture" : ""}`, "aria-labelledby": `inv-${inv.id}` },
    h(
      "header",
      { class: "inv-head" },
      h("div", null, h("h2", { id: `inv-${inv.id}` }, inv.name, inv.acronym ? h("span", { class: "muted" }, ` (${inv.acronym})`) : null), h("p", { class: "mono small muted" }, inv.id)),
      h(
        "div",
        { class: "inv-tags" },
        isFixture(inv) ? fixtureBadge() : null,
        classes.map((c) => evidenceBadge(c)),
        h(
          "label",
          { class: "check compare-toggle", for: checkboxId },
          h("input", {
            type: "checkbox",
            id: checkboxId,
            checked: selected,
            onchange: () => ctx.store.selection.toggle(inv.id),
          }),
          h("span", null, "Compare"),
        ),
      ),
    ),
    investigationMeta(inv),
    missingList(missingInvestigationFields(inv), "Not reported in record"),
    h("details", { class: "prov-details" }, h("summary", null, `Investigation sources (${(inv.sources || []).length})`), sourceList(inv.sources)),
    h("h3", { class: "subhead" }, `Findings (${findings.length})`),
    findingsBody,
  );
}
