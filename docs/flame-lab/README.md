# Flame Lab (standalone interactive flame, illustration only)

A single isolated flame on a minimal specimen stage, at `#/flame` in the dashboard. No room, no spacecraft. Original work: nothing is copied from any other project.

**ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data.** The sentence is shown twice on the page (banner and inside the stage), in the canvas's accessible label and in the fallback.

## Controls
| Control | Input | What the drawing does (direction only) |
|---|---|---|
| Ignite / Extinguish | button, `I` or `Space` | spark burst and growth; fade with a smoke puff |
| Gravity | Microgravity, Moon, Mars, Earth presets (reference values) or a 0 to 1 g slider; keys `1` to `4` | more gravity, more upward stretch, faster rising particles |
| Oxygen | 15 to 40 % of the surrounding gas (the viewer's input) | more oxygen, brighter and larger; extinction limits are **not** modelled |
| Forced airflow | still to strong | leans and stretches the flame downstream; particles drift |
| Fuel look | low-soot droplet, sooty droplet, solid sample (generic looks, not real fuels) | sootier looks glow warmer and smoke more |
| View | drag or arrow keys to orbit, wheel / pinch or `+` `-` to zoom, `R` to reset | |

## Scientific rules (enforced by tests)
- `frontend/static/js/flame/params.js` maps inputs to unitless drawing parameters only. It outputs no temperature, burning rate, spread rate, extinction limit, probability, risk or suppression value, and the page shows none.
- The explanations use only the viewer's own inputs as numbers; a test bans predictive wording and unexpected numbers for every input combination.
- The evidence link is worded from what is actually loaded ("No NASA evidence registered yet", "Fixture data, not NASA data", or the real counts). The Flame Lab never reads or shows Findings.
- Fuels are generic looks; a test forbids naming a real fuel.

## Accessibility and fallbacks
Keyboard control of the scene, labelled form controls, `prefers-reduced-motion` (a still frame that redraws on change) plus a Pause motion button, and a non-WebGL fallback (`?scene=off` forces it) in which the controls and explanations still work. The lab is always dark, whatever the page theme.

## Technology
Vanilla ES modules, no build step and no CDN (works offline). three.js 0.170.0 (MIT) is vendored unmodified with hashes in `frontend/static/vendor/three/VENDOR.txt` (npm integrity verified) and is loaded lazily, only when the Flame Lab opens: about 760 KB that no other page pays for.

## Run it
With the B7 backend (PR #32) and this frontend:
```bash
python -m flameguard serve --auto-port --open      # then open  #/flame
```
Or with the development preview (PR #19/#33), from a checkout that has `preview/`:
```bash
python preview/run.py --frontend-ref origin/feat/visual-research-scene --port 8791
# http://127.0.0.1:8791/#/flame
```

## Measured (headless Chrome, software WebGL: not representative of a real GPU)
31 draw calls, about 13,000 triangles and 890 particles per frame; no console errors; no horizontal overflow at 1440x900 or 390x844. Frame rate on real graphics hardware has not been measured.

## Screenshots (real application, served by the B7 backend)
`desktop-microgravity.png`, `desktop-earth-sooty-airflow.png`, `desktop-mars-solid.png`, `mobile-earth.png`, `desktop-fallback.png`.
