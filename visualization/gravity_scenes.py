"""Illustrative gravity-comparison scenes. NOT a combustion simulation. NOT NASA data. UNTESTED.

    blender --background --python visualization/gravity_scenes.py -- --out visualization/out
    python visualization/gravity_scenes.py --list      # no Blender needed

The buoyancy scale is local gravity divided by Earth gravity and drives only the visual height and
speed of a particle plume. Nothing here is computed from or compared with measurements.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EARTH_G = 9.81
CAPTION = "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data."
SCENES = {  # name: (label, gravity in m/s^2 as a standard reference value)
    "earth": ("Earth, 1 g", EARTH_G),
    "mars": ("Mars, about 0.38 g", 3.71),
    "moon": ("Moon, about 0.165 g", 1.62),
    "microgravity": ("Microgravity (ISS), about 0 g", 0.0),
}


def buoyancy_scale(gravity: float) -> float:
    return gravity / EARTH_G


def build_scene(name: str, out_dir: Path) -> None:
    import bpy  # only available inside Blender

    label, gravity = SCENES[name]
    scale = buoyancy_scale(gravity)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.filepath = str(out_dir / f"{name}.png")

    world = bpy.data.worlds.new("bg")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.03, 1)
    scene.world = world

    # The same generic flame body in every scene; only the plume height changes with `scale`.
    height = 0.4 + 1.6 * scale  # visual design choice, not a model
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(0, 0, 0.35))
    body = bpy.context.active_object
    body.scale = (1.0, 1.0, 0.6 + 0.4 * (height / 2.0) * 2.0)
    mat = bpy.data.materials.new("flame")
    mat.use_nodes = True
    emission = mat.node_tree.nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (1.0, 0.55, 0.15, 1)
    emission.inputs[1].default_value = 6.0
    out = mat.node_tree.nodes["Material Output"]
    mat.node_tree.links.new(emission.outputs[0], out.inputs[0])
    body.data.materials.append(mat)

    bpy.ops.object.camera_add(location=(0, -6, 1.4), rotation=(1.5708, 0, 0))
    scene.camera = bpy.context.active_object

    for text, loc, size in ((label, (-2.8, 0, 3.0), 0.3), (CAPTION, (-2.8, 0, -0.6), 0.16)):
        bpy.ops.object.text_add(location=loc, rotation=(1.5708, 0, 0))
        obj = bpy.context.active_object
        obj.data.body, obj.data.size = text, size

    bpy.ops.render.render(write_still=True)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="visualization/out")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    if args.list:
        for name, (label, g) in SCENES.items():
            print(f"{name:13} {label:32} g={g:5.2f} m/s^2  buoyancy scale {buoyancy_scale(g):.3f}")
        print(CAPTION)
        return 0
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in SCENES:
        build_scene(name, out_dir)
    return 0


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    sys.exit(main(args))
