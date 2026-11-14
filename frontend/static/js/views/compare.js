import { buildComparison } from "../model/compare.js";
import { evidenceInfo, formatValue, isFixture } from "../model/evidence.js";
import { evidenceBadge, findingCard, fixtureBadge, investigationMeta, resourcePanel, sourceList, statePanel } from "../ui/components.js";
import { h, mount } from "../ui/dom.js";
import { barChart } from "../ui/chart.js";

export const title = "Experiment Comparison";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  const picker = h("fieldset", { class: "card picker" }, h("legend", null, "Investigations to compare"));
  const body = h("div", { class: "compare-body", "aria-live": "polite" });
  const root = h(
    "section",
    { class: "view" },
    h(
      "header",
      { class: "view-head" },
      h("h1", { tabindex: "-1" }, title),
      h("p", { class: "lede" }, "Side-by-side evidence for selected investigations. Values are charted only when FlameGuard-SI can confirm they measure the same quantity in the same unit."),
    ),
    picker,
    body,
  );
  mount(body, statePanel({ kind: "loading", title: "Loading evidence…" }));

  ctx.store.evidence().then((ev) => {
    if (ev.investigations.state !== "ready") {
      mount(picker, h("legend", null, "Investigations to compare"));
      mount(body, resourcePanel(ev.investigations, "Investigations", "GET /api/investigations"));
      return;
    }
    const all = ev.investigations.data;
    if (all.length === 0) {
      mount(body, statePanel({ kind: "empty", title: "No investigations available to compare" }));
      return;
    }

    const drawPicker = () =>
      mount(
        picker,
        h("legend", null, "Investigations to compare"),
        h(
          "div",
          { class: "picker-list" },
          all.map((inv) =>
            h(
              "label",
              { class: "check" },
              h("input", { type: "checkbox", checked: ctx.store.selection.has(inv.id), onchange: () => ctx.store.selection.toggle(inv.id) }),
              h("span", null, inv.name),
              isFixture(inv) ? fixtureBadge() : null,
            ),
          ),
        ),
        h(
          "div",
          { class: "row gap" },
          h("button", { type: "button", class: "btn btn-ghost", onclick: () => ctx.store.selection.set(all.map((i) => i.id)) }, "Select all"),
          h("button", { type: "button", class: "btn btn-ghost", onclick: () => ctx.store.selection.set([]) }, "Clear"),
        ),
      );

    const draw = () => {
      drawPicker();
      const selected = all.filter((i) => ctx.store.selection.has(i.id));
      const model = buildComparison(selected, ev.findingsByInvestigation);
      mount(body, comparisonView(model, ev));
    };
    const unsubscribe = ctx.store.onSelectionChange(draw);
    ctx.onLeave(unsubscribe);
    draw();
  });

  return root;
}

function comparisonView(model, ev) {
  if (model.columns.length === 0) {
    return statePanel({ kind: "empty", title: "Nothing selected", message: "Choose investigations above, or tick “Compare” on cards in the Evidence Explorer." });
  }

  const charts = h(
    "section",
    { class: "card", "aria-labelledby": "charts-h" },
    h("h2", { id: "charts-h" }, "Quantitative comparison"),
    model.message ? h("div", { class: "alert alert-info", role: "status" }, model.message) : null,
    model.groups.map((g) =>
      h(
        "div",
        { class: "chart-group" },
        h("h3", null, g.quantity),
        g.compatible
          ? barChart(
              g.findings.map((f) => ({
                label: (model.columns.find((c) => c.investigation.id === f.investigation_id) || {}).investigation?.name || f.investigation_id,
                value: /** @type {number} */ (f.value),
                note: f.uncertainty ? `uncertainty as reported: ${f.uncertainty}` : "uncertainty not reported",
                fixture: isFixture(f),
              })),
              { unit: g.findings[0].unit, title: g.quantity },
            )
          : h("div", { class: "alert alert-warn" }, h("strong", null, "Not charted. "), h("ul", null, g.reasons.map((r) => h("li", null, r)))),
      ),
    ),
  );

  const cols = model.columns;
  const row = (label, cell) => h("tr", null, h("th", { scope: "row" }, label), cols.map((c) => h("td", null, cell(c))));
  const table = h(
    "div",
    { class: "table-wrap", tabindex: "0", role: "region", "aria-label": "Side-by-side evidence table" },
    h(
      "table",
      { class: "compare-table" },
      h("caption", { class: "sr-only" }, "Selected investigations side by side"),
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Field"), cols.map((c) => h("th", { scope: "col" }, c.investigation.name, isFixture(c.investigation) ? [" ", fixtureBadge()] : null)))),
      h(
        "tbody",
        null,
        row("Metadata", (c) => investigationMeta(c.investigation)),
        row("Findings by class", (c) =>
          h(
            "ul",
            { class: "plain" },
            Object.entries(c.counts).map(([k, n]) => h("li", null, evidenceBadge(k), ` ${n}`)),
          ),
        ),
        row("Reported values", (c) =>
          ev.findings.state !== "ready"
            ? resourcePanel(ev.findings, "Findings", "GET /api/findings")
            : c.findings.length
              ? h(
                  "ul",
                  { class: "plain values" },
                  c.findings.map((f) =>
                    h("li", null, h("span", { class: "sr-only" }, `${evidenceInfo(f.evidence_class).label}: `), evidenceBadge(f.evidence_class), " ", formatValue(f) ?? h("span", { class: "missing-value" }, "value not reported"), h("span", { class: "muted small" }, ` — ${f.id}`)),
                  ),
                )
              : h("span", { class: "missing-value" }, "No findings"),
        ),
        row("Sources", (c) => sourceList(c.investigation.sources)),
      ),
    ),
  );

  const details = h(
    "section",
    { class: "card" },
    h("h2", null, "Finding detail"),
    h("div", { class: "compare-grid", style: `--cols:${cols.length}` }, cols.map((c) => h("div", null, h("h3", null, c.investigation.name), c.findings.length ? c.findings.map((f) => findingCard(f, ev.findingsById)) : h("p", { class: "missing-value" }, "No findings")))),
  );

  return [charts, h("section", { class: "card" }, h("h2", null, "Side-by-side evidence"), table), details];
}
