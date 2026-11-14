import { CONTRACT_VERSION } from "../config.js";
import { EVIDENCE_CLASSES, isFixture, VALUE_STATUS } from "../model/evidence.js";
import { evidenceBadge, fixtureBadge, resourcePanel, sourceList, statePanel, valueStatusBadge } from "../ui/components.js";
import { h, mount } from "../ui/dom.js";

export const title = "Overview";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  const stats = h("div", { class: "stats", "aria-live": "polite" }, statePanel({ kind: "loading", title: "Loading evidence summary…" }));
  const sources = h("div", null);

  const root = h(
    "section",
    { class: "view" },
    h(
      "header",
      { class: "hero" },
      h("p", { class: "eyebrow" }, "NASA Space Apps 2026 · Flame in Freefall"),
      h("h1", { tabindex: "-1" }, "Fire-safety insight from microgravity combustion evidence"),
      h(
        "p",
        { class: "lede" },
        "FlameGuard-SI helps researchers and engineers discover, compare, rank, and interpret NASA microgravity combustion investigations for spacecraft, stations, lunar and Martian bases, and pressurized rovers. Every value shows where it came from.",
      ),
      h(
        "div",
        { class: "row gap wrap" },
        h("a", { class: "btn btn-primary", href: "#/explorer" }, "Explore evidence"),
        h("a", { class: "btn", href: "#/compare" }, "Compare investigations"),
        h("button", { type: "button", class: "btn btn-ghost", onclick: () => ctx.demo.start() }, "Start 90-second demo"),
      ),
    ),
    h("section", { "aria-labelledby": "status-h" }, h("h2", { id: "status-h" }, "What is loaded right now"), stats),
    h(
      "section",
      { class: "card", "aria-labelledby": "classes-h" },
      h("h2", { id: "classes-h" }, "How to read evidence"),
      h(
        "dl",
        { class: "legend" },
        Object.entries(EVIDENCE_CLASSES).filter(([k]) => k !== "illustrative_simulation").map(([k, v]) => [h("dt", null, evidenceBadge(k)), h("dd", null, v.description)]),
        h("dt", null, fixtureBadge()),
        h("dd", null, "Contract example with invented placeholder content, used while the backend is built. Never NASA data."),
        Object.entries(VALUE_STATUS).map(([k, v]) => [h("dt", null, valueStatusBadge(k)), h("dd", null, v.description)]),
        h("dt", null, h("span", { class: "badge" }, "FlameGuard-SI caution / exclusion")),
        h("dd", null, "A FlameGuard-SI quality assessment of a measured value, linked to a reviewed quality flag and a recorded NASA quote. Never source text, never shown as source-reported uncertainty."),
      ),
    ),
    h("section", { class: "card", "aria-labelledby": "prov-h" }, h("h2", { id: "prov-h" }, "Sources cited by loaded records"), sources),
    h(
      "section",
      { class: "card", "aria-labelledby": "where-h" },
      h("h2", { id: "where-h" }, "Where the evidence will come from"),
      h(
        "p",
        null,
        "Measured records are curated by the FlameGuard-SI data workstream from NASA archives such as the ",
        h("a", { href: "https://psi.nasa.gov/", target: "_blank", rel: "noopener noreferrer" }, "Physical Sciences Informatics (PSI) system"),
        " and the ",
        h("a", { href: "https://ntrs.nasa.gov/", target: "_blank", rel: "noopener noreferrer" }, "NASA Technical Reports Server (NTRS)"),
        ". Each measured record must be registered in the data manifest with a checksum and rights status before it appears here. These links are navigation aids, not evidence.",
      ),
    ),
  );

  ctx.store.evidence().then((ev) => {
    if (ev.investigations.state !== "ready") {
      mount(stats, resourcePanel(ev.investigations, "Investigations", "GET /api/investigations"));
      mount(sources, h("p", { class: "muted" }, "No records loaded."));
      return;
    }
    const invs = ev.investigations.data;
    const findings = ev.findings.state === "ready" ? ev.findings.data : [];
    const fixtures = [...invs, ...findings].filter(isFixture).length;
    const byClass = (k) => findings.filter((f) => f.evidence_class === k).length;
    const tile = (label, value, extra) => h("div", { class: "stat card" }, h("p", { class: "stat-value" }, String(value)), h("p", { class: "stat-label" }, label), extra || null);

    mount(
      stats,
      tile("Investigations loaded", invs.length),
      tile("Measured findings", byClass("measured"), evidenceBadge("measured")),
      tile("Interpretations", byClass("interpretation"), evidenceBadge("interpretation")),
      tile("Values excluded by FlameGuard-SI", findings.filter((f) => f.value_status === "excluded").length, valueStatusBadge("excluded")),
      tile("Contract version", CONTRACT_VERSION),
      fixtures
        ? h("p", { class: "alert alert-fixture grow-all", role: "note" }, `${fixtures} of these records are contract fixtures with placeholder content. They demonstrate the interface only and are not NASA data.`)
        : null,
      ev.findings.state !== "ready" ? resourcePanel(ev.findings, "Findings", "GET /api/findings") : null,
    );

    const all = [];
    const seen = new Set();
    for (const s of [...invs.flatMap((i) => i.sources || []), ...findings.flatMap((f) => f.provenance?.sources || [])]) {
      const key = `${s.title}|${s.url}`;
      if (!seen.has(key)) {
        seen.add(key);
        all.push(s);
      }
    }
    mount(sources, sourceList(all, "No sources cited by loaded records."));
  });

  return root;
}
