# Blender illustrative visualization: plan (P2, not evidence)

**Status:** plan and an UNTESTED scene script. Blender was not installed on the development machine when this was written, so nothing here has been rendered.

## What this is, and is not

These images **illustrate** how gravity changes buoyancy-driven flow around a flame. They are **not** combustion simulations and **not** validated. No NASA measurement is used, none is shown, and no number in any image comes from a Finding. They are kept apart from the evidence pipeline: no code in `backend/`, `frontend/` or `data/` reads from or writes to `visualization/`.

Every render carries this caption, baked into the image: **"ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data."**

## Scenes (same camera, same scale, same colour map)

| Scene | Gravity | Buoyancy scale (illustrative) | What the picture is meant to convey |
|---|---|---|---|
| Earth | 1 g (9.81 m/s²) | 1.00 | Hot gas rises quickly; flame is elongated and drawn upward |
| Mars | about 0.38 g | 0.38 | Weaker buoyancy; flame less elongated |
| Moon | about 0.165 g | 0.165 | Weaker still |
| Microgravity (ISS) | about 0 g | 0 | No buoyant plume; flame tends toward a rounder shape; flow is driven by diffusion and any forced airflow |

Gravity values are standard reference values for the bodies. The buoyancy scale is the ratio of local gravity to Earth gravity and is applied only as a **visual** parameter (plume height and velocity of a particle system). The mapping from that ratio to flame size or shape is a **qualitative design choice, not a measured or computed relationship.**

## Assumptions to state on the image or in the caption
- Fuel, oxidiser fraction, pressure, ignition source and sample geometry are **not modelled**; the scene shows a generic small flame so it can make no claim about any specific NASA test.
- Flame colour is decorative.
- Microgravity flames in real experiments can differ from the round idealisation, depending on flow and conditions. Real behaviour is what the evidence pipeline is for.

## Attribution
When a slide pairs an image with a NASA result, the result is cited from its Finding (with its own sources and limitations), and the image is labelled illustrative. Images never replace or imply a Finding.

## Reproduce
```bash
blender --background --python visualization/gravity_scenes.py -- --out visualization/out
```
Output: `earth.png`, `mars.png`, `moon.png`, `microgravity.png` (git-ignored). Needs Blender 3.6 or newer. `--list` prints the scene table without Blender.

## Open items
1. Install Blender (or `pip install bpy` for Python 3.11) and render; review images with Member 5 for any wording that could read as a prediction.
2. Decide whether the images go in the judge demo, and where the caption sits.
