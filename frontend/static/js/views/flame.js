// Flame Lab: a standalone, ILLUSTRATIVE interactive flame. The view owns the controls, the honest
// wording and the fallbacks; the WebGL scene (flame/flame-scene.js) is loaded lazily and only
// draws what flame/params.js maps from the inputs. No measurement, prediction or score is shown.

import { ASSUMPTIONS, CONTROL_NOTE, DEFAULTS, DISCLAIMER, FUELS, GRAVITY_PRESETS, LIMITS, describe, evidenceCta, prefersReducedMotion, presetForGravity, sanitize, sceneMode, webglAvailable } from "../flame/params.js";
import { h, mount } from "../ui/dom.js";

export const title = "Flame Lab";

/** @param {import("../main.js").ViewContext} ctx */
export function render(ctx) {
  let inputs = sanitize(DEFAULTS);
  let scene = null;
  let reduced = prefersReducedMotion();
  let disposed = false;

  const stage = h("div", { class: "flame-stage", tabindex: "0", "aria-label": "Interactive illustrative flame. Arrow keys orbit, plus and minus zoom, R resets the view, I or Space toggles ignition, 1 to 4 choose gravity." });
  const status = h("p", { class: "flame-status small", role: "status", "aria-live": "polite" }, "Loading the 3D flame…");
  const stamp = h("p", { class: "flame-stamp", "aria-hidden": "true" }, DISCLAIMER);
  /** Share of the stage height the disclaimer stamp covers, so the scene keeps the flame below it. */
  const topReserve = () => {
    const box = stage.getBoundingClientRect();
    return box.height > 0 ? (stamp.getBoundingClientRect().bottom - box.top + 10) / box.height : 0.1;
  };
  const explain = h("ul", { class: "flame-explain", "aria-live": "polite" });
  const cta = h("div", { class: "flame-evidence" });

  const gravityValue = h("output", { class: "flame-value", for: "flame-gravity" });
  const oxygenValue = h("output", { class: "flame-value", for: "flame-oxygen" });
  const airflowValue = h("output", { class: "flame-value", for: "flame-airflow" });
  const igniteBtn = h("button", { type: "button", class: "btn btn-primary flame-ignite", "aria-pressed": "true", onclick: () => update({ ignited: !inputs.ignited }) });

  const range = (id, key, limits) =>
    h("input", {
      type: "range",
      id,
      min: limits.min,
      max: limits.max,
      step: limits.step,
      value: inputs[key],
      oninput: (e) => update({ [key]: Number(e.target.value) }),
    });
  const gravityRange = range("flame-gravity", "gravity", LIMITS.gravity);
  const oxygenRange = range("flame-oxygen", "oxygen", LIMITS.oxygen);
  const airflowRange = range("flame-airflow", "airflow", LIMITS.airflow);
  const presetButtons = GRAVITY_PRESETS.map((p) =>
    h(
      "button",
      { type: "button", class: "flame-preset", role: "radio", "aria-checked": "false", "aria-label": `${p.label}, ${p.gLabel}`, dataset: { preset: p.id }, onclick: () => update({ gravity: p.g }) },
      h("span", { class: "flame-preset-name", "aria-hidden": "true" }, p.short),
      h("span", { class: "flame-preset-g", "aria-hidden": "true" }, p.gShort),
    ),
  );
  const fuelSelect = h(
    "select",
    { id: "flame-fuel", onchange: (e) => update({ fuel: e.target.value }) },
    FUELS.map((f) => h("option", { value: f.id }, f.label)),
  );
  const motionBtn = h("button", { type: "button", class: "btn btn-ghost", "aria-pressed": String(reduced), onclick: () => setReduced(!reduced) });

  function paint() {
    const preset = presetForGravity(inputs.gravity);
    igniteBtn.textContent = inputs.ignited ? "Extinguish" : "Ignite";
    igniteBtn.setAttribute("aria-pressed", String(inputs.ignited));
    igniteBtn.classList.toggle("is-lit", inputs.ignited);
    gravityRange.value = String(inputs.gravity);
    oxygenRange.value = String(inputs.oxygen);
    airflowRange.value = String(inputs.airflow);
    fuelSelect.value = inputs.fuel;
    gravityValue.textContent = preset ? `${preset.label} · ${preset.gLabel}` : `${inputs.gravity.toFixed(2)} g`;
    oxygenValue.textContent = `${inputs.oxygen}%`;
    airflowValue.textContent = inputs.airflow < 0.01 ? "Still" : inputs.airflow < 0.4 ? "Gentle" : inputs.airflow < 0.75 ? "Moderate" : "Strong";
    for (const b of presetButtons) b.setAttribute("aria-checked", String(Boolean(preset) && b.dataset.preset === preset.id));
    motionBtn.textContent = reduced ? "Resume motion" : "Pause motion";
    motionBtn.setAttribute("aria-pressed", String(reduced));
    mount(explain, describe(inputs).map((line) => h("li", { dataset: { control: line.control } }, line.text)));
  }

  function update(patch) {
    inputs = sanitize({ ...inputs, ...patch });
    paint();
    if (scene) scene.setInputs(inputs);
  }

  function setReduced(on) {
    reduced = on;
    if (scene) {
      scene.setReducedMotion(on);
      scene.setInputs(inputs);
    }
    paint();
  }

  function showFallback(reason) {
    stage.classList.add("is-fallback");
    stage.dataset.sceneState = "fallback";
    mount(
      stage,
      h(
        "div",
        { class: "flame-fallback", role: "img", "aria-label": "Still illustration of a flame. The 3D view is not available." },
        h("div", { class: "flame-fallback-art", "aria-hidden": "true" }),
        h("p", null, h("strong", null, "The 3D flame is not available here. "), reason),
        h("p", { class: "small muted" }, "The controls and explanations below still work. ", DISCLAIMER),
      ),
    );
    status.textContent = "3D view unavailable: showing a still illustration.";
  }

  async function start() {
    if (sceneMode() === "off") return showFallback("It was switched off for this page (scene=off).");
    if (!webglAvailable()) return showFallback("This browser or device does not provide WebGL.");
    try {
      const { createFlameScene } = await import("../flame/flame-scene.js");
      if (disposed) return;
      scene = await createFlameScene(stage, {
        inputs,
        reducedMotion: reduced,
        topReserve,
        label: `Illustrative 3D flame. ${DISCLAIMER}`,
        onAction: (action) => {
          if (action === "toggle-ignition") update({ ignited: !inputs.ignited });
          else if (action.startsWith("gravity:")) update({ gravity: GRAVITY_PRESETS.find((p) => p.id === action.slice(8)).g });
        },
      });
      if (disposed) {
        scene.dispose();
        scene = null;
        return;
      }
      stage.dataset.sceneState = "ready";
      stage.fgFlame = scene; // read by browser tests for frame and draw statistics
      status.textContent = reduced ? "Reduced motion: showing a still frame that updates when you change a control." : "Drag to orbit, scroll or pinch to zoom.";
    } catch (err) {
      showFallback(`It could not start (${err && err.message ? err.message : "unknown error"}).`);
    }
  }

  ctx.onLeave(() => {
    disposed = true;
    if (scene) scene.dispose();
    scene = null;
  });

  ctx.store.evidence().then((ev) => {
    if (disposed) return;
    const findings = ev.findings.state === "ready" ? ev.findings.data : [];
    const c = evidenceCta({
      source: ctx.store.source.kind,
      state: ev.findings.state === "ready" && ev.investigations.state === "ready" ? "ready" : ev.findings.state === "loading" ? "loading" : "error",
      measured: findings.filter((f) => f.evidence_class === "measured").length,
      investigations: ev.investigations.state === "ready" ? ev.investigations.data.length : 0,
    });
    mount(
      cta,
      h("p", { class: "flame-evidence-title" }, "Looking for real measurements?"),
      h("p", { class: "small muted" }, "The Flame Lab is a drawing. NASA combustion measurements, with their sources, cautions and exclusions, are in the Evidence Explorer."),
      h("div", { class: "row gap wrap" }, h("a", { class: "btn", href: "#/explorer" }, c.label), h("span", { class: "chip flame-evidence-status" }, c.status)),
    );
  });

  const root = h(
    "section",
    { class: "view flame-view" },
    h(
      "header",
      { class: "flame-head" },
      h("p", { class: "eyebrow" }, "Flame Lab · interactive illustration"),
      h("h1", { tabindex: "-1" }, "Explore how a flame responds"),
      h("p", { class: "lede" }, "Ignite an isolated flame and change gravity, oxygen, airflow and fuel. The picture follows the direction of each effect so you can build intuition before reading the evidence."),
    ),
    h("p", { class: "flame-disclaimer", role: "note" }, h("strong", null, DISCLAIMER), " ", ASSUMPTIONS),
    h(
      "div",
      { class: "flame-layout" },
      h("div", { class: "flame-stage-wrap" }, stage, stamp, status),
      h(
        "form",
        { class: "flame-controls card", "aria-label": "Flame Lab controls", onsubmit: (e) => e.preventDefault() },
        h("div", { class: "flame-control" }, h("span", { class: "sr-only" }, "Ignition"), igniteBtn),
        h(
          "div",
          { class: "flame-control" },
          h("label", { class: "flame-label", for: "flame-gravity" }, "Gravity", gravityValue),
          h("div", { class: "flame-presets", role: "radiogroup", "aria-label": "Gravity context" }, presetButtons),
          gravityRange,
        ),
        h(
          "div",
          { class: "flame-control" },
          h("label", { class: "flame-label", for: "flame-oxygen" }, "Oxygen", oxygenValue),
          oxygenRange,
        ),
        h(
          "div",
          { class: "flame-control" },
          h("label", { class: "flame-label", for: "flame-airflow" }, "Forced airflow", airflowValue),
          airflowRange,
        ),
        h(
          "div",
          { class: "flame-control" },
          h("label", { class: "flame-label", for: "flame-fuel" }, "Fuel look"),
          fuelSelect,
        ),
        h("p", { class: "flame-note", role: "note" }, CONTROL_NOTE),
        h(
          "div",
          { class: "row gap wrap flame-actions" },
          h("button", { type: "button", class: "btn btn-ghost", onclick: () => scene && scene.resetView() }, "Reset view"),
          motionBtn,
          h("button", { type: "button", class: "btn btn-ghost", onclick: () => update(DEFAULTS) }, "Reset controls"),
        ),
      ),
    ),
    h(
      "div",
      { class: "flame-below" },
      h("section", { class: "card", "aria-labelledby": "flame-explain-h" }, h("h2", { id: "flame-explain-h" }, "What you are seeing"), explain, h("p", { class: "small muted" }, "No temperature, burning rate, spread rate, extinction limit, risk or suppression value is calculated or shown.")),
      h("section", { class: "card", "aria-labelledby": "flame-evidence-h" }, h("h2", { id: "flame-evidence-h" }, "From illustration to evidence"), cta),
    ),
  );

  paint();
  queueMicrotask(start);
  return root;
}
