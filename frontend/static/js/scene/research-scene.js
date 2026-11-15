// The interactive research scene: an ORIGINAL ISS-style module (built in Blender by
// tools/visual/build_research_module.py) with an ILLUSTRATIVE droplet flame and particles.
// Loaded lazily by the overview only. Nothing drawn here is a NASA measurement or a validated
// simulation: see contexts.js for the scientific rules of this drawing.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { flameLook, keyAction } from "./contexts.js";

const MODEL_URL = new URL("../../models/research-module.glb", import.meta.url).href;
const PARTICLES = 520;
const CABIN = { x: 4.3, y: 0.92, z: 0.92 }; // camera must stay inside the cabin

const NOISE = /* glsl */ `
float hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453); }
float noise(vec3 p) {
  vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}`;

function flameMaterial(inner) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uStretch: { value: 0 },
      uLum: { value: 0.2 },
      uFlicker: { value: 0.2 },
      uInner: { value: inner ? 1 : 0 },
      uOpacity: { value: inner ? 0.9 : 0.75 },
    },
    vertexShader: /* glsl */ `
      uniform float uTime, uStretch, uFlicker;
      varying vec3 vN; varying vec3 vView; varying float vH;
      ${NOISE}
      void main() {
        vec3 p = position;
        float up = max(p.y, 0.0);
        p.y += up * up * uStretch * 1.7;
        p.xz *= 1.0 - 0.5 * uStretch * smoothstep(0.0, 1.2, up);
        float n = noise(p * 3.2 + vec3(0.0, -uTime * 2.4, uTime * 0.3));
        p += normal * (n - 0.5) * 0.22 * uFlicker * (0.25 + up);
        vH = p.y;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        vView = normalize(-mv.xyz);
        vN = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */ `
      uniform float uLum, uInner, uOpacity;
      varying vec3 vN; varying vec3 vView; varying float vH;
      void main() {
        float facing = abs(dot(normalize(vN), normalize(vView)));
        float rim = 1.0 - facing;
        vec3 blue = vec3(0.28, 0.48, 1.0);
        vec3 warm = mix(vec3(1.0, 0.38, 0.08), vec3(1.0, 0.78, 0.32), clamp(vH * 0.55 + 0.45, 0.0, 1.0));
        vec3 col = mix(blue, warm, uLum);
        float a;
        if (uInner > 0.5) { col = mix(vec3(0.45, 0.65, 1.0), vec3(1.0, 0.92, 0.7), uLum); a = pow(facing, 2.2); }
        else { a = pow(rim, 1.4) * 0.85 + 0.15 * facing; }
        gl_FragColor = vec4(col * (1.1 + 1.4 * uLum), a * uOpacity * (0.4 + 0.6 * uLum));
      }`,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}

function particleMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: { uSize: { value: 0.03 }, uLum: { value: 0.2 }, uPixel: { value: 1 } },
    vertexShader: /* glsl */ `
      attribute float aAlpha;
      uniform float uSize, uPixel;
      varying float vAlpha;
      void main() {
        vAlpha = aAlpha;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = uSize * uPixel * (300.0 / -mv.z);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */ `
      uniform float uLum;
      varying float vAlpha;
      void main() {
        vec2 c = gl_PointCoord - 0.5;
        float d = length(c);
        if (d > 0.5) discard;
        float soft = smoothstep(0.5, 0.0, d);
        vec3 col = mix(vec3(0.45, 0.6, 1.0), vec3(1.0, 0.6, 0.22), uLum);
        gl_FragColor = vec4(col, soft * vAlpha);
      }`,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}

function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
}

/**
 * Build the scene inside `host`. Resolves once the model is shown; rejects if WebGL or the model
 * fails (the caller then shows the still image).
 * @param {HTMLElement} host
 * @param {{context: string, reducedMotion: boolean, onContextKey?: (id: string) => void, label: string}} opts
 */
export async function createResearchScene(host, opts) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const canvas = renderer.domElement;
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", opts.label);
  canvas.className = "scene-canvas";
  host.appendChild(canvas);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x03060c);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTexture = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = envTexture;
  scene.environmentIntensity = 0.55;
  scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x1a1f2b, 0.55));
  const key = new THREE.DirectionalLight(0xfff4e6, 0.9);
  key.position.set(1.5, 3, -1);
  scene.add(key);

  const gltf = await new GLTFLoader().loadAsync(MODEL_URL);
  const model = gltf.scene;
  model.traverse((o) => {
    if (!o.isMesh) return;
    const m = o.material;
    if (m && m.name === "chamber_glass") {
      m.transparent = true;
      m.opacity = 0.16;
      m.depthWrite = false;
      m.roughness = 0.05;
    }
    if (m && /light_strip|status_|porthole/.test(m.name)) m.toneMapped = true;
  });
  scene.add(model);
  model.updateMatrixWorld(true);
  const anchorNode = model.getObjectByName("FLAME_ANCHOR");
  const anchor = new THREE.Vector3();
  if (anchorNode) anchorNode.getWorldPosition(anchor);

  // --- illustrative flame -------------------------------------------------------------------
  const flame = new THREE.Group();
  flame.position.copy(anchor);
  scene.add(flame);
  const droplet = new THREE.Mesh(
    new THREE.SphereGeometry(0.016, 24, 16),
    new THREE.MeshStandardMaterial({ color: 0x5a3a12, roughness: 0.25, metalness: 0.1, emissive: 0x2a1204 }),
  );
  flame.add(droplet);
  const outerMat = flameMaterial(false);
  const innerMat = flameMaterial(true);
  const outer = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 6), outerMat);
  const inner = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 5), innerMat);
  outer.scale.setScalar(0.075);
  inner.scale.setScalar(0.05);
  flame.add(outer, inner);
  const glow = new THREE.PointLight(0xff8a3d, 0.6, 2.2, 2);
  flame.add(glow);

  // particles (soot/embers, illustrative)
  const pos = new Float32Array(PARTICLES * 3);
  const vel = new Float32Array(PARTICLES * 3);
  const age = new Float32Array(PARTICLES);
  const life = new Float32Array(PARTICLES);
  const alpha = new Float32Array(PARTICLES);
  const pgeo = new THREE.BufferGeometry();
  pgeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  pgeo.setAttribute("aAlpha", new THREE.BufferAttribute(alpha, 1));
  const pmat = particleMaterial();
  pmat.uniforms.uPixel.value = renderer.getPixelRatio();
  const points = new THREE.Points(pgeo, pmat);
  points.frustumCulled = false;
  flame.add(points);
  const spawn = (i, scatter) => {
    const u = Math.random() * 2 - 1;
    const t = Math.random() * Math.PI * 2;
    const s = Math.sqrt(1 - u * u);
    const r = 0.055 + Math.random() * 0.02;
    pos[i * 3] = r * s * Math.cos(t);
    pos[i * 3 + 1] = r * u;
    pos[i * 3 + 2] = r * s * Math.sin(t);
    vel[i * 3] = s * Math.cos(t);
    vel[i * 3 + 1] = u;
    vel[i * 3 + 2] = s * Math.sin(t);
    life[i] = 1.6 + Math.random() * 2.4;
    age[i] = scatter ? Math.random() * life[i] : 0;
  };
  for (let i = 0; i < PARTICLES; i++) spawn(i, true);

  // --- camera and controls --------------------------------------------------------------------
  const camera = new THREE.PerspectiveCamera(48, 1, 0.02, 40);
  const homeOffset = new THREE.Vector3(1.75, 0.28, -1.15);
  const inspectOffset = new THREE.Vector3(0.32, 0.06, -0.5);
  camera.position.copy(anchor).add(homeOffset);
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(anchor);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 0.22;
  controls.maxDistance = 2.4;
  controls.minPolarAngle = Math.PI * 0.18;
  controls.maxPolarAngle = Math.PI * 0.82;
  controls.minAzimuthAngle = Math.PI * 0.56; // stay in front of the rack wall (wraps through pi)
  controls.maxAzimuthAngle = -Math.PI * 0.56;
  controls.enablePan = false;
  controls.autoRotate = !opts.reducedMotion;
  controls.autoRotateSpeed = 0.35;
  controls.update();
  const stopAuto = () => {
    controls.autoRotate = false;
  };
  canvas.addEventListener("pointerdown", stopAuto);
  canvas.addEventListener("wheel", stopAuto, { passive: true });

  let tween = null;
  const flyTo = (offset) => {
    stopAuto();
    const from = camera.position.clone();
    const to = anchor.clone().add(offset);
    if (opts.reducedMotion) {
      camera.position.copy(to);
      controls.update();
      return;
    }
    tween = { from, to, t: 0 };
  };
  const clampToCabin = () => {
    camera.position.x = THREE.MathUtils.clamp(camera.position.x, -CABIN.x, CABIN.x);
    camera.position.y = THREE.MathUtils.clamp(camera.position.y, -CABIN.y, CABIN.y);
    camera.position.z = THREE.MathUtils.clamp(camera.position.z, -CABIN.z, CABIN.z);
  };

  // --- state, look transitions ----------------------------------------------------------------
  let look = flameLook(opts.context, opts.reducedMotion);
  let shown = { ...look };
  let reduced = opts.reducedMotion;
  const applyLook = (l) => {
    for (const m of [outerMat, innerMat]) {
      m.uniforms.uStretch.value = l.stretch;
      m.uniforms.uLum.value = l.luminous;
      m.uniforms.uFlicker.value = l.flicker;
    }
    pmat.uniforms.uLum.value = l.luminous;
    glow.intensity = 0.25 + 1.6 * l.luminous;
    glow.color.setRGB(0.5 + 0.5 * l.luminous, 0.55 + 0.05 * l.luminous, 1.0 - 0.75 * l.luminous);
  };
  applyLook(shown);

  // --- loop with pause when hidden ------------------------------------------------------------
  const clock = new THREE.Clock();
  let raf = 0;
  let visible = true;
  let frames = 0;
  let fpsWindow = { t: performance.now(), n: 0, fps: 0 };
  const resize = () => {
    const w = host.clientWidth || 1;
    const h = host.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  const ro = new ResizeObserver(resize);
  ro.observe(host);
  resize();
  const io = new IntersectionObserver((entries) => {
    visible = entries.some((e) => e.isIntersecting);
    if (visible && !raf) loop();
  });
  io.observe(host);
  const onVisibility = () => {
    if (!document.hidden && visible && !raf) loop();
  };
  document.addEventListener("visibilitychange", onVisibility);

  function step(dt, elapsed) {
    for (const k of ["stretch", "luminous", "rise", "flicker"]) shown[k] += (look[k] - shown[k]) * Math.min(1, dt * 3);
    applyLook(shown);
    outerMat.uniforms.uTime.value = elapsed;
    innerMat.uniforms.uTime.value = elapsed;
    if (!reduced) {
      for (let i = 0; i < PARTICLES; i++) {
        age[i] += dt;
        if (age[i] > life[i]) spawn(i, false);
        const k = i * 3;
        pos[k] += vel[k] * 0.018 * dt;
        pos[k + 1] += (vel[k + 1] * 0.018 + shown.rise * 0.32) * dt;
        pos[k + 2] += vel[k + 2] * 0.018 * dt;
        const f = age[i] / life[i];
        alpha[i] = Math.sin(Math.PI * f) * (0.35 + 0.5 * shown.luminous);
      }
      pgeo.attributes.position.needsUpdate = true;
      pgeo.attributes.aAlpha.needsUpdate = true;
    }
    if (tween) {
      tween.t = Math.min(1, tween.t + dt / 0.9);
      camera.position.lerpVectors(tween.from, tween.to, easeInOut(tween.t));
      if (tween.t >= 1) tween = null;
    }
    controls.update();
    clampToCabin();
  }

  function loop() {
    raf = 0;
    if (!visible || document.hidden) return;
    const dt = Math.min(clock.getDelta(), 0.05);
    step(dt, clock.elapsedTime);
    renderer.render(scene, camera);
    frames += 1;
    fpsWindow.n += 1;
    const now = performance.now();
    if (now - fpsWindow.t >= 1000) {
      fpsWindow = { t: now, n: 0, fps: (fpsWindow.n * 1000) / (now - fpsWindow.t) };
    }
    raf = requestAnimationFrame(loop);
  }
  if (reduced) {
    step(0, 0);
    for (let i = 0; i < PARTICLES; i++) alpha[i] = 0.25 + 0.2 * Math.random();
    pgeo.attributes.aAlpha.needsUpdate = true;
  }
  loop();

  // --- keyboard --------------------------------------------------------------------------------
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
    const action = keyAction(e.key);
    if (!action) return;
    e.preventDefault();
    if (action === "orbit-left") nudge(-0.12, 0, 1);
    else if (action === "orbit-right") nudge(0.12, 0, 1);
    else if (action === "orbit-up") nudge(0, -0.08, 1);
    else if (action === "orbit-down") nudge(0, 0.08, 1);
    else if (action === "zoom-in") nudge(0, 0, 0.88);
    else if (action === "zoom-out") nudge(0, 0, 1.14);
    else if (action === "reset") api.reset();
    else if (action === "inspect") api.inspect();
    else if (action.startsWith("context:") && opts.onContextKey) opts.onContextKey(action.slice(8));
  };
  host.addEventListener("keydown", onKey);

  const api = {
    setContext(id) {
      look = flameLook(id, reduced);
      if (reduced) {
        shown = { ...look };
        applyLook(shown);
        renderer.render(scene, camera);
      }
    },
    setReducedMotion(on) {
      reduced = on;
      controls.autoRotate = !on && controls.autoRotate;
    },
    reset() {
      flyTo(homeOffset);
    },
    inspect() {
      flyTo(inspectOffset);
    },
    stats() {
      return {
        frames,
        fps: Math.round(fpsWindow.fps),
        drawCalls: renderer.info.render.calls,
        triangles: renderer.info.render.triangles,
        pixelRatio: renderer.getPixelRatio(),
        particles: PARTICLES,
        anchorFound: Boolean(anchorNode),
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
      scene.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        const ms = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
        ms.forEach((m) => m.dispose());
      });
      envTexture.dispose();
      pmrem.dispose();
      renderer.dispose();
      canvas.remove();
    },
  };
  return api;
}
