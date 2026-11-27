# SPDX-License-Identifier: GPL-3.0-or-later
"""Render presets one by one (Cycles, CPU) for visual checks and before/after comparisons.

    python tests/render_preview.py --out reports/_artifacts/<run> --presets HEDGE_COTONEASTER:CUBE,PICEA_ABIES
    python tests/render_preview.py --out <dir> --presets ALL --samples 32 --res 640
    python tests/render_preview.py --out <dir> --presets HEDGE_COTONEASTER:CUBE --zoom 2.5   # close-up
    python tests/render_preview.py --out <dir> --presets PICEA_ABIES --set "Height=18,Card Size=0.4"

PRESET[:FORM] — the form is for clipped shrubs. Files: <out>/<PRESET>[_<FORM>][_z<zoom>].png and
<out>/renders.json (preset, form, seed, tris, seconds). Same seed (default 3) = same tree.
"""
import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _boot  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402


def scene_setup(res, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.transparent_max_bounces = 32
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new("EC preview") if sc.world is None else sc.world
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
    bg.inputs["Strength"].default_value = 0.6
    ground = bpy.data.objects.get("EC ground")
    if ground is None:
        me = bpy.data.meshes.new("EC ground")
        s = 200
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        ground = bpy.data.objects.new("EC ground", me)
        sc.collection.objects.link(ground)
        mat = bpy.data.materials.new("EC ground")
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.34, 0.3, 1)
        me.materials.append(mat)
    if bpy.data.objects.get("EC sun") is None:
        sun = bpy.data.objects.new("EC sun", bpy.data.lights.new("EC sun", 'SUN'))
        sun.data.energy = 4.0
        sun.data.angle = math.radians(2)
        sun.rotation_euler = (math.radians(50), 0, math.radians(35))
        sc.collection.objects.link(sun)
    cam = bpy.data.objects.get("EC camera")
    if cam is None:
        cam = bpy.data.objects.new("EC camera", bpy.data.cameras.new("EC camera"))
        cam.data.lens = 50
        sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def frame(cam, obj, zoom):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for inst in dg.object_instances:
        parent = inst.parent.original if inst.is_instance and inst.parent else inst.object.original
        if parent == obj:
            pts += [inst.matrix_world @ Vector(c) for c in inst.object.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    centre, size = (lo + hi) / 2, (hi - lo).length
    d = Vector((1.0, -1.25, 0.55)).normalized()
    dist = size * 1.25 / zoom
    target = centre if zoom <= 1 else Vector((centre.x, centre.y, lo.z + (hi.z - lo.z) * 0.6))
    cam.location = target + d * dist
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--presets", default="HEDGE_COTONEASTER:CUBE")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--res", type=int, default=800)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--set", default="", help='parameter overrides "Name=value,Name=value"')
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    ec = _boot.load_addon()
    cam = scene_setup(args.res, args.samples)
    params = {}
    for kv in filter(None, args.set.split(",")):
        k, v = kv.split("=", 1)
        params[k.strip()] = float(v)
    items = args.presets.split(",")
    if items == ["ALL"]:
        items = [p["key"] + (":CUBE" if p["kind"] == "HEDGE" else "") for p in ec.presets_list()]
    os.makedirs(args.out, exist_ok=True)
    log = []
    for item in items:
        key, _, form = item.partition(":")
        t = time.time()
        r = ec.add(key, (0, 0, 0), seed=args.seed, form=form or None, params=params or None)
        obj = bpy.data.objects[r["name"]]
        frame(cam, obj, args.zoom)
        fn = key + ("_" + form if form else "") + ("_z%g" % args.zoom if args.zoom != 1 else "") + ".png"
        bpy.context.scene.render.filepath = os.path.join(args.out, fn)
        bpy.ops.render.render(write_still=True)
        row = dict(preset=key, form=form, seed=args.seed, tris=ec.tri_count(obj), file=fn,
                   seconds=round(time.time() - t, 1), params=params)
        log.append(row)
        print("rendered", row)
        ec.delete(obj.name)
    _boot.write_json(os.path.join(args.out, "renders.json"), log)


if __name__ == "__main__":
    main()
