// Flame Lab parameter model: pure functions, no DOM, no WebGL (tested in tests/flame.test.js).
//
// SCIENTIFIC RULE FOR EVERYTHING HERE: the Flame Lab is an ILLUSTRATION. The controls are inputs
// the viewer chooses. The response is an artistic mapping that follows only the well-known
// DIRECTION of each effect (less gravity, less buoyant stretching; more oxygen, a more vigorous
// flame; airflow leans and stretches a flame; sootier fuels glow yellower). No magnitude drawn
// here is computed, measured or validated, and the model outputs no temperature, burning rate,
// spread rate, extinction limit, probability, risk or suppression score. Real measurements live in
// the Evidence Explorer, with their sources.

export const DISCLAIMER = "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data.";

export const ASSUMPTIONS =
  "Every response to a control is an artistic drawing of the direction of an effect, not a calculation. No chemistry, heat transfer or fluid flow is solved, and nothing shown is a prediction.";

/** Gravity presets: standard reference values, as a fraction of Earth gravity. */
export const GRAVITY_PRESETS = Object.freeze([
  { id: "microgravity", label: "Microgravity", gLabel: "about 0 g", g: 0 },
  { id: "moon", label: "Moon", gLabel: "about 0.165 g", g: 0.165 },
  { id: "mars", label: "Mars", gLabel: "about 0.38 g", g: 0.38 },
  { id: "earth", label: "Earth", gLabel: "1 g", g: 1 },
]);

/** Generic fuel looks. Deliberately not named after real fuels: no real fuel's behaviour is claimed. */
export const FUELS = Object.freeze([
  { id: "low-soot-liquid", label: "Liquid droplet, low soot", shape: "droplet", soot: 0.12 },
  { id: "sooty-liquid", label: "Liquid droplet, sooty", shape: "droplet", soot: 0.85 },
  { id: "solid-sample", label: "Solid sample", shape: "solid", soot: 0.6 },
]);

export const LIMITS = Object.freeze({
  gravity: { min: 0, max: 1, step: 0.005 },
  oxygen: { min: 15, max: 40, step: 1 }, // percent of the surrounding gas: an INPUT, not a result
  airflow: { min: 0, max: 1, step: 0.01 }, // relative: 0 still, 1 strong
});

export const DEFAULTS = Object.freeze({ ignited: true, gravity: 0, oxygen: 21, airflow: 0, fuel: "low-soot-liquid" });

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const num = (v, fallback) => (typeof v === "number" && Number.isFinite(v) ? v : fallback);

export function fuelById(id) {
  return FUELS.find((f) => f.id === id) || FUELS[0];
}

/** The gravity preset a g value corresponds to, or null between presets. */
export function presetForGravity(g) {
  return GRAVITY_PRESETS.find((p) => Math.abs(p.g - g) < 0.0026) || null;
}

/** Inputs with every field present, finite and inside its limits. Never throws. */
export function sanitize(input = {}) {
  return {
    ignited: input.ignited === undefined ? DEFAULTS.ignited : Boolean(input.ignited),
    gravity: clamp(num(input.gravity, DEFAULTS.gravity), LIMITS.gravity.min, LIMITS.gravity.max),
    oxygen: clamp(num(input.oxygen, DEFAULTS.oxygen), LIMITS.oxygen.min, LIMITS.oxygen.max),
    airflow: clamp(num(input.airflow, DEFAULTS.airflow), LIMITS.airflow.min, LIMITS.airflow.max),
    fuel: fuelById(input.fuel).id,
  };
}

/**
 * Drawing parameters for the flame. Every value is unitless and exists only to drive the picture.
 * @returns {{ lit: number, stretch: number, lean: number, size: number, brightness: number, luminous: number,
 *   flicker: number, rise: number, drift: number, smoke: number, shape: string }}
 */
export function flameLook(input, { reducedMotion = false } = {}) {
  const s = sanitize(input);
  const fuel = fuelById(s.fuel);
  const buoyancy = Math.sqrt(s.gravity); // perceptual: small gravities are still visible
  const o2 = (s.oxygen - LIMITS.oxygen.min) / (LIMITS.oxygen.max - LIMITS.oxygen.min);
  const look = {
    lit: s.ignited ? 1 : 0,
    stretch: 1.3 * buoyancy + 0.35 * s.airflow,
    lean: 0.95 * s.airflow,
    size: 0.78 + 0.5 * o2,
    brightness: 0.5 + 0.7 * o2,
    luminous: clamp(fuel.soot * (0.3 + 0.7 * buoyancy) + 0.12 * o2, 0, 1),
    flicker: clamp(0.1 + 0.9 * Math.max(buoyancy, s.airflow), 0, 1),
    rise: buoyancy,
    drift: s.airflow,
    smoke: fuel.soot * (0.25 + 0.75 * buoyancy),
    shape: fuel.shape,
  };
  if (reducedMotion) return { ...look, flicker: 0, rise: 0, drift: 0 };
  return look;
}

/**
 * What the viewer is looking at, in words: one honest, qualitative sentence per control. No
 * numbers other than the inputs the viewer chose, and no prediction.
 */
export function describe(input) {
  const s = sanitize(input);
  const preset = presetForGravity(s.gravity);
  const gravityName = preset ? `${preset.label} (${preset.gLabel})` : `${s.gravity.toFixed(2)} g`;
  const lines = [];
  if (!s.ignited) lines.push({ control: "ignition", text: "Not ignited. Press Ignite to start the illustrated flame." });
  lines.push({
    control: "gravity",
    text:
      s.gravity < 0.01
        ? `Gravity: ${gravityName}. Without buoyancy, hot gas does not rise, so the drawing shows a rounder, calmer flame. Droplet flames in real microgravity experiments are typically near-spherical.`
        : `Gravity: ${gravityName}. Buoyancy lifts hot gas, so the drawing stretches the flame upward, more as gravity increases.`,
  });
  lines.push({
    control: "oxygen",
    text:
      s.oxygen > 21
        ? `Oxygen: ${s.oxygen}% of the surrounding gas (your input). More oxygen generally makes combustion more vigorous; the drawing is brighter and larger.`
        : s.oxygen < 21
          ? `Oxygen: ${s.oxygen}% of the surrounding gas (your input). Less oxygen generally weakens combustion; the drawing is dimmer and smaller. Where a real flame would go out is not modelled.`
          : "Oxygen: 21% of the surrounding gas (your input), similar to air.",
  });
  lines.push({
    control: "airflow",
    text:
      s.airflow < 0.01
        ? "Airflow: still surroundings."
        : "Airflow: a forced flow leans and stretches the drawn flame downstream. Real flames can be strengthened or blown out by airflow depending on conditions this drawing does not model.",
  });
  lines.push({
    control: "fuel",
    text:
      fuelById(s.fuel).soot > 0.5
        ? "Fuel: a sootier look. Glowing soot is what makes many flames yellow; the drawing is warmer, with more smoke where buoyancy carries it."
        : "Fuel: a low-soot look. With little soot the drawn flame stays dim and blue.",
  });
  return lines;
}

/** Keyboard controls of the Flame Lab. */
export const KEYMAP = Object.freeze({
  ArrowLeft: "orbit-left",
  ArrowRight: "orbit-right",
  ArrowUp: "orbit-up",
  ArrowDown: "orbit-down",
  "+": "zoom-in",
  "=": "zoom-in",
  "-": "zoom-out",
  r: "reset-view",
  R: "reset-view",
  i: "toggle-ignition",
  I: "toggle-ignition",
  " ": "toggle-ignition",
  "1": "gravity:microgravity",
  "2": "gravity:moon",
  "3": "gravity:mars",
  "4": "gravity:earth",
});

export function keyAction(key) {
  return KEYMAP[key] || null;
}

/** Whether the browser can draw the scene. `makeCanvas` is injectable for tests. */
export function webglAvailable(makeCanvas = () => document.createElement("canvas")) {
  try {
    const canvas = makeCanvas();
    return Boolean(canvas && (canvas.getContext("webgl2") || canvas.getContext("webgl")));
  } catch {
    return false;
  }
}

export function prefersReducedMotion(match = (q) => (typeof matchMedia === "function" ? matchMedia(q) : null)) {
  const mq = match("(prefers-reduced-motion: reduce)");
  return Boolean(mq && mq.matches);
}

/**
 * Whether the render loop should draw a frame now. With reduced motion the scene idles: it draws
 * only when a still frame is pending (first paint, a control, the camera or the size changed).
 */
export function shouldAnimate({ reducedMotion = false, visible = true, hidden = false, pending = false } = {}) {
  if (!visible || hidden) return false;
  return reducedMotion ? Boolean(pending) : true;
}

/** `?scene=off` forces the non-WebGL fallback (for tests and constrained devices). */
export function sceneMode(href = typeof location === "object" ? location.href : "http://x/") {
  return new URL(href).searchParams.get("scene") === "off" ? "off" : "auto";
}

/** The evidence call-to-action, worded from what is actually loaded; never claims unregistered evidence. */
export function evidenceCta(ev = {}) {
  if (ev.source === "fixtures") return { label: "Open the Evidence Explorer", status: "Fixture data, not NASA data" };
  if (ev.state === "error") return { label: "Open the Evidence Explorer", status: "Evidence unavailable right now" };
  if (ev.state !== "ready") return { label: "Open the Evidence Explorer", status: "Checking registered evidence…" };
  if (!ev.measured) return { label: "Open the Evidence Explorer", status: "No NASA evidence registered yet" };
  const n = ev.measured;
  const inv = ev.investigations || 0;
  return {
    label: "Explore the registered NASA evidence",
    status: `${n} measured finding${n === 1 ? "" : "s"} in ${inv} investigation${inv === 1 ? "" : "s"}`,
  };
}
