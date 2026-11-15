import { environmentLabel, EVIDENCE_CLASSES, isFixture, VALUE_STATUS } from "../model/evidence.js";
import { groupFindingsByRow } from "../model/group.js";
import { EMPTY_FILTERS, facetOptions, filterInvestigations } from "../model/filter.js";
import {
  conditionsBlock,
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
  // Not a live region: the role=status count below announces changes; the list itself is not read aloud on every keystroke.
  const results = h("div", { class: "results" });
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
      select("evidenceClass", "Has evidence class", ["measured", "interpretation"], (k) => EVIDENCE_CLASSES[k].label),
      select("valueStatus", "Has value status", Object.keys(VALUE_STATUS), (k) => VALUE_STATUS[k].label),
      h("label", { class: "check" }, h("input", { type: "checkbox", name: "withValuesOnly", onchange: (e) => update("withValuesOnly", e.target.checked) }), h("span", null, "Only investigations reporting a value")),
      h("button", { type: "reset", class: "btn btn-ghost", onclick: () => setTimeout(() => { Object.assign(filters, EMPTY_FILTERS); draw(); }) }, "Clear filters"),
      h(
        "p",
        { class: "small muted note" },
        "Experimental conditions (oxygen fraction, pressure, flow, fuel) are shown on each finding. Condition filters will be added once real curated data shows which ones are populated.",
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

/**
 * Findings of one investigation. Large investigations (e.g. FLEX, ~40
 * findings) are grouped by test row (`locator`) with the row's conditions
 * shown once; small ones are listed flat.
 */
export function findingsSection(findings, findingsById) {
  const { grouped, groups, interpretations } = groupFindingsByRow(findings);
  const interp = interpretations.length ? [h("h4", { class: "subhead" }, `Interpretations (${interpretations.length})`), h("div", { class: "findings" }, interpretations.map((f) => findingCard(f, findingsById)))] : null;
  if (!grouped) return h("div", { class: "findings" }, groups[0].findings.map((f) => findingCard(f, findingsById)), interp);
  return h(
    "div",
    { class: "findings grouped" },
    h("p", { class: "small muted" }, `${groups.length} test rows${groups.every((g) => g.testId) ? " (grouped by the source's test identifier)" : ""}. Each row lists its own findings; conditions are shown once per row when every finding in it shares them.`),
    groups.map((g, i) => {
      const counts = {};
      for (const f of g.findings) counts[f.value_status] = (counts[f.value_status] || 0) + 1;
      return h(
        "details",
        { class: "row-group", open: i === 0 },
        h(
          "summary",
          null,
          h("span", { class: "row-label" }, g.label),
          g.testId ? h("span", { class: "chip test-outcome", title: "The label the source prints for this test. Not a FlameGuard-SI classification of what happened." }, `Test end as printed: ${g.outcomeConflict ? "CONFLICT" : g.outcome || "Not reported"}`) : null,
          g.outcomeConflict ? h("span", { class: "badge vs vs-excluded", role: "alert" }, "Findings of this test report different outcomes") : null,
          h("span", { class: "muted small" }, ` · ${g.findings.length} finding${g.findings.length === 1 ? "" : "s"}`),
          Object.entries(counts).map(([k, n]) => h("span", { class: `badge vs vs-${k}` }, `${n} ${(VALUE_STATUS[k] || { label: k }).label.toLowerCase()}`)),
        ),
        g.sharedConditions ? h("div", { class: "row-conditions" }, h("p", { class: "small" }, h("strong", null, "Conditions for this row")), conditionsBlock(g.sharedConditions)) : null,
        h("div", { class: "findings" }, g.findings.map((f) => findingCard(f, findingsById, { hideConditions: Boolean(g.sharedConditions), hideTestIdentity: Boolean(g.testId) && !g.outcomeConflict }))),
      );
    }),
    interp,
  );
}

function investigationCard(ctx, inv, ev) {
  const findings = ev.findingsByInvestigation.get(inv.id) || [];
  const selected = ctx.store.selection.has(inv.id);
  const checkboxId = `cmp-${inv.id}`;
  const classes = [...new Set(findings.map((f) => f.evidence_class))];

  let findingsBody;
  if (ev.findings.state !== "ready") findingsBody = resourcePanel(ev.findings, "Findings", "GET /api/findings");
  else if (findings.length === 0) findingsBody = statePanel({ kind: "empty", title: "No findings recorded for this investigation" });
  else findingsBody = findingsSection(findings, ev.findingsById);

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
          h("span", null, "Compare", h("span", { class: "sr-only" }, ` ${inv.name}`)),
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
