"""Illustrative gravity-comparison scenes. NOT a combustion simulation. NOT NASA data. UNTESTED.

    blender --background --python visualization/gravity_scenes.py -- --out visualization/out
    python visualization/gravity_scenes.py --list      # no Blender needed

The buoyancy scale is local gravity divided by Earth gravity and drives only the visual height and
speed of a particle plume. Nothing here is computed from or compared with measurements.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

EARTH_G = 9.81
CAPTION = "ILLUSTRATION ONLY. Not a validated combustion simulation. Not NASA data."
ASSUMPTIONS = (
    "Fuel, oxygen fraction, pressure and airflow are not modelled. "
    "Flame shape is an artistic choice."
)
SCENES = {  # name: (label, gravity in m/s^2 as a standard reference value)
    "earth": ("Earth, 1 g", EARTH_G),
    "mars": ("Mars, about 0.38 g", 3.71),
    "moon": ("Moon, about 0.165 g", 1.62),
    "microgravity": ("Microgravity (ISS), about 0 g", 0.0),
}


def buoyancy_scale(gravity: float) -> float:
    return gravity / EARTH_G


def _emissive(bpy, name: str, color: tuple, strength: float):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True  # deprecated in Blender 6.0; revisit then
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*color, 1.0)
    emission.inputs[1].default_value = strength
    links.new(emission.outputs[0], nodes["Material Output"].inputs[0])
    return mat


def _text(bpy, body: str, z: float, size: float, color=(1, 1, 1), strength=1.0) -> None:
    bpy.ops.object.text_add(location=(0, 0, z), rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.active_object
    obj.data.body, obj.data.size, obj.data.align_x = body, size, "CENTER"
    obj.data.materials.append(_emissive(bpy, "label", color, strength))


def build_scene(name: str, out_dir: Path) -> None:
    import bpy  # only available inside Blender

    label, gravity = SCENES[name]
    scale = buoyancy_scale(gravity)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.filepath = str(out_dir / f"{name}.png")
    scene.view_settings.view_transform = "Standard"  # no tone mapping: colours as authored
    scene.world = bpy.data.worlds.new("bg")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.04, 1)

    # Identical in every scene: wick, camera, framing, lighting-free emissive materials.
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.5, location=(0, 0, 0.25))
    bpy.context.active_object.data.materials.append(_emissive(bpy, "wick", (0.5, 0.5, 0.55), 0.8))

    # Only the flame's height stretch changes with `scale`: 1.0 (round) at 0 g to 2.6 at 1 g.
    # This is an artistic mapping, not a model, and says nothing about real flame size.
    stretch = 1.0 + 1.6 * scale
    radius = 0.4
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24)
    flame = bpy.context.active_object
    flame.scale = (1.0, 1.0, stretch)
    flame.location = (0, 0, 0.5 + radius * stretch)
    bpy.ops.object.shade_smooth()
    flame.data.materials.append(_emissive(bpy, "flame", (1.0, 0.3, 0.02), 1.0))

    bpy.ops.object.camera_add(location=(0, -10, 1.45), rotation=(math.pi / 2, 0, 0))
    cam = bpy.context.active_object
    cam.data.type, cam.data.ortho_scale = "ORTHO", 7.0  # same scale in every scene
    scene.camera = cam

    _text(bpy, label, 3.0, 0.32)
    _text(bpy, CAPTION, -0.24, 0.14, color=(1.0, 0.85, 0.4))
    _text(bpy, ASSUMPTIONS, -0.45, 0.095, color=(0.8, 0.8, 0.8))
    bodies = {o.data.body for o in scene.objects if o.type == "FONT"}
    if bodies != {label, CAPTION, ASSUMPTIONS}:  # never render an image without its disclaimer
        raise RuntimeError(f"{name}: caption objects missing or altered: {sorted(bodies)}")
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
