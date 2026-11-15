"""Build FlameGuard-SI's ORIGINAL ISS-style research module in Blender and export it for the browser.

    blender --background --factory-startup --python tools/visual/build_research_module.py -- \
        --glb frontend/static/models/research-module.glb --poster frontend/static/img/research-module-poster.jpg

Everything is generated procedurally from primitives here; no external model, texture or asset is
used. The geometry is a generic pressurised-module interior (rack walls, handrails, light strips,
hatches) with a combustion research rack and a viewing chamber. It is an illustration, not a
replica of any real module, and carries no scientific data. The flame itself is drawn in the
browser (frontend/static/js/scene/), anchored to the empty named FLAME_ANCHOR exported here.

Coordinates (glTF, Y up): the module runs along X from -4.6 to 4.6 m, the cabin is about 2.1 m
square, the combustion chamber window faces +Z at the centre of the -Z wall.
"""

from __future__ import annotations

import math
import sys

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


HALF = 1.05  # half width of the square cabin cross-section (m)
LENGTH = 9.2
RACK = 1.0  # rack bay width along X


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, metal=0.0, rough=0.5, emit=None, emit_strength=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    return m


M = {}


def materials():
    M["panel"] = mat("panel_offwhite", (0.80, 0.82, 0.85), rough=0.55)
    M["panel_dark"] = mat("panel_grey", (0.42, 0.45, 0.50), rough=0.6)
    M["frame"] = mat("frame_metal", (0.55, 0.58, 0.62), metal=0.85, rough=0.35)
    M["rail"] = mat("handrail_blue", (0.16, 0.36, 0.62), metal=0.3, rough=0.35)
    M["light"] = mat("light_strip", (1.0, 0.97, 0.9), emit=(1.0, 0.95, 0.86), emit_strength=6.0)
    M["status_g"] = mat("status_green", (0.1, 0.8, 0.4), emit=(0.1, 0.9, 0.45), emit_strength=3.0)
    M["status_a"] = mat("status_amber", (1.0, 0.6, 0.1), emit=(1.0, 0.55, 0.1), emit_strength=3.0)
    M["chamber"] = mat("chamber_steel", (0.30, 0.32, 0.35), metal=0.9, rough=0.28)
    M["glass"] = mat("chamber_glass", (0.55, 0.75, 0.9), metal=0.0, rough=0.05, alpha=0.18)
    M["cable"] = mat("cable_black", (0.05, 0.05, 0.06), rough=0.7)
    M["label"] = mat("label_orange", (0.95, 0.42, 0.12), rough=0.5)
    M["hatch"] = mat("hatch_metal", (0.62, 0.64, 0.67), metal=0.9, rough=0.3)
    M["porthole"] = mat("porthole_space", (0.0, 0.01, 0.03), emit=(0.02, 0.05, 0.12), emit_strength=0.6)


def box(name, size, loc, material, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width, b.segments = bevel, 2
    o.data.materials.append(material)
    return o


def cyl(name, radius, depth, loc, material, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o


def torus(name, major, minor, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc, rotation=rot, major_segments=48, minor_segments=12)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o


# Blender is Z-up; the glTF exporter converts to Y-up. Build with X along the module,
# Blender Z = up (glTF Y), Blender -Y = glTF +Z (towards the viewer of the chamber wall).


def rack_wall(axis, sign):
    """A wall of rack bays. axis: 'side' (Blender Y walls) or 'deck' (Blender Z walls)."""
    bays = int(LENGTH / RACK) - 1
    for i in range(bays):
        x = -LENGTH / 2 + RACK * (i + 1)
        if axis == "side":
            y = sign * HALF
            box(f"rack_{sign}_{i}", (RACK * 0.94, 0.06, HALF * 1.86), (x, y, 0), M["panel"], bevel=0.015)
            # recessed sub-panels and knobs give scale and detail
            for k, z in enumerate((-0.55, 0.0, 0.55)):
                box(f"sub_{sign}_{i}_{k}", (RACK * 0.78, 0.02, 0.42), (x, y - sign * 0.04, z), M["panel_dark"] if (i + k) % 3 == 0 else M["panel"], bevel=0.008)
                if (i * 3 + k) % 4 == 0:
                    box(f"led_{sign}_{i}_{k}", (0.04, 0.012, 0.02), (x + 0.3, y - sign * 0.055, z + 0.15), M["status_g"] if k != 1 else M["status_a"])
            cyl(f"rail_{sign}_{i}", 0.018, RACK * 0.8, (x, y - sign * 0.16, -0.78), M["rail"], rot=(0, math.pi / 2, 0), verts=12)
        else:
            z = sign * HALF
            box(f"deck_{sign}_{i}", (RACK * 0.94, HALF * 1.86, 0.06), (x, 0, z), M["panel"] if sign < 0 else M["panel_dark"], bevel=0.015)
            if sign > 0:  # overhead light strips
                box(f"light_{i}", (RACK * 0.7, 0.22, 0.02), (x, 0, z - 0.045), M["light"])
            else:
                for yy in (-0.6, 0.6):
                    cyl(f"floorrail_{i}_{yy}", 0.016, RACK * 0.8, (x, yy, z + 0.14), M["rail"], rot=(0, math.pi / 2, 0), verts=12)


def corners():
    for sy in (-1, 1):
        for sz in (-1, 1):
            box(f"standoff_{sy}_{sz}", (LENGTH, 0.14, 0.14), (0, sy * (HALF - 0.05), sz * (HALF - 0.05)), M["frame"], bevel=0.02)
            cyl(f"cable_{sy}_{sz}", 0.022, LENGTH, (0, sy * (HALF - 0.16), sz * (HALF - 0.12)), M["cable"], rot=(0, math.pi / 2, 0), verts=10)


def hatches():
    for s in (-1, 1):
        x = s * LENGTH / 2
        box(f"bulkhead_{s}", (0.08, HALF * 2.2, HALF * 2.2), (x, 0, 0), M["frame"])
        torus(f"hatch_ring_{s}", 0.62, 0.05, (x - s * 0.06, 0, 0), M["hatch"], rot=(0, math.pi / 2, 0))
        cyl(f"hatch_door_{s}", 0.58, 0.05, (x - s * 0.05, 0, 0), M["hatch"], rot=(0, math.pi / 2, 0), verts=48)
        cyl(f"hatch_window_{s}", 0.16, 0.06, (x - s * 0.08, 0, 0.12), M["porthole"], rot=(0, math.pi / 2, 0), verts=32)
        for k in range(8):
            a = k * math.pi / 4
            cyl(f"latch_{s}_{k}", 0.03, 0.08, (x - s * 0.09, 0.66 * math.cos(a), 0.66 * math.sin(a)), M["frame"], rot=(0, math.pi / 2, 0), verts=10)


def combustion_rack():
    """The research rack: a deeper rack on the -Y wall with a cylindrical chamber and a window."""
    y = -HALF + 0.22
    box("combustion_rack", (RACK * 1.9, 0.44, HALF * 1.9), (0, y, 0), M["panel_dark"], bevel=0.02)
    box("combustion_rack_label", (0.5, 0.01, 0.08), (-0.55, y + 0.225, 0.78), M["label"])
    # chamber: a steel cylinder whose axis faces the cabin, with a viewing window
    cyl("chamber_body", 0.42, 0.34, (0, y + 0.2, 0.08), M["chamber"], rot=(math.pi / 2, 0, 0), verts=48)
    torus("chamber_flange", 0.44, 0.035, (0, y + 0.38, 0.08), M["frame"], rot=(math.pi / 2, 0, 0))
    cyl("chamber_window", 0.36, 0.01, (0, y + 0.385, 0.08), M["glass"], rot=(math.pi / 2, 0, 0), verts=48)
    for k in range(12):
        a = k * math.pi / 6
        cyl(f"bolt_{k}", 0.012, 0.03, (0.44 * math.cos(a), y + 0.4, 0.08 + 0.44 * math.sin(a)), M["frame"], rot=(math.pi / 2, 0, 0), verts=8)
    # interior back plate and a fuel-deployment needle pair (generic), plus side instruments
    cyl("chamber_backplate", 0.38, 0.01, (0, y + 0.06, 0.08), M["panel_dark"], rot=(math.pi / 2, 0, 0), verts=48)
    for s in (-1, 1):
        cyl(f"needle_{s}", 0.004, 0.22, (s * 0.13, y + 0.22, 0.08), M["frame"], rot=(0, math.pi / 2, 0), verts=8)
    for k, z in enumerate((-0.62, 0.62)):
        box(f"instrument_{k}", (0.7, 0.08, 0.3), (0.55, y + 0.25, z), M["panel"], bevel=0.01)
        box(f"instrument_screen_{k}", (0.4, 0.01, 0.16), (0.55, y + 0.295, z), M["porthole"])
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, y + 0.22, 0.08))
    bpy.context.active_object.name = "FLAME_ANCHOR"


def stage_for_render():
    bpy.ops.object.camera_add(location=(2.6, 0.75, 0.25))
    cam = bpy.context.active_object
    cam.data.lens = 18
    direction = (0 - 2.6, -0.72 - 0.75, 0.08 - 0.25)
    cam.rotation_mode = "QUATERNION"
    from mathutils import Vector

    cam.rotation_quaternion = Vector(direction).to_track_quat("-Z", "Y")
    bpy.context.scene.camera = cam
    bpy.ops.object.light_add(type="AREA", location=(0, 0, HALF - 0.1))
    light = bpy.context.active_object
    light.data.energy, light.data.size = 900, 6
    bpy.ops.object.light_add(type="POINT", location=(0, -0.45, 0.08))
    flame = bpy.context.active_object
    flame.data.energy, flame.data.color = 60, (1.0, 0.55, 0.2)
    flame.name = "poster_flame_light_only"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0, -0.62, 0.08))
    glow = bpy.context.active_object
    glow.name = "poster_flame_only"
    glow.data.materials.append(mat("poster_flame", (1, 0.6, 0.2), emit=(1.0, 0.55, 0.15), emit_strength=25))
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.02, 1)
    bpy.context.scene.world = world


def main():
    reset()
    materials()
    for s in (-1, 1):
        rack_wall("side", s)
        rack_wall("deck", s)
    corners()
    hatches()
    combustion_rack()
    glb = arg("--glb")
    if glb:
        bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", export_apply=True, export_yup=True, export_extras=False, export_lights=False, export_cameras=False)
    poster = arg("--poster")
    if poster:
        stage_for_render()
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = 1600, 900
        scene.render.image_settings.file_format = "JPEG"
        scene.render.image_settings.quality = 82
        scene.view_settings.view_transform = "AgX" if "AgX" in [v.identifier for v in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
        scene.render.filepath = poster
        bpy.ops.render.render(write_still=True)


main()
