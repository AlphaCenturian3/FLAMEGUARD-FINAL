// Flame Lab scene: one isolated, ILLUSTRATIVE flame on a minimal specimen stage. No room, no
// spacecraft. Loaded lazily by the Flame Lab view only. Every visual response comes from
// params.js (direction-only artistic mapping); nothing here is computed combustion or NASA data.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { flameLook, keyAction, shouldAnimate } from "./params.js";

const EMBERS = 420;
const SMOKE = 220;
const SPARKS = 90;
const HOME = new THREE.Vector3(0.0, 0.2, 1.3);
const TARGET = new THREE.Vector3(0, 0.14, 0);

const NOISE = /* glsl */ `
float hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453); }
float noise(vec3 p) {
  vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}`;

function shellMaterial(layer) {
  // layer: 0 outer envelope, 1 middle, 2 inner core
  return new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uStretch: { value: 0 },
      uLean: { value: 0 },
      uFlicker: { value: 0.1 },
      uLum: { value: 0.1 },
      uBright: { value: 0.7 },
      uSolid: { value: 0 },
      uLayer: { value: layer },
    },
    vertexShader: /* glsl */ `
      uniform float uTime, uStretch, uLean, uFlicker, uSolid, uLayer;
      varying vec3 vN; varying vec3 vView; varying float vH;
      ${NOISE}
      void main() {
        vec3 p = position;
        // a solid sample burns from a wider, flatter base
        p.x *= 1.0 + 0.75 * uSolid;
        p.y = mix(p.y, max(p.y, -0.35), uSolid);
        float up = max(p.y, 0.0);
        p.y += up * up * uStretch * 1.75;                       // buoyant / flow stretching
        // taper the stretched upper half to a soft point (a sphere when there is no stretch)
        p.xz *= mix(1.0, 1.0 - 0.94 * pow(up, 1.35), clamp(uStretch, 0.0, 1.0));
        float h = max(p.y + 1.0, 0.0);
        p.x += uLean * h * h * 0.22;                            // airflow leans the flame downstream
        float n = noise(p * (1.7 + 0.5 * uLayer) + vec3(uTime * 0.35, -uTime * 2.2, uTime * 0.25));
        p += normal * (n - 0.5) * 0.2 * uFlicker * (0.25 + 0.6 * up) * (1.0 - 0.6 * smoothstep(0.6, 1.0, up));
        vH = p.y;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        vView = normalize(-mv.xyz);
        vN = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */ `
      uniform float uLum, uBright, uLayer;
      varying vec3 vN; varying vec3 vView; varying float vH;
      void main() {
        float facing = abs(dot(normalize(vN), normalize(vView)));
        float rim = 1.0 - facing;
        vec3 blue = vec3(0.22, 0.42, 1.0);
        vec3 warm = mix(vec3(1.0, 0.24, 0.02), vec3(1.0, 0.52, 0.07), clamp(vH * 0.45 + 0.4, 0.0, 1.0));
        vec3 col; float a;
        if (uLayer > 1.5) {            // inner core: hot, pale
          col = mix(vec3(0.5, 0.68, 1.0), vec3(1.0, 0.74, 0.28), uLum);
          a = pow(facing, 3.0) * 0.7;
        } else if (uLayer > 0.5) {     // middle body
          col = mix(blue * 1.1, warm, uLum);
          a = pow(facing, 1.6) * 0.42;
        } else {                        // outer envelope: thin blue edge even on sooty flames
          col = mix(blue, mix(warm, blue, 0.18), uLum);
          a = pow(rim, 2.0) * 0.9 + 0.05 * facing;
        }
        // sooty (luminous) flames glow more strongly than blue, soot-free ones
        gl_FragColor = vec4(col * (0.4 + 0.55 * uBright) * (1.0 + 0.5 * uLum), a * (0.28 + 0.44 * uBright) * (1.0 + 0.25 * uLum));
      }`,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}

function pointsMaterial(additive) {
  return new THREE.ShaderMaterial({
    uniforms: { uPixel: { value: 1 }, uWarm: { value: 0.2 }, uSmoke: { value: additive ? 0 : 1 } },
    vertexShader: /* glsl */ `
      attribute float aAlpha; attribute float aSize;
      uniform float uPixel;
      varying float vAlpha;
      void main() {
        vAlpha = aAlpha;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = aSize * uPixel * (320.0 / -mv.z);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */ `
      uniform float uWarm, uSmoke;
      varying float vAlpha;
      void main() {
        float d = length(gl_PointCoord - 0.5);
        if (d > 0.5) discard;
        float soft = smoothstep(0.5, 0.0, d);
        vec3 ember = mix(vec3(0.5, 0.65, 1.0), vec3(1.0, 0.58, 0.2), uWarm);
        vec3 col = mix(ember, vec3(0.16, 0.17, 0.2), uSmoke);
        gl_FragColor = vec4(col, soft * soft * vAlpha);
      }`,
    transparent: true,
    depthWrite: false,
    blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
  });
}

function makePool(count, additive) {
  const pos = new Float32Array(count * 3);
  const vel = new Float32Array(count * 3);
  const age = new Float32Array(count).fill(1);
  const life = new Float32Array(count).fill(1);
  const alpha = new Float32Array(count);
  const size = new Float32Array(count);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("aAlpha", new THREE.BufferAttribute(alpha, 1));
  geo.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
  const mat = pointsMaterial(additive);
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  let cursor = 0;
  return {
    points,
    mat,
    count,
    emit(x, y, z, vx, vy, vz, lifetime) {
      const i = cursor;
      cursor = (cursor + 1) % count;
      pos.set([x, y, z], i * 3);
      vel.set([vx, vy, vz], i * 3);
      age[i] = 0;
      life[i] = lifetime;
    },
    update(dt, ax, ay, fade, baseSize, grow) {
      for (let i = 0; i < count; i++) {
        if (age[i] >= life[i]) {
          alpha[i] = 0;
          continue;
        }
        age[i] += dt;
        const k = i * 3;
        vel[k] += ax * dt;
        vel[k + 1] += ay * dt;
        pos[k] += vel[k] * dt;
        pos[k + 1] += vel[k + 1] * dt;
        pos[k + 2] += vel[k + 2] * dt;
        const f = Math.min(1, age[i] / life[i]);
        alpha[i] = Math.sin(Math.PI * f) * fade;
        size[i] = baseSize * (1 + grow * f);
      }
      geo.attributes.position.needsUpdate = true;
      geo.attributes.aAlpha.needsUpdate = true;
      geo.attributes.aSize.needsUpdate = true;
    },
    freeze(fade, baseSize) {
      for (let i = 0; i < count; i++) {
        alpha[i] = age[i] < life[i] ? fade * 0.6 : 0;
        size[i] = baseSize;
      }
      geo.attributes.aAlpha.needsUpdate = true;
      geo.attributes.aSize.needsUpdate = true;
    },
    dispose() {
      geo.dispose();
      mat.dispose();
    },
  };
}

function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
}

/**
 * @param {HTMLElement} host
 * @param {{inputs: object, reducedMotion: boolean, label: string, onAction?: (action: string) => void}} opts
 */
export async function createFlameScene(host, opts) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.75);
  renderer.setPixelRatio(pixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.info.autoReset = false; // count the whole frame, not only the last pass
  const canvas = renderer.domElement;
  canvas.className = "flame-canvas";
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", opts.label);
  host.appendChild(canvas);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x02040a);
  scene.fog = new THREE.FogExp2(0x02040a, 0.1);
  const camera = new THREE.PerspectiveCamera(40, 1, 0.02, 60);
  camera.position.copy(HOME);

  // --- backdrop: a soft vignette dome and slow dust, nothing else ---------------------------
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(30, 32, 16),
    new THREE.ShaderMaterial({
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
      vertexShader: "varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
      fragmentShader: "varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 top = vec3(0.003,0.005,0.014); vec3 low = vec3(0.01,0.016,0.036); vec3 c = mix(low, top, smoothstep(-0.2, 0.7, h)); gl_FragColor = vec4(c,1.0); }",
    }),
  );
  scene.add(dome);
  const dust = makePool(160, true);
  dust.mat.uniforms.uPixel.value = pixelRatio;
  scene.add(dust.points);
  let seed = 7;
  const rnd = () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
  for (let i = 0; i < dust.count; i++) dust.emit((rnd() - 0.5) * 5, (rnd() - 0.3) * 3, (rnd() - 0.5) * 5 - 0.5, (rnd() - 0.5) * 0.01, (rnd() - 0.5) * 0.01, 0, 1e9);

  // --- specimen stage: a fine ring and a support, to give the flame scale and a ground -------
  const stage = new THREE.Group();
  scene.add(stage);
  const metal = new THREE.MeshStandardMaterial({ color: 0x8792a6, metalness: 0.9, roughness: 0.28 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x10141d, metalness: 0.6, roughness: 0.55 });
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.66, 0.03, 96), dark);
  disc.position.y = -0.62;
  stage.add(disc);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x5cc8ff, transparent: true, opacity: 0.55 });
  for (const [r, w, o] of [[0.6, 0.004, 0.55], [0.42, 0.002, 0.3], [0.24, 0.002, 0.2]]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, w, 8, 128), ringMat.clone());
    ring.material.opacity = o;
    ring.rotation.x = Math.PI / 2;
    ring.position.y = -0.602;
    stage.add(ring);
  }
  const needle = new THREE.Mesh(new THREE.CylinderGeometry(0.0035, 0.006, 0.6, 12), metal);
  needle.position.y = -0.31;
  stage.add(needle);
  const droplet = new THREE.Mesh(
    new THREE.SphereGeometry(0.03, 32, 20),
    new THREE.MeshPhysicalMaterial({ color: 0x9fb9d8, roughness: 0.08, metalness: 0, transmission: 0.6, thickness: 0.05, ior: 1.33 }),
  );
  stage.add(droplet);
  const slab = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.012, 0.12), new THREE.MeshStandardMaterial({ color: 0x3a3128, roughness: 0.9 }));
  slab.position.y = -0.02;
  stage.add(slab);
  scene.add(new THREE.HemisphereLight(0x9fb4ff, 0x05070c, 0.35));
  const rimLight = new THREE.DirectionalLight(0x7fa8ff, 0.5);
  rimLight.position.set(-2, 1.5, -1.5);
  scene.add(rimLight);

  // --- the illustrative flame ---------------------------------------------------------------
  const flame = new THREE.Group();
  scene.add(flame);
  const mats = [shellMaterial(0), shellMaterial(1), shellMaterial(2)];
  const shells = [
    new THREE.Mesh(new THREE.IcosahedronGeometry(1, 7), mats[0]),
    new THREE.Mesh(new THREE.IcosahedronGeometry(1, 6), mats[1]),
    new THREE.Mesh(new THREE.IcosahedronGeometry(1, 5), mats[2]),
  ];
  const BASE = [0.15, 0.115, 0.07];
  shells.forEach((m) => flame.add(m));
  const glow = new THREE.PointLight(0xff8a3d, 0, 4, 2);
  glow.position.y = 0.05;
  flame.add(glow);
  const embers = makePool(EMBERS, true);
  const smoke = makePool(SMOKE, false);
  const sparks = makePool(SPARKS, true);
  for (const p of [embers, smoke, sparks]) {
    p.mat.uniforms.uPixel.value = pixelRatio;
    scene.add(p.points);
  }

  // --- post-processing: bloom gives the flame its glow ----------------------------------------
  const composer = new EffectComposer(renderer);
  composer.setPixelRatio(pixelRatio);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), 0.5, 0.55, 0.32);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  // --- controls ------------------------------------------------------------------------------
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(TARGET);
  controls.enableDamping = !opts.reducedMotion; // damping needs a running loop
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.minDistance = 0.5;
  controls.maxDistance = 4;
  controls.minPolarAngle = Math.PI * 0.12;
  controls.maxPolarAngle = Math.PI * 0.6;
  controls.autoRotate = !opts.reducedMotion;
  controls.autoRotateSpeed = 0.45;
  controls.update();
  const stopAuto = () => {
    controls.autoRotate = false;
  };
  canvas.addEventListener("pointerdown", stopAuto);
  canvas.addEventListener("wheel", stopAuto, { passive: true });

  // --- state ---------------------------------------------------------------------------------
  let reduced = opts.reducedMotion;
  let target = flameLook(opts.inputs, { reducedMotion: reduced });
  const shown = { ...target, lit: 0 };
  let ignitionT = target.lit ? 0 : 1; // seconds since ignition started (drives the spark and overshoot)
  let smokeBurst = 0;
  let tween = null;
  let emitE = 0;
  let emitS = 0;

  const applyLook = (l, elapsed) => {
    const solid = l.shape === "solid" ? 1 : 0;
    droplet.visible = !solid;
    needle.visible = true;
    slab.visible = Boolean(solid);
    const overshoot = ignitionT < 1.1 ? 1 + 0.35 * Math.sin(Math.min(1, ignitionT / 1.1) * Math.PI) : 1;
    const lit = l.lit * overshoot;
    shells.forEach((mesh, i) => {
      const s = BASE[i] * l.size * Math.max(lit, 0.0001);
      mesh.scale.set(s, s, s);
      mesh.visible = l.lit > 0.01;
      const u = mats[i].uniforms;
      u.uTime.value = elapsed;
      u.uStretch.value = l.stretch;
      u.uLean.value = l.lean;
      u.uFlicker.value = l.flicker;
      u.uLum.value = l.luminous;
      u.uBright.value = l.brightness * Math.min(1, lit);
      u.uSolid.value = solid;
    });
    flame.position.set(0, solid ? 0.03 : 0, 0);
    glow.intensity = lit * (0.25 + 1.1 * l.brightness);
    glow.color.setRGB(0.45 + 0.55 * l.luminous, 0.5 + 0.1 * l.luminous, 1.0 - 0.8 * l.luminous);
    embers.mat.uniforms.uWarm.value = l.luminous;
    sparks.mat.uniforms.uWarm.value = 0.9;
    bloom.strength = 0.28 + 0.42 * l.brightness * Math.min(1, lit);
  };

  const emitParticles = (dt, l) => {
    if (l.lit < 0.05) return;
    emitE += dt * (40 + 90 * l.brightness) * l.lit;
    while (emitE >= 1) {
      emitE -= 1;
      const a = Math.random() * Math.PI * 2;
      const u = Math.random() * 2 - 1;
      const s = Math.sqrt(1 - u * u);
      const r = 0.08 * l.size;
      embers.emit(r * s * Math.cos(a), r * u * 0.9 + 0.02, r * s * Math.sin(a), s * Math.cos(a) * 0.03 + l.drift * 0.25, u * 0.03 + l.rise * 0.22, s * Math.sin(a) * 0.03, 1.2 + Math.random() * 1.8);
    }
    emitS += dt * (4 + 46 * l.smoke + smokeBurst * 60) * Math.max(l.lit, smokeBurst);
    while (emitS >= 1) {
      emitS -= 1;
      const a = Math.random() * Math.PI * 2;
      const r = 0.05 * l.size * Math.random();
      const top = 0.12 * l.size * (1 + l.stretch);
      smoke.emit(r * Math.cos(a) + l.lean * 0.15, top * (0.6 + 0.4 * Math.random()), r * Math.sin(a), Math.cos(a) * 0.015 + l.drift * 0.3, 0.02 + l.rise * 0.28, Math.sin(a) * 0.015, 2.5 + Math.random() * 2.5);
    }
  };

  const burstSparks = () => {
    for (let i = 0; i < SPARKS; i++) {
      const a = Math.random() * Math.PI * 2;
      const u = Math.random() * 2 - 1;
      const s = Math.sqrt(1 - u * u);
      const v = 0.25 + Math.random() * 0.5;
      sparks.emit(0, 0.01, 0, s * Math.cos(a) * v, u * v, s * Math.sin(a) * v, 0.25 + Math.random() * 0.45);
    }
  };

  // --- loop ----------------------------------------------------------------------------------
  const clock = new THREE.Clock();
  let raf = 0;
  let visible = true;
  let pending = true; // reduced motion: a still frame is waiting to be drawn
  let requestStill = () => {}; // set once the loop exists
  let frames = 0;
  let fpsWindow = { t: performance.now(), n: 0, fps: 0 };
  const resize = () => {
    const w = host.clientWidth || 1;
    const h = host.clientHeight || 1;
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
    camera.aspect = w / h;
    // keep the whole flame in frame on tall, narrow screens
    camera.fov = camera.aspect < 0.8 ? 52 : 40;
    camera.updateProjectionMatrix();
    requestStill();
  };
  const ro = new ResizeObserver(resize);
  ro.observe(host);
  resize();
  const io = new IntersectionObserver((entries) => {
    visible = entries.some((e) => e.isIntersecting);
    pending = true;
    if (visible && !raf) loop();
  });
  io.observe(host);
  const onVisibility = () => {
    pending = true;
    if (!document.hidden && visible && !raf) loop();
  };
  document.addEventListener("visibilitychange", onVisibility);

  function step(dt, elapsed) {
    const rate = reduced ? 1 : Math.min(1, dt * 3.2);
    for (const k of ["stretch", "lean", "size", "brightness", "luminous", "flicker", "rise", "drift", "smoke"]) shown[k] += (target[k] - shown[k]) * rate;
    shown.shape = target.shape;
    shown.lit += (target.lit - shown.lit) * (reduced ? 1 : Math.min(1, dt * (target.lit ? 2.6 : 4.5)));
    ignitionT += dt;
    smokeBurst = Math.max(0, smokeBurst - dt * 1.4);
    applyLook(shown, elapsed);
    if (!reduced) {
      emitParticles(dt, shown);
      embers.update(dt, 0, 0.02 * shown.rise, 0.5 + 0.4 * shown.brightness, 0.012, -0.4);
      smoke.update(dt, 0.02 * shown.drift, 0.03 * shown.rise, 0.2 + 0.25 * shown.smoke, 0.05, 3.2);
      sparks.update(dt, 0, -0.35 * shown.rise, 1, 0.012, -0.6);
      dust.update(dt, 0, 0, 0.16, 0.007, 0);
    }
    if (tween) {
      tween.t = Math.min(1, tween.t + dt / 0.9);
      camera.position.lerpVectors(tween.from, tween.to, easeInOut(tween.t));
      if (tween.t >= 1) tween = null;
    }
    controls.update();
  }

  function draw() {
    renderer.info.reset();
    composer.render();
    frames += 1;
  }

  function loop() {
    raf = 0;
    if (!shouldAnimate({ reducedMotion: reduced, visible, hidden: document.hidden, pending })) return;
    pending = false;
    const dt = Math.min(clock.getDelta(), 0.05);
    step(dt, clock.elapsedTime);
    draw();
    fpsWindow.n += 1;
    const now = performance.now();
    if (now - fpsWindow.t >= 1000) fpsWindow = { t: now, n: 0, fps: (fpsWindow.n * 1000) / (now - fpsWindow.t) };
    // reduced motion: one still frame, then idle until something changes (see requestStill)
    if (!reduced) raf = requestAnimationFrame(loop);
  }
  /** Reduced motion only: draw one more still frame (camera moved, resized, input changed). */
  requestStill = () => {
    if (!reduced) return;
    pending = true;
    if (!raf) raf = requestAnimationFrame(loop);
  };
  controls.addEventListener("change", requestStill);
  if (reduced) {
    // a still frame: seed a few motes so the picture is not empty, then draw only on change
    shown.lit = target.lit;
    for (let i = 0; i < 60; i++) emitParticles(0.05, { ...target, lit: target.lit });
    embers.freeze(0.5, 0.012);
    smoke.freeze(0.2, 0.08);
    dust.freeze(0.16, 0.007);
  }
  loop();

  // --- keyboard ------------------------------------------------------------------------------
  const spherical = new THREE.Spherical();
  const offset = new THREE.Vector3();
  const nudge = (dTheta, dPhi, scale) => {
    stopAuto();
    offset.copy(camera.position).sub(controls.target);
    spherical.setFromVector3(offset);
    spherical.theta += dTheta;
    spherical.phi = THREE.MathUtils.clamp(spherical.phi + dPhi, controls.minPolarAngle, controls.maxPolarAngle);
    spherical.radius = THREE.MathUtils.clamp(spherical.radius * scale, controls.minDistance, controls.maxDistance);
    offset.setFromSpherical(spherical);
    camera.position.copy(controls.target).add(offset);
    controls.update();
  };
  const onKey = (e) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
    const action = keyAction(e.key);
    if (!action) return;
    e.preventDefault();
    if (action === "orbit-left") nudge(-0.14, 0, 1);
    else if (action === "orbit-right") nudge(0.14, 0, 1);
    else if (action === "orbit-up") nudge(0, -0.08, 1);
    else if (action === "orbit-down") nudge(0, 0.08, 1);
    else if (action === "zoom-in") nudge(0, 0, 0.88);
    else if (action === "zoom-out") nudge(0, 0, 1.14);
    else if (action === "reset-view") api.resetView();
    else if (opts.onAction) opts.onAction(action);
  };
  host.addEventListener("keydown", onKey);

  const api = {
    setInputs(inputs) {
      const next = flameLook(inputs, { reducedMotion: reduced });
      if (next.lit && !target.lit) {
        ignitionT = 0;
        if (!reduced) burstSparks();
      }
      if (!next.lit && target.lit) smokeBurst = 1;
      target = next;
      requestStill();
    },
    setReducedMotion(on) {
      reduced = on;
      controls.enableDamping = !on;
      if (on) controls.autoRotate = false;
      pending = true;
      if (!raf) raf = requestAnimationFrame(loop);
      target = { ...target, ...(on ? { flicker: 0, rise: 0, drift: 0 } : {}) };
    },
    resetView() {
      stopAuto();
      if (reduced) {
        camera.position.copy(HOME);
        controls.update();
        requestStill();
        return;
      }
      tween = { from: camera.position.clone(), to: HOME.clone(), t: 0 };
    },
    stats() {
      return {
        frames,
        fps: Math.round(fpsWindow.fps),
        drawCalls: renderer.info.render.calls,
        triangles: renderer.info.render.triangles,
        pixelRatio,
        particles: EMBERS + SMOKE + SPARKS + dust.count,
        lit: Number(shown.lit.toFixed(3)),
      };
    },
    dispose() {
      cancelAnimationFrame(raf);
      raf = 0;
      ro.disconnect();
      io.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      host.removeEventListener("keydown", onKey);
      controls.dispose();
      for (const p of [embers, smoke, sparks, dust]) p.dispose();
      scene.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        const ms = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
        ms.forEach((m) => m.dispose());
      });
      composer.dispose();
      renderer.dispose();
      canvas.remove();
    },
  };
  return api;
}
