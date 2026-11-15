# Blender illustrative visualization: plan (P2, not evidence)

**Status:** the script was run and its output inspected with **Blender 5.2.4 LTS** (official arm64 build from a blender.org-listed mirror, SHA-256 checked against the published file). It renders four 1280x720 images in about 4 seconds. The script refuses to render an image whose title, disclaimer or assumptions line is missing. The images are illustrations only; they have not been reviewed by Member 5.

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

## Assumptions (also printed on every image)
- **Fuel, oxygen fraction, pressure, ignition source and sample geometry are not modelled.** The scene shows one generic flame so it makes no claim about any specific NASA test.
- **Airflow:** none. The scene is a quiescent ambient. Forced flow, which strongly affects real flames, is not shown.
- **Flame shape:** the height stretch is 1.0 (round) at 0 g rising linearly to 2.6 at 1 g. This is an **artistic mapping, not a model, not validated**, and says nothing about real flame size, spread rate or burning rate.
- Same camera (orthographic, scale 7.0), wick, colours and background in every scene.
- Flame colour is decorative.
- Microgravity flames in real experiments can differ from the round idealisation, depending on flow and conditions. Real behaviour is what the evidence pipeline is for.

## Attribution
When a slide pairs an image with a NASA result, the result is cited from its Finding (with its own sources and limitations), and the image is labelled illustrative. Images never replace or imply a Finding.

## Reproduce
```bash
blender --background --python visualization/gravity_scenes.py -- --out visualization/out
```
Output: `earth.png`, `mars.png`, `moon.png`, `microgravity.png` (git-ignored). Tested with Blender 5.2.4 LTS. `--list` prints the scene table without Blender.

## Open items
1. Review images with Member 5 for any wording that could read as a prediction.
2. Decide whether the images go in the judge demo, and where the caption sits.
