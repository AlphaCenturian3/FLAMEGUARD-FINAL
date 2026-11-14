import { environmentLabel, isFixture } from "../model/evidence.js";
import { reviewRankings } from "../model/ranking.js";
import { resourceFromError } from "../store.js";
import { evidenceBadge, fixtureBadge, resourcePanel, statePanel } from "../ui/components.js";
import { h, mount } from "../ui/dom.js";
import { contextSelect, getContext } from "./context.js";

export const title = "Ranking";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  const out = h("div", { "aria-live": "polite" });
  const root = h(
    "section",
    { class: "view" },
    h(
      "header",
      { class: "view-head" },
      h("h1", { tabindex: "-1" }, title),
      h("p", { class: "lede" }, "Rank investigations by relevance to a crewed environment. Scores come only from the FlameGuard-SI backend; this page never computes or estimates them."),
    ),
    h("div", { class: "card row gap wrap" }, contextSelect(() => load()), h("p", { class: "small muted grow" }, "The ranking is a relevance ordering of evidence, not a fire-risk score or a safety rating.")),
    h(
      "section",
      { class: "card", "aria-labelledby": "criteria-h" },
      h("h2", { id: "criteria-h" }, "Ranking criteria"),
      h("ul", null,
        h("li", null, "Criteria and weights are defined by the backend ranking module (spec §5.1, GET /api/rankings?context=)."),
        h("li", null, "Every ranked item must list the findings it relies on. Only ", evidenceBadge("measured"), " and ", evidenceBadge("interpretation"), " findings are accepted."),
        h("li", null, "Every supporting finding must resolve to a loaded record and trace back to measured evidence. Items with unresolved findings, broken provenance, or an ", evidenceBadge("illustrative_simulation"), " anywhere in the chain (directly or through an interpretation) are withheld and listed below."),
        h("li", null, "Items without a rationale or with a non-numeric score are also withheld."),
      ),
      h("div", { id: "criteria-detail" }),
    ),
    out,
  );

  async function load() {
    const context = getContext();
    mount(out, statePanel({ kind: "loading", title: `Requesting ranking for ${environmentLabel(context)}…` }));
    const ev = await ctx.store.evidence();
    let resource;
    try {
      resource = { state: "ready", data: await ctx.store.source.getRankings(context) };
    } catch (err) {
      resource = resourceFromError(err);
    }
    if (getContext() !== context) return; // a newer request superseded this one
    const criteria = root.querySelector("#criteria-detail");
    if (resource.state !== "ready") {
      mount(criteria);
      mount(out, resourcePanel(resource, "Rankings", `GET /api/rankings?context=${context}`));
      return;
    }
    const data = resource.data;
    // Optional: show backend-supplied criteria verbatim if the response includes them.
    mount(criteria, Array.isArray(data.criteria) && data.criteria.length ? [h("h3", null, "Criteria reported by the backend"), h("ul", null, data.criteria.map((c) => h("li", null, typeof c === "string" ? c : JSON.stringify(c))))] : null);

    const { accepted, rejected } = reviewRankings(data, ev.findingsById);
    const invName = (id) => (ev.investigations.state === "ready" ? ev.investigations.data.find((i) => i.id === id)?.name : null) || id;
    mount(
      out,
      accepted.length === 0 ? statePanel({ kind: "empty", title: `No ranked investigations for ${environmentLabel(context)}` }) : null,
      accepted.length
        ? h(
            "ol",
            { class: "ranking" },
            accepted.map(({ item, inputs }, i) =>
              h(
                "li",
                { class: "card rank-item" },
                h("div", { class: "rank-pos", "aria-hidden": "true" }, String(i + 1)),
                h(
                  "div",
                  { class: "grow" },
                  h("h3", null, invName(item.investigation_id)),
                  h("p", null, h("span", { class: "muted" }, "Backend score: "), h("strong", { class: "mono" }, String(item.score)), h("span", { class: "muted small" }, " (relative ordering, not a risk value)")),
                  h("p", null, h("span", { class: "muted" }, "Rationale (FlameGuard-SI): "), item.rationale),
                  h("p", { class: "small" }, "Supporting findings: ", inputs.map((f) => h("span", { class: "chip" }, evidenceBadge(f.evidence_class), " ", f.id, isFixture(f) ? [" ", fixtureBadge()] : null))),
                ),
              ),
            ),
          )
        : null,
      rejected.length
        ? h(
            "section",
            { class: "card alert-warn" },
            h("h3", null, `Withheld items (${rejected.length})`),
            h("ul", null, rejected.map(({ item, problems }) => h("li", null, h("strong", null, item?.investigation_id || "unknown"), ": ", problems.join(" ")))),
          )
        : null,
    );
  }

  load();
  return root;
}
