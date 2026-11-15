// Simulation panel (GET /api/simulations/{id}). Isolated: rankings,
// interpretations, and the assistant never import this module (spec §2.3).
// The required label is always shown, and results with a different label
// are refused.

import { isNotImplemented } from "../api/errors.js";
import { SIMULATION_LABEL, isFixture } from "../model/evidence.js";
import { evidenceBadge, fixtureBadge, simulationLabel, statePanel } from "../ui/components.js";
import { h, mount } from "../ui/dom.js";

/** @returns {string[]} problems */
export function reviewSimulation(sim) {
  const problems = [];
  if (!sim || sim.evidence_class !== "illustrative_simulation") problems.push("evidence_class must be illustrative_simulation.");
  if (!sim || sim.label !== SIMULATION_LABEL) problems.push("Required simulation label is missing or altered.");
  if (!sim || !sim.model || !sim.model_version) problems.push("Model name and version are required.");
  return problems;
}

/** @param {import("../api/types.js").DataSource} source */
export function renderSimulationPanel(source, id = "fixture-sim-1") {
  const out = h("div", { "aria-live": "polite" }, statePanel({ kind: "loading", title: "Loading simulation…" }));
  source.getSimulation(id).then(
    (sim) => {
      const problems = reviewSimulation(sim);
      if (problems.length) {
        mount(out, statePanel({ kind: "error", title: "Simulation withheld", message: problems.join(" ") }));
        return;
      }
      const params = Object.entries(sim.parameters || {});
      const outputs = Object.entries(sim.outputs || {});
      mount(
        out,
        h("div", { class: "row gap wrap" }, evidenceBadge("illustrative_simulation"), isFixture(sim) ? fixtureBadge() : null),
        h("dl", { class: "kv" }, h("dt", null, "Model"), h("dd", { class: "mono" }, `${sim.model} ${sim.model_version}`), h("dt", null, "Verification"), h("dd", null, sim.verification_status || "not stated")),
        h("p", { class: "small" }, params.length ? `${params.length} parameter(s), ${outputs.length} output(s).` : h("span", { class: "missing-value" }, "No parameters or outputs in this result.")),
      );
    },
    (err) =>
      mount(
        out,
        isNotImplemented(err)
          ? statePanel({ kind: "not_implemented", title: "Simulations not implemented yet", message: `GET /api/simulations/${id} returned HTTP 501.` })
          : statePanel({ kind: "error", title: "Could not load simulation", message: err.message }),
      ),
  );

  return h(
    "section",
    { class: "card sim-panel", "aria-labelledby": "sim-h" },
    h("h2", { id: "sim-h" }, "Illustrative simulation ", h("span", { class: "badge planned" }, "integration point")),
    simulationLabel(),
    h("p", { class: "small muted" }, "Simulation output is never experimental data and never feeds rankings, interpretations, or the assistant."),
    out,
  );
}
