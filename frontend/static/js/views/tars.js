import { MODES, renderAssistantPanel } from "../integrations/assistant.js";
import { h } from "../ui/dom.js";

export const title = "TARS assistant";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  return h(
    "section",
    { class: "view" },
    h(
      "header",
      { class: "view-head" },
      h("h1", { tabindex: "-1" }, title),
      h("p", { class: "lede" }, "A source-grounded research assistant. It cites evidence, states uncertainty, and never presents FlameGuard-SI interpretations as NASA conclusions."),
    ),
    renderAssistantPanel(ctx.store),
    h(
      "section",
      { class: "card", "aria-labelledby": "modes-h" },
      h("h2", { id: "modes-h" }, "Answer modes"),
      h("dl", { class: "legend" }, Object.values(MODES).map((m) => [h("dt", null, m.label), h("dd", null, m.description)])),
    ),
  );
}
