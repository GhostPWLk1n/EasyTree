# SPDX-License-Identifier: GPL-3.0-or-later
"""Check every function of the MCP / scripting API (api.py) headless.

    python tests/test_api.py            (bpy module)
    blender -b --factory-startup --python tests/test_api.py

Prints PASS|FAIL <check> — details; exit code 1 on any FAIL.
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _boot  # noqa: E402
import bpy  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
ec = _boot.load_addon()
failed = 0


def _expect_error(fn):
    """True if fn raises ValueError (a readable API error), False if it silently succeeds."""
    try:
        fn()
    except ValueError as e:
        return "error: %s" % e
    return False


def check(name, fn, cond=lambda r: True):
    global failed
    try:
        r = fn()
        ok = bool(cond(r))
        detail = str(r)[:160]
    except Exception as e:  # noqa: BLE001
        ok, detail = False, "%s: %s\n%s" % (type(e).__name__, e, traceback.format_exc(limit=3))
        r = None
    failed += not ok
    print("%s  %s — %s" % ("PASS" if ok else "FAIL", name, detail))
    return r


check("help", ec.help, lambda r: "add_hedge" in r)
check("version", ec.version, lambda r: r["api"] >= 1)
check("presets_list", ec.presets_list, lambda r: len(r) > 20)
check("presets_list HEDGE", lambda: ec.presets_list("HEDGE"), lambda r: r and all(p["kind"] == "HEDGE" for p in r))
check("forms", ec.forms, lambda r: {f["key"] for f in r} >= {"BALL", "CUBE", "TRAPEZOID", "NATURAL"})
check("parameter_names", lambda: ec.parameter_names("HEDGE"), lambda r: "Shape" in r)

spruce = check("add conifer", lambda: ec.add("PICEA_ABIES", (0, 0, 0), seed=1, params={"Height": 10}),
               lambda r: r["kind"] == "CONIFER")
check("parameters", lambda: ec.parameters(spruce["name"]), lambda r: abs(r["Height"] - 10) < 1e-4)
check("info", lambda: ec.info(spruce["name"]), lambda r: r["tris"] > 1000 and not r["warnings"])
check("set_params", lambda: ec.set_params(spruce["name"], Height=14),
      lambda r: abs(ec.parameters(spruce["name"])["Height"] - 14) < 1e-4)
check("set_params unknown -> error", lambda: _expect_error(lambda: ec.set_params(spruce["name"], Nope=1)), bool)
check("new_seed", lambda: ec.new_seed(spruce["name"], 77), lambda r: r[spruce["name"]] == 77)
check("apply_preset same kind", lambda: ec.apply_preset(spruce["name"], "ABIES"),
      lambda r: r["updated"] == [spruce["name"]] and ec.parameters(spruce["name"])["Seed"] == 77)
check("apply_preset other kind skipped", lambda: ec.apply_preset(spruce["name"], "TILIA_CORDATA"),
      lambda r: r["skipped_other_kind"] == [spruce["name"]])

birch = check("add broadleaf", lambda: ec.add("BETULA_PENDULA", (10, 0, 0), seed=2), lambda r: r["kind"] == "BROADLEAF")
ball = check("add hedge form", lambda: ec.add("HEDGE_COTONEASTER", (0, 10, 0), seed=3, form="BALL"),
             lambda r: r["kind"] == "HEDGE")
check("apply_form keep_size", lambda: ec.apply_form(ball["name"], "CUBE", keep_size=True),
      lambda r: r["updated"] == [ball["name"]])
check("hedge tris <= 5000", lambda: ec.info(ball["name"]), lambda r: 0 < r["tris"] <= 5000)
hedge = check("add_hedge 10 m", lambda: ec.add_hedge("HEDGE_PHYSOCARPUS", (0, 20), (10, 20), height=1.2, seed=4),
              lambda r: abs(ec.parameters(r["name"])["Width"] - 10) < 1e-3)
check("add_hedge rotation", lambda: ec.info(hedge["name"]), lambda r: abs(r["rotation_z"]) < 0.01)
check("add_row", lambda: ec.add_row("HEDGE_PHYSO_DIABOLO", (0, 30), (6, 30), 2.0, seed=5, form="BALL"),
      lambda r: r["count"] == 4)
check("add_many", lambda: ec.add_many("BETULA_YOUNG", [(20, 0), (24, 3)], seed=6, scale_jitter=0.1),
      lambda r: r["count"] == 2)
check("form on tree -> error", lambda: _expect_error(lambda: ec.add("PICEA_ABIES", form="BALL")), bool)
check("unknown preset -> error", lambda: _expect_error(lambda: ec.add("NOPE")), bool)
check("scene_info", lambda: ec.scene_info(with_tris=True), lambda r: r["count"] == 10 and r["tris_total"] > 0)
check("foliage_visible", lambda: ec.foliage_visible(False), lambda r: len(r["updated"]) == 10)
check("realize", lambda: ec.realize(ball["name"]), lambda r: 0 < r[ball["name"]] <= 5000)
check("realized is plain mesh", lambda: bpy.data.objects[ball["name"]].modifiers.keys(), lambda r: len(r) == 0)
check("rebuild", ec.rebuild, lambda r: "FINISHED" in r["result"])
check("delete", lambda: ec.delete([birch["name"]]), lambda r: birch["name"] not in bpy.data.objects)
check("bake_species", ec.bake_species, lambda r: "SPRUCE" in r)
check("frame (background)", ec.frame, lambda r: "framed" in r)
if "--bake" in sys.argv:
    check("bake 256", lambda: ec.bake("COTONEASTER_HEDGE", resolution=256), lambda r: "COTONEASTER_HEDGE" in r["seconds"])
    check("reset_textures", ec.reset_textures, lambda r: "FINISHED" in r["result"])

print("\n%s" % ("all passed" if not failed else "%d failed" % failed))
sys.exit(1 if failed else 0)

