import { availableQuantities, reviewComparison } from "../model/compare.js";
import { CONDITIONS, isFixture, isMissing, valueStatusInfo } from "../model/evidence.js";
import { resourceFromError } from "../store.js";
import { barChart } from "../ui/chart.js";
import { fixtureBadge, investigationMeta, resourcePanel, statePanel, valueStatusBadge } from "../ui/components.js";
import { h, mount } from "../ui/dom.js";

export const title = "Experiment Comparison";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  const controls = h("form", { class: "card compare-controls", onsubmit: (e) => e.preventDefault() });
  const result = h("div", { class: "compare-body", "aria-live": "polite" });
  const root = h(
    "section",
    { class: "view" },
    h(
      "header",
      { class: "view-head" },
      h("h1", { tabindex: "-1" }, title),
      h("p", { class: "lede" }, "Measured values for one quantity across investigations. Whether they are comparable is decided by the FlameGuard-SI backend; this page shows that decision and its reasons exactly as returned."),
    ),
    controls,
    result,
  );
  mount(result, statePanel({ kind: "loading", title: "Loading evidence…" }));

  ctx.store.evidence().then((ev) => {
    if (ev.investigations.state !== "ready" || ev.findings.state !== "ready") {
      mount(result, resourcePanel(ev.investigations.state !== "ready" ? ev.investigations : ev.findings, "Evidence", "GET /api/investigations, /api/findings"));
      return;
    }
    const all = ev.investigations.data;
    const quantities = availableQuantities(ev.findings.data);
    if (!quantities.length) {
      mount(controls, h("p", { class: "muted" }, "No measured finding names a quantity, so there is nothing to compare."));
      mount(result);
      return;
    }
    const qSelect = h("select", { id: "cmp-quantity", name: "quantity" }, quantities.map((q) => h("option", { value: q.quantity }, `${q.quantity.replaceAll("_", " ")} (${q.unit})`)));
    const run = h("button", { type: "submit", class: "btn btn-primary" }, "Request comparison");

    const drawControls = () =>
      mount(
        controls,
        h("label", { class: "field", for: "cmp-quantity" }, h("span", null, "Quantity"), qSelect),
        h(
          "fieldset",
          { class: "picker" },
          h("legend", null, "Limit to investigations (optional)"),
          h(
            "div",
            { class: "picker-list" },
            all.map((inv) =>
              h("label", { class: "check" }, h("input", { type: "checkbox", checked: ctx.store.selection.has(inv.id), onchange: () => ctx.store.selection.toggle(inv.id) }), h("span", null, inv.name), isFixture(inv) ? fixtureBadge() : null),
            ),
          ),
          h("p", { class: "small muted" }, "With none selected, the backend compares every investigation that reports the quantity."),
        ),
        h("div", { class: "row gap" }, run),
      );
    drawControls();
    ctx.onLeave(ctx.store.onSelectionChange(drawControls));

    async function request() {
      const quantity = qSelect.value;
      const ids = all.filter((i) => ctx.store.selection.has(i.id)).map((i) => i.id);
      mount(result, statePanel({ kind: "loading", title: `Requesting comparison for ${quantity}…` }));
      try {
        const resp = await ctx.store.source.compare(quantity, ids);
        mount(result, comparisonView(resp, ev, all));
      } catch (err) {
        mount(result, resourcePanel(resourceFromError(err), "Comparison", `GET /api/compare?quantity=${quantity}`));
      }
    }
    controls.addEventListener("submit", request);
    mount(result, statePanel({ kind: "empty", title: "Choose a quantity and request a comparison" }));
  });

  return root;
}

function comparisonView(resp, ev, investigations) {
  const { chartable, problems } = reviewComparison(resp, ev.findingsById);
  const invName = (id) => investigations.find((i) => i.id === id)?.name || id;
  const rows = resp.rows || [];

  const decision = h(
    "section",
    { class: "card", "aria-labelledby": "decision-h" },
    h("h2", { id: "decision-h" }, "Backend decision ", resp.fixture ? fixtureBadge() : null),
    h("p", null, h("strong", null, resp.comparable ? "Comparable" : "Not comparable"), ` · ${resp.quantity} (${resp.unit})`),
    (resp.non_comparable_reasons || []).length
      ? h("div", null, h("p", { class: "small" }, "Reasons given by the backend:"), h("ul", { class: "reasons-list" }, resp.non_comparable_reasons.map((r) => h("li", null, r))))
      : null,
    problems.length ? h("div", { class: "alert alert-warn", role: "status" }, h("strong", null, "Withheld by dashboard check: "), "the response is inconsistent with the contract, so no chart is drawn.", h("ul", null, problems.map((p) => h("li", null, p)))) : null,
  );

  const chart = chartable
    ? h(
        "section",
        { class: "card" },
        h("h2", null, "Chart"),
        barChart(
          rows.map((r) => ({ label: invName(r.investigation_id), value: r.value, note: `finding ${r.finding_id}`, fixture: Boolean(resp.fixture) })),
          { unit: resp.unit, title: resp.quantity },
        ),
      )
    : h("p", { class: "small muted" }, "No chart: values are charted only when the backend marks them comparable. Missing and excluded values are never plotted.");

  const table = h(
    "section",
    { class: "card" },
    h("h2", null, "Rows as returned"),
    h(
      "div",
      { class: "table-wrap", tabindex: "0", role: "region", "aria-label": "Comparison rows" },
      h(
        "table",
        { class: "compare-table" },
        h("thead", null, h("tr", null, h("th", { scope: "col" }, "Investigation"), h("th", { scope: "col" }, "Value"), CONDITIONS.map(([, label, unit]) => h("th", { scope: "col" }, unit ? `${label} (${unit})` : label)))),
        h(
          "tbody",
          null,
          rows.map((r) =>
            h(
              "tr",
              null,
              h("th", { scope: "row" }, invName(r.investigation_id), h("div", { class: "mono small muted" }, r.finding_id)),
              h("td", null, r.value_status === "reported" && r.value !== null ? `${r.value} ${resp.unit}` : valueStatusBadge(r.value_status), r.value_status !== "reported" ? h("div", { class: "small muted" }, valueStatusInfo(r.value_status).description) : null),
              CONDITIONS.map(([key]) => h("td", null, isMissing(r.conditions?.[key]) ? h("span", { class: "missing-value" }, "Not reported") : String(r.conditions[key]).replaceAll("_", " "))),
            ),
          ),
        ),
      ),
    ),
  );

  const selected = investigations.filter((i) => rows.some((r) => r.investigation_id === i.id));
  const meta = selected.length
    ? h("section", { class: "card" }, h("h2", null, "Investigations in this comparison"), h("div", { class: "compare-grid" }, selected.map((i) => h("div", null, h("h3", null, i.name), investigationMeta(i)))))
    : null;

  return [decision, chart, table, meta];
}
