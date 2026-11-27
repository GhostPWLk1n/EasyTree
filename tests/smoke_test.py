# SPDX-License-Identifier: GPL-3.0-or-later
"""Smoke test for Easy Conifer: runs headless with the `bpy` module (pip install bpy==5.2.*).

    python tests/smoke_test.py                 # every preset (+ every form for clipped shrubs)
    python tests/smoke_test.py --quick         # one preset per generator
    python tests/smoke_test.py --bake          # also bake one small atlas into a temp folder
    python tests/smoke_test.py --json out.json # write the results table as JSON

Exit code 0 — all checks passed, 1 — at least one FAIL. Prints one line per case.
"""
import argparse
import json
import os
import sys
import tempfile
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _boot  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Triangle budgets (whole object, instances realised). Over budget = FAIL.
BUDGET = {"HEDGE": 5000, "BROADLEAF": 150000, "CONIFER": 60000}  # README numbers + margin


def tri_count(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for inst in dg.object_instances:
        src = inst.object           # for instances: the evaluated instance geometry
        parent = inst.parent.original if inst.is_instance and inst.parent else inst.object.original
        if parent != obj or src.type != 'MESH':
            continue
        me = src.to_mesh()
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        src.to_mesh_clear()
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--preset", help="comma-separated preset keys to test")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    ec = _boot.load_addon()
    from easy_conifer import presets, operators
    print("Blender", bpy.app.version_string, "| Easy Conifer", ec.version()["addon"])

    keys = [k for k, *_ in presets.ALL_ENUM_ITEMS if k]
    if args.quick:
        keys = ["PICEA_ABIES", next(k for k in keys if presets.is_broadleaf(k) and not presets.is_hedge(k)),
                next(k for k in keys if presets.is_hedge(k))]
    if args.preset:
        keys = args.preset.split(",")
    forms = [k for k, *_ in presets.SHRUB_FORM_ITEMS]

    results, failed = [], 0
    sc = bpy.context.scene
    for key in keys:
        for form in (forms if presets.is_hedge(key) else [None]):
            sc.easy_conifer_preset = key
            if form:
                sc.easy_conifer_shrub_form = form
            t = time.time()
            try:
                r = bpy.ops.object.easy_conifer_add(preset=key, seed=3)
                obj = bpy.context.active_object
                mod = operators.conifer_modifier(obj)
                kind = operators.group_kind(mod.node_group)
                warns = [w.message for w in mod.node_warnings]
                tris = tri_count(obj)
                ok = r == {'FINISHED'} and not warns and 0 < tris <= BUDGET[kind]
                note = "; ".join(warns) or ("" if tris <= BUDGET[kind] else f"over budget {BUDGET[kind]}")
                obj.location.x += 3 * len(results)
            except Exception as e:  # noqa: BLE001 — any error is a FAIL line, not a crash
                kind, tris, ok, note = "?", 0, False, f"{type(e).__name__}: {e}"
            failed += not ok
            row = dict(preset=key, form=form or "", kind=kind, tris=tris, ok=ok, note=note,
                       seconds=round(time.time() - t, 2))
            results.append(row)
            print(f"{'PASS' if ok else 'FAIL'}  {key:22s} {form or '':10s} {kind:9s} tris={tris:<7d} {note}")

    # operators on the last object
    for name, call in (("new_seed", lambda: bpy.ops.object.easy_conifer_new_seed()),
                       ("apply_preset", lambda: bpy.ops.object.easy_conifer_apply_preset()),
                       ("needles_hide", lambda: bpy.ops.object.easy_conifer_needles_visibility(show=False)),
                       ("needles_show", lambda: bpy.ops.object.easy_conifer_needles_visibility(show=True)),
                       ("rebuild", lambda: bpy.ops.object.easy_conifer_rebuild())):
        try:
            ok = call() == {'FINISHED'}
            note = ""
        except Exception as e:  # noqa: BLE001
            ok, note = False, f"{type(e).__name__}: {e}"
        failed += not ok
        results.append(dict(preset="(operator)", form=name, kind="", tris=0, ok=ok, note=note, seconds=0))
        print(f"{'PASS' if ok else 'FAIL'}  operator {name} {note}")

    if args.bake:
        from easy_conifer import twig_baker
        out = tempfile.mkdtemp(prefix="ec_bake_")
        t = time.time()
        try:
            twig_baker.bake_atlas("COTONEASTER_HEDGE", out, resolution=256, samples=4, report=lambda *a: None)
            files = sorted(os.listdir(out))
            ok = all(f"cotoneaster_hedge_{m}.png" in files for m in ("albedo", "normal", "mask"))
            note = ", ".join(files)
        except Exception as e:  # noqa: BLE001
            ok, note = False, f"{type(e).__name__}: {e}"
        failed += not ok
        results.append(dict(preset="(bake)", form="COTONEASTER_HEDGE", kind="", tris=0, ok=ok, note=note,
                            seconds=round(time.time() - t, 1)))
        print(f"{'PASS' if ok else 'FAIL'}  bake 256px {time.time() - t:.0f}s {note}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(dict(blender=bpy.app.version_string, failed=failed, results=results), f,
                      ensure_ascii=False, indent=1)
    print(f"\n{len(results) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
