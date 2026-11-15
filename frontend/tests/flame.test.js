// Flame Lab parameter model (static/js/flame/params.js): pure logic, no WebGL.
import { assert, test } from "./harness.js";
import { ASSUMPTIONS, DEFAULTS, DISCLAIMER, FUELS, GRAVITY_PRESETS, KEYMAP, LIMITS, describe, evidenceCta, flameLook, fuelById, keyAction, prefersReducedMotion, presetForGravity, sanitize, sceneMode, webglAvailable } from "../static/js/flame/params.js";

const NUMERIC = ["lit", "stretch", "lean", "size", "brightness", "luminous", "flicker", "rise", "drift", "smoke"];
const grid = () => {
  const out = [];
  for (const gravity of [0, 0.165, 0.38, 0.7, 1])
    for (const oxygen of [15, 21, 30, 40])
      for (const airflow of [0, 0.3, 1])
        for (const fuel of FUELS.map((f) => f.id)) for (const ignited of [true, false]) out.push({ gravity, oxygen, airflow, fuel, ignited });
  return out;
};

test("flame: the disclaimer is exact and the assumptions say nothing is calculated", () => {
  assert.equal(DISCLAIMER, "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data.");
  assert.includes(ASSUMPTIONS, "not a calculation");
  assert.includes(ASSUMPTIONS, "nothing shown is a prediction");
});

test("flame: gravity presets are the reference values, in order, and round-trip", () => {
  assert.deepEqual(GRAVITY_PRESETS.map((p) => [p.id, p.g]), [["microgravity", 0], ["moon", 0.165], ["mars", 0.38], ["earth", 1]]);
  for (const p of GRAVITY_PRESETS) assert.equal(presetForGravity(p.g).id, p.id);
  assert.equal(presetForGravity(0.5), null);
});

test("flame: fuels are generic looks, never named after a real fuel", () => {
  assert.equal(FUELS.length, 3);
  for (const f of FUELS) assert.ok(!/methanol|heptane|ethanol|kerosene|hydrogen|methane|PMMA|paper|cotton/i.test(f.label), f.label);
  assert.equal(fuelById("nope").id, FUELS[0].id, "an unknown fuel falls back safely");
});

test("flame: sanitize clamps, fills and never throws on junk", () => {
  assert.deepEqual(sanitize(), { ...DEFAULTS });
  assert.deepEqual(sanitize({ gravity: 9, oxygen: -5, airflow: 3, fuel: "x", ignited: 0 }), { ignited: false, gravity: 1, oxygen: 15, airflow: 1, fuel: FUELS[0].id });
  for (const junk of [NaN, Infinity, -Infinity, "1", null, undefined, {}, []]) {
    const s = sanitize({ gravity: junk, oxygen: junk, airflow: junk });
    assert.ok(Number.isFinite(s.gravity) && Number.isFinite(s.oxygen) && Number.isFinite(s.airflow), String(junk));
    assert.ok(s.oxygen >= LIMITS.oxygen.min && s.oxygen <= LIMITS.oxygen.max);
  }
});

test("flame: every drawing parameter is finite and bounded for every input combination", () => {
  for (const input of grid()) {
    const look = flameLook(input);
    for (const k of NUMERIC) {
      assert.ok(Number.isFinite(look[k]), `${k} for ${JSON.stringify(input)}`);
      assert.ok(look[k] >= 0 && look[k] <= 2, `${k}=${look[k]} out of range`);
    }
    assert.ok(look.shape === "droplet" || look.shape === "solid");
    assert.equal(look.lit, input.ignited ? 1 : 0);
  }
});

test("flame: the response follows only the direction of each effect (monotonic)", () => {
  const base = { ...DEFAULTS, fuel: "sooty-liquid" };
  const seq = (key, values, param) => values.map((v) => flameLook({ ...base, [key]: v })[param]);
  const rising = (xs) => xs.every((x, i) => i === 0 || x >= xs[i - 1]) && xs[xs.length - 1] > xs[0];
  assert.ok(rising(seq("gravity", [0, 0.165, 0.38, 1], "stretch")), "more gravity, more buoyant stretch");
  assert.ok(rising(seq("gravity", [0, 0.165, 0.38, 1], "rise")), "more gravity, particles rise faster");
  assert.ok(rising(seq("gravity", [0, 0.165, 0.38, 1], "luminous")), "more gravity, a sootier flame glows warmer");
  assert.ok(rising(seq("oxygen", [15, 21, 30, 40], "brightness")), "more oxygen, brighter");
  assert.ok(rising(seq("oxygen", [15, 21, 30, 40], "size")), "more oxygen, larger");
  assert.ok(rising(seq("airflow", [0, 0.3, 0.7, 1], "lean")), "more airflow, more lean");
  assert.ok(rising(seq("airflow", [0, 0.3, 0.7, 1], "drift")), "more airflow, more drift");
  assert.ok(flameLook({ ...base, fuel: "sooty-liquid", gravity: 1 }).luminous > flameLook({ ...base, fuel: "low-soot-liquid", gravity: 1 }).luminous);
  assert.ok(flameLook({ ...base, fuel: "sooty-liquid", gravity: 1 }).smoke > flameLook({ ...base, fuel: "low-soot-liquid", gravity: 1 }).smoke);
});

test("flame: microgravity is round and calm; nothing leans without airflow", () => {
  const mg = flameLook({ ...DEFAULTS, gravity: 0, airflow: 0 });
  assert.equal(mg.stretch, 0);
  assert.equal(mg.rise, 0);
  assert.equal(mg.lean, 0);
  assert.ok(mg.flicker <= 0.11);
  assert.equal(flameLook({ ...DEFAULTS, fuel: "solid-sample" }).shape, "solid");
});

test("flame: reduced motion freezes movement but keeps the picture", () => {
  const input = { ...DEFAULTS, gravity: 1, airflow: 0.8, fuel: "sooty-liquid" };
  const still = flameLook(input, { reducedMotion: true });
  const moving = flameLook(input);
  assert.equal(still.flicker, 0);
  assert.equal(still.rise, 0);
  assert.equal(still.drift, 0);
  assert.equal(still.stretch, moving.stretch, "the shape is unchanged");
  assert.equal(still.lean, moving.lean);
  assert.equal(still.luminous, moving.luminous);
});

test("flame: the explanation is qualitative: no outputs, no predictions, only the viewer's own inputs as numbers", () => {
  const banned = /\b(kelvin|celsius|°C|°F|K\b|mm\/s|cm\/s|m\/s|kW|watts?|joules?|probabilit|risk score|risk of|chance of|will ignite|will extinguish|will go out|predict(s|ed|ion)? that|safe to|unsafe|suppression (score|rate))/i;
  for (const input of grid()) {
    const lines = describe(input);
    assert.ok(lines.length >= 4);
    for (const line of lines) {
      assert.ok(!banned.test(line.text), line.text);
      const numbers = line.text.match(/\d+(\.\d+)?/g) || [];
      const allowed = new Set([String(input.oxygen), "21", input.gravity.toFixed(2), "0", "0.165", "0.38", "1"]);
      for (const n of numbers) assert.ok(allowed.has(n), `unexpected number ${n} in: ${line.text}`);
    }
    assert.deepEqual(lines.filter((l) => l.control !== "ignition").map((l) => l.control), ["gravity", "oxygen", "airflow", "fuel"]);
    assert.equal(lines.some((l) => l.control === "ignition"), !input.ignited);
  }
  assert.includes(describe({ ...DEFAULTS, oxygen: 16 }).find((l) => l.control === "oxygen").text, "not modelled");
});

test("flame: the evidence link is worded from what is loaded and never claims unregistered evidence", () => {
  assert.equal(evidenceCta({ state: "ready", measured: 0, investigations: 0 }).status, "No NASA evidence registered yet");
  assert.equal(evidenceCta({ state: "ready", measured: 40, investigations: 1 }).status, "40 measured findings in 1 investigation");
  assert.equal(evidenceCta({ state: "ready", measured: 1, investigations: 2 }).status, "1 measured finding in 2 investigations");
  assert.equal(evidenceCta({ source: "fixtures", state: "ready", measured: 4 }).status, "Fixture data, not NASA data");
  assert.equal(evidenceCta({ state: "error" }).status, "Evidence unavailable right now");
  assert.includes(evidenceCta({}).status, "Checking");
  for (const ev of [{}, { state: "error" }, { state: "ready", measured: 0 }, { source: "fixtures" }]) assert.ok(!/NASA evidence$|registered NASA/.test(evidenceCta(ev).label), "no claim of registered evidence");
});

test("flame: keyboard map covers orbit, zoom, reset, ignition and the four gravity presets", () => {
  assert.equal(keyAction("ArrowLeft"), "orbit-left");
  assert.equal(keyAction("+"), "zoom-in");
  assert.equal(keyAction("-"), "zoom-out");
  assert.equal(keyAction("r"), "reset-view");
  assert.equal(keyAction("i"), "toggle-ignition");
  assert.equal(keyAction(" "), "toggle-ignition");
  assert.deepEqual(["1", "2", "3", "4"].map(keyAction), GRAVITY_PRESETS.map((p) => `gravity:${p.id}`));
  assert.equal(keyAction("q"), null);
  assert.ok(Object.isFrozen(KEYMAP));
});

test("flame: WebGL, reduced-motion and scene-off decisions fail safe", () => {
  assert.equal(webglAvailable(() => ({ getContext: (k) => (k === "webgl2" ? {} : null) })), true);
  assert.equal(webglAvailable(() => ({ getContext: (k) => (k === "webgl" ? {} : null) })), true);
  assert.equal(webglAvailable(() => ({ getContext: () => null })), false);
  assert.equal(webglAvailable(() => { throw new Error("blocked"); }), false);
  assert.equal(prefersReducedMotion(() => ({ matches: true })), true);
  assert.equal(prefersReducedMotion(() => ({ matches: false })), false);
  assert.equal(prefersReducedMotion(() => null), false);
  assert.equal(sceneMode("http://x.test/?scene=off#/flame"), "off");
  assert.equal(sceneMode("http://x.test/#/flame"), "auto");
});

test("flame: the Flame Lab is a first-class route, lazily loads its scene, and the evidence routes are untouched", async () => {
  const main = await (await fetch(new URL("../static/js/main.js", import.meta.url))).text();
  assert.includes(main, '"/flame": { view: flame, nav: "Flame Lab"');
  for (const path of ['"/"', '"/explorer"', '"/compare"', '"/rank"', '"/interpret"', '"/tars"', '"/integrations"']) assert.includes(main, `${path}: { view:`);
  assert.ok(!/from "\.\/flame\/flame-scene\.js"|from "three"/.test(main), "three.js is never loaded by the app shell");
  const view = await (await fetch(new URL("../static/js/views/flame.js", import.meta.url))).text();
  assert.includes(view, 'await import("../flame/flame-scene.js")');
  assert.ok(!/^import .*three/m.test(view), "the view loads the 3D scene lazily");
  const html = await (await fetch(new URL("../index.html", import.meta.url))).text();
  assert.includes(html, '"three": "./static/vendor/three/three.module.min.js"');
  assert.ok(!/https?:\/\/(unpkg|cdn|cdnjs|jsdelivr)/.test(html), "no CDN: the demo must work offline");
});
