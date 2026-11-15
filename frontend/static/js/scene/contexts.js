// Pure data and decisions for the illustrative research scene. No DOM, no WebGL: unit-tested in
// frontend/tests/scene.test.js.
//
// Scientific rule for everything in this file: the scene is an ILLUSTRATION. Gravity values are
// standard reference values for the bodies. The flame shape, brightness and particle drift are an
// artistic, monotonic mapping of "less gravity, less buoyancy", not a computed or validated model,
// and nothing here is a NASA measurement, a prediction, a fire-risk score or a suppression score.

export const DISCLAIMER = "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data.";

export const ASSUMPTIONS =
  "Fuel, oxygen fraction, pressure and airflow are not modelled. The flame's shape, colour and particle drift are an artistic choice that only follows the direction of the effect: less gravity, less buoyancy.";

/**
 * Gravity contexts. `g` is a standard reference value (m/s^2). `look` drives the drawing only.
 * @type {ReadonlyArray<{id: string, label: string, short: string, g: number, gLabel: string, explanation: string, look: {stretch: number, luminous: number, rise: number, flicker: number}}>}
 */
export const CONTEXTS = Object.freeze([
  {
    id: "microgravity",
    label: "Microgravity (ISS)",
    short: "µg",
    g: 0,
    gLabel: "about 0 g",
    explanation:
      "In orbit, hot gas around a burning droplet does not rise, so there is no buoyant plume to stretch the flame. Droplet flames in microgravity experiments are typically near-spherical and burn more slowly and dimly than on Earth, which is why NASA studies them on the ISS. The drawing shows that idea, not a measured flame.",
    look: { stretch: 0.0, luminous: 0.18, rise: 0.0, flicker: 0.15 },
  },
  {
    id: "moon",
    label: "Moon",
    short: "Moon",
    g: 1.62,
    gLabel: "about 0.165 g",
    explanation:
      "Lunar gravity is about a sixth of Earth's, so buoyancy is weak but not absent. A lunar habitat sits between orbit and Earth; how a real flame behaves there depends on materials, oxygen and airflow, which this drawing does not model.",
    look: { stretch: 0.35, luminous: 0.42, rise: 0.17, flicker: 0.35 },
  },
  {
    id: "mars",
    label: "Mars",
    short: "Mars",
    g: 3.71,
    gLabel: "about 0.38 g",
    explanation:
      "Martian gravity is a little over a third of Earth's. The drawing shows more buoyant stretching than on the Moon and less than on Earth. It is not a prediction for a Mars habitat, whose atmosphere and pressure the scene does not model.",
    look: { stretch: 0.62, luminous: 0.6, rise: 0.38, flicker: 0.55 },
  },
  {
    id: "earth",
    label: "Earth",
    short: "Earth",
    g: 9.81,
    gLabel: "1 g",
    explanation:
      "On Earth, hot combustion gas rises, draws in fresh air from below and pulls the flame into the familiar elongated, bright shape. That buoyant flow is the reason Earth fire intuition does not transfer directly to spacecraft.",
    look: { stretch: 1.35, luminous: 0.95, rise: 1.0, flicker: 1.0 },
  },
]);

export const DEFAULT_CONTEXT = "microgravity";

/** @param {string} id */
export function contextById(id) {
  return CONTEXTS.find((c) => c.id === id) || CONTEXTS.find((c) => c.id === DEFAULT_CONTEXT);
}

/** The drawing parameters for a context, frozen in place when motion is reduced. */
export function flameLook(id, reducedMotion = false) {
  const { look } = contextById(id);
  return reducedMotion ? { ...look, flicker: 0, rise: 0 } : { ...look };
}

/**
 * The evidence call-to-action, worded from what is actually loaded. Never claims evidence that is
 * not registered, and never presents fixtures as NASA data.
 * @param {{ source?: string, investigations?: number, measured?: number, state?: string }} ev
 */
export function evidenceCta(ev = {}) {
  if (ev.source === "fixtures") return { label: "Open the Evidence Explorer", status: "Fixture data, not NASA data" };
  if (ev.state === "error") return { label: "Open the Evidence Explorer", status: "Evidence unavailable right now" };
  if (ev.state !== "ready") return { label: "Open the Evidence Explorer", status: "Checking registered evidence…" };
  if (!ev.measured) return { label: "Open the Evidence Explorer", status: "No NASA evidence registered yet" };
  const n = ev.measured;
  const inv = ev.investigations || 0;
  return {
    label: "Explore the registered evidence",
    status: `${n} measured finding${n === 1 ? "" : "s"} in ${inv} investigation${inv === 1 ? "" : "s"}`,
  };
}

/** Keyboard controls of the scene (documented in the panel and the help text). */
export const KEYMAP = Object.freeze({
  ArrowLeft: "orbit-left",
  ArrowRight: "orbit-right",
  ArrowUp: "orbit-up",
  ArrowDown: "orbit-down",
  "+": "zoom-in",
  "=": "zoom-in",
  "-": "zoom-out",
  r: "reset",
  R: "reset",
  c: "inspect",
  C: "inspect",
  "1": "context:microgravity",
  "2": "context:moon",
  "3": "context:mars",
  "4": "context:earth",
});

/** @param {string} key */
export function keyAction(key) {
  return KEYMAP[key] || null;
}

/**
 * Whether the browser can draw the scene. `makeCanvas` is injectable for tests.
 * @param {() => {getContext: (kind: string) => unknown}} [makeCanvas]
 */
export function webglAvailable(makeCanvas = () => document.createElement("canvas")) {
  try {
    const canvas = makeCanvas();
    return Boolean(canvas && (canvas.getContext("webgl2") || canvas.getContext("webgl")));
  } catch {
    return false;
  }
}

/** True when the user asked for reduced motion (or the query is unavailable: then false). */
export function prefersReducedMotion(match = (q) => (typeof matchMedia === "function" ? matchMedia(q) : null)) {
  const mq = match("(prefers-reduced-motion: reduce)");
  return Boolean(mq && mq.matches);
}

/** URL switches for tests and constrained devices: ?scene=off forces the still image. */
export function sceneMode(href = typeof location === "object" ? location.href : "http://x/") {
  const v = new URL(href).searchParams.get("scene");
  return v === "off" ? "off" : "auto";
}
