# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — scripting / MCP API. Copyright (C) 2026 Pavel Fomin
"""Easy Conifer API for scripts and AI agents (Blender MCP).

    import bpy, json
    ec = bpy.app.driver_namespace["easy_conifer_api"]
    print(ec.help())

Every function works without a 3D view or a mouse and returns plain dict / list / str values
(JSON-friendly). Objects are addressed by name; where a function takes `names`, a single name,
a list of names or None (= every Easy Conifer object in the scene) is accepted.
Units: metres, degrees. Errors are raised as ValueError with a readable message.
"""
import math
import random

import bpy
from mathutils import Vector

from . import presets, twig_baker, materials, nodes_builder, operators as ops
from .modifier_io import get_input, set_input

API_VERSION = 1


# ---------------------------------------------------------------- helpers
def _version():
    import os
    try:
        import tomllib
        with open(os.path.join(os.path.dirname(__file__), "blender_manifest.toml"), "rb") as f:
            return tomllib.load(f).get("version", "?")
    except Exception:
        return "?"


def _plain(v):
    """Socket value -> JSON-friendly value."""
    if isinstance(v, bpy.types.ID):
        return v.name
    if v is None or isinstance(v, (bool, int, float, str)):
        return round(v, 5) if isinstance(v, float) else v
    try:
        return [round(float(x), 5) for x in v]
    except TypeError:
        return str(v)


def _kind_of_key(key):
    if not key:
        raise ValueError("preset key is empty")
    if key not in _all_keys():
        raise ValueError("unknown preset %r; see presets()" % key)
    return ops.preset_kind(key)


def _all_keys():
    return [k for k, *_ in presets.ALL_ENUM_ITEMS if k]


def _obj(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise ValueError("no object named %r" % name)
    if ops.conifer_modifier(obj) is None:
        raise ValueError("%r is not an Easy Conifer object" % name)
    return obj


def _objs(names):
    if names is None:
        return [o for o in bpy.context.scene.objects if ops.conifer_modifier(o)]
    if isinstance(names, str):
        names = [names]
    return [_obj(n) for n in names]


def _set_values(mod, values):
    """Set inputs by their UI names. Unknown names -> ValueError listing valid ones."""
    ids = ops._ids(mod)
    bad = [k for k in values if k not in ids]
    if bad:
        raise ValueError("unknown parameter(s) %s; valid: %s" % (bad, sorted(ids)))
    for k, v in values.items():
        if isinstance(v, str) and k.endswith("Material"):
            mat = bpy.data.materials.get(v)
            if mat is None:
                raise ValueError("no material named %r" % v)
            v = mat
        set_input(mod, ids[k], v)


def _bounces(minimum=32):
    cyc = getattr(bpy.context.scene, "cycles", None)
    if cyc is not None and cyc.transparent_max_bounces < minimum:
        cyc.transparent_max_bounces = minimum


def tri_count(obj):
    """Triangles of the evaluated object, instances included."""
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for inst in dg.object_instances:
        parent = inst.parent.original if inst.is_instance and inst.parent else inst.object.original
        src = inst.object
        if parent != obj or src.type != 'MESH':
            continue
        me = src.to_mesh()
        me.calc_loop_triangles()
        total += len(me.loop_triangles)
        src.to_mesh_clear()
    return total


# ---------------------------------------------------------------- reference
def help():  # noqa: A001 — mirrors the convention of other add-on APIs
    """List of API functions with their first doc line."""
    lines = ["Easy Conifer API v%d (add-on %s)" % (API_VERSION, _version())]
    for name in __all__:
        fn = globals()[name]
        doc = (fn.__doc__ or "").strip().splitlines()
        lines.append("  %s%s — %s" % (name, _sig(fn), doc[0] if doc else ""))
    return "\n".join(lines)


def _sig(fn):
    import inspect
    return str(inspect.signature(fn))


def version():
    """Add-on and API version, Blender version."""
    return dict(addon=_version(), api=API_VERSION, blender=bpy.app.version_string)


def presets_list(kind=None):
    """Presets: [{key, name, kind, section}]. kind: CONIFER / BROADLEAF / SHRUB / HEDGE or None."""
    out, section = [], ""
    for key, label, desc in presets.ALL_ENUM_ITEMS:
        if not key:
            section = label
            continue
        k = ops.preset_kind(key)
        if k == 'BROADLEAF' and key in presets.SHRUB_PRESETS:
            k_pub = 'SHRUB'
        else:
            k_pub = k
        if kind and kind.upper() != k_pub:
            continue
        out.append(dict(key=key, name=label, description=desc, kind=k_pub, section=section))
    return out


def forms():
    """Clipped-shrub forms: [{key, name, description}]."""
    return [dict(key=k, name=label, description=desc) for k, label, desc in presets.SHRUB_FORM_ITEMS]


def parameters(name):
    """All generator parameters of an object: {param name: value}. Materials as names."""
    mod = ops.conifer_modifier(_obj(name))
    return {k: _plain(get_input(mod, ident)) for k, ident in ops._ids(mod).items()}


def parameter_names(kind):
    """Parameter names of a generator kind (CONIFER / BROADLEAF / HEDGE), grouped by panel."""
    from . import broadleaf_builder, hedge_builder
    interface = {'CONIFER': nodes_builder.INTERFACE, 'BROADLEAF': broadleaf_builder.INTERFACE,
                 'HEDGE': hedge_builder.INTERFACE}.get(kind.upper())
    if interface is None:
        raise ValueError("kind must be CONIFER, BROADLEAF or HEDGE")
    out = {}
    for panel, socks in interface:
        out[panel] = [dict(name=s[0], type=s[1], default=_plain(s[2]),
                           min=s[3] if len(s) > 3 else None, max=s[4] if len(s) > 4 else None,
                           description=s[-1] if isinstance(s[-1], str) else "") for s in socks]
    return out


# ---------------------------------------------------------------- scene
def info(name):
    """One object: preset, kind, seed, location, rotation, triangles, node warnings."""
    obj = _obj(name)
    mod = ops.conifer_modifier(obj)
    ids = ops._ids(mod)
    return dict(name=obj.name, preset=obj.get("easy_conifer_preset", ""), kind=ops.group_kind(mod.node_group),
                seed=get_input(mod, ids["Seed"]), location=[round(c, 3) for c in obj.location],
                rotation_z=round(math.degrees(obj.rotation_euler.z), 2), tris=tri_count(obj),
                warnings=[w.message for w in mod.node_warnings])


def scene_info(with_tris=False):
    """All Easy Conifer objects in the scene (tris only when with_tris=True — it evaluates them)."""
    out = []
    for obj in _objs(None):
        mod = ops.conifer_modifier(obj)
        row = dict(name=obj.name, preset=obj.get("easy_conifer_preset", ""),
                   kind=ops.group_kind(mod.node_group), location=[round(c, 3) for c in obj.location])
        if with_tris:
            row["tris"] = tri_count(obj)
        out.append(row)
    total = sum(r.get("tris", 0) for r in out)
    return dict(objects=out, count=len(out), tris_total=total if with_tris else None,
                transparent_max_bounces=getattr(getattr(bpy.context.scene, "cycles", None),
                                                "transparent_max_bounces", None))


# ---------------------------------------------------------------- create
def add(preset, location=(0, 0, 0), seed=None, form=None, name=None, rotation=0.0, params=None,
        collection=None):
    """Add a tree / shrub. form — for clipped shrubs (BALL/CUBE/TRAPEZOID/NATURAL);
    params — {parameter: value} applied after the preset; seed None = random; rotation in degrees (Z)."""
    kind = _kind_of_key(preset)
    if form is not None and kind != 'HEDGE':
        raise ValueError("form is only for clipped shrubs (HEDGE_* presets)")
    form = (form or 'BALL').upper()
    if kind == 'HEDGE' and form not in presets.SHRUB_FORMS:
        raise ValueError("unknown form %r; see forms()" % form)
    from . import broadleaf_builder, hedge_builder
    tree = {'HEDGE': hedge_builder.ensure_hedge_group, 'BROADLEAF': broadleaf_builder.ensure_broadleaf_group,
            'CONIFER': nodes_builder.ensure_group}[kind]()
    table = {'HEDGE': presets.HEDGE_PRESETS, 'BROADLEAF': presets.BROADLEAF_PRESETS, 'CONIFER': presets.PRESETS}[kind]
    label = table[preset][0]
    if kind == 'HEDGE':
        label = "%s — %s" % (label, presets.SHRUB_FORMS[form][0])
    obj = bpy.data.objects.new(name or label,
                               bpy.data.meshes.new({'HEDGE': "Shrub", 'BROADLEAF': "Tree"}.get(kind, "Conifer")))
    obj.location = Vector(location)
    obj.rotation_euler.z = math.radians(rotation)
    coll = bpy.data.collections.get(collection) if collection else bpy.context.scene.collection
    if coll is None:
        coll = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(coll)
    coll.objects.link(obj)
    mod = obj.modifiers.new(tree.name, 'NODES')
    mod.node_group = tree
    ids = ops._ids(mod)
    presets.apply(mod, ids, preset, ops._defaults(mod))
    if kind == 'HEDGE':
        ops._apply_form(mod, ids, form)
    set_input(mod, ids["Seed"], random.randint(0, 99999) if seed is None else int(seed))
    ops._set_materials(bpy.context, mod, preset)
    if params:
        _set_values(mod, params)
    obj["easy_conifer_preset"] = preset
    _bounces()
    return dict(name=obj.name, preset=preset, kind=kind, seed=get_input(mod, ids["Seed"]),
                location=[round(c, 3) for c in obj.location])


def add_many(preset, points, seed=None, form=None, params=None, rotation="random", scale_jitter=0.0,
             collection=None):
    """Add one object per point [(x, y[, z]), ...]. Seeds: seed, seed+1, ... (random if None).
    rotation: degrees or "random"; scale_jitter: 0.1 = ±10 % uniform scale."""
    rng = random.Random(seed)
    base = rng.randint(0, 90000) if seed is None else int(seed)
    out = []
    for i, p in enumerate(points):
        p = tuple(p) + (0.0,) * (3 - len(p))
        rot = rng.uniform(0, 360) if rotation == "random" else float(rotation)
        r = add(preset, p, seed=base + i, form=form, params=params, rotation=rot, collection=collection)
        if scale_jitter:
            s = 1.0 + rng.uniform(-scale_jitter, scale_jitter)
            bpy.data.objects[r["name"]].scale = (s, s, s)
        out.append(r["name"])
    return dict(names=out, count=len(out))


def add_row(preset, start, end, spacing, seed=None, form=None, params=None, rotation="along",
            collection=None):
    """Plant a row from start to end (x, y) every `spacing` metres (alley, hedge of separate shrubs).
    rotation: "along" (shrubs face the row), "random" or degrees."""
    a, b = Vector((*start[:2], 0)), Vector((*end[:2], 0))
    length = (b - a).length
    if spacing <= 0 or length == 0:
        raise ValueError("spacing must be > 0 and start != end")
    n = int(length // spacing) + 1
    ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
    pts = [a.lerp(b, i / (n - 1)) if n > 1 else a for i in range(n)]
    rot = ang if rotation == "along" else rotation
    return add_many(preset, [tuple(p) for p in pts], seed=seed, form=form, params=params, rotation=rot,
                    collection=collection)


def add_hedge(preset, start, end, height=1.0, depth=0.8, form="CUBE", seed=None, params=None, name=None):
    """One continuous clipped hedge from start to end (x, y): a single shrub stretched along the line."""
    a, b = Vector((*start[:2], 0)), Vector((*end[:2], 0))
    if _kind_of_key(preset) != 'HEDGE':
        raise ValueError("add_hedge needs a HEDGE_* preset")
    vals = dict(params or {})
    vals.update({"Width": (b - a).length, "Depth": depth, "Height": height})
    return add(preset, tuple((a + b) / 2), seed=seed, form=form, name=name, params=vals,
               rotation=math.degrees(math.atan2(b.y - a.y, b.x - a.x)))


# ---------------------------------------------------------------- edit
def set_params(names, **values):
    """Set parameters by UI name, e.g. set_params("Ель", Height=18, **{"Card Size": 0.4}).
    Colours as [r, g, b, a]; materials by name."""
    done = []
    for obj in _objs(names):
        _set_values(ops.conifer_modifier(obj), values)
        obj.update_tag()
        done.append(obj.name)
    return dict(updated=done)


def apply_preset(names, preset, keep_seed=True):
    """Re-apply a preset to objects of the same kind (a conifer can't become a birch).
    Clipped shrubs keep their form and size."""
    kind = _kind_of_key(preset)
    done, skipped = [], []
    for obj in _objs(names):
        mod = ops.conifer_modifier(obj)
        if ops.group_kind(mod.node_group) != kind:
            skipped.append(obj.name)
            continue
        ids = ops._ids(mod)
        seed = get_input(mod, ids["Seed"])
        keep = {}
        if kind == 'HEDGE':
            keep = {nm: get_input(mod, ids[nm]) for nm in presets.SHRUB_FORMS['BALL'][2] if nm in ids}
        presets.apply(mod, ids, preset, ops._defaults(mod))
        for nm, v in keep.items():
            set_input(mod, ids[nm], v)
        if keep_seed:
            set_input(mod, ids["Seed"], seed)
        ops._set_materials(bpy.context, mod, preset)
        obj["easy_conifer_preset"] = preset
        obj.update_tag()
        done.append(obj.name)
    return dict(updated=done, skipped_other_kind=skipped)


def apply_form(names, form, keep_size=False):
    """Clipped shrubs: set the form (BALL/CUBE/TRAPEZOID/NATURAL); keep_size keeps Width/Depth/Height."""
    form = form.upper()
    if form not in presets.SHRUB_FORMS:
        raise ValueError("unknown form %r; see forms()" % form)
    done = []
    for obj in _objs(names):
        mod = ops.conifer_modifier(obj)
        if ops.group_kind(mod.node_group) != 'HEDGE':
            continue
        ids = ops._ids(mod)
        size = {k: get_input(mod, ids[k]) for k in ("Width", "Depth", "Height")}
        ops._apply_form(mod, ids, form)
        if keep_size:
            for k, v in size.items():
                set_input(mod, ids[k], v)
        obj.update_tag()
        done.append(obj.name)
    return dict(updated=done)


def new_seed(names, seed=None):
    """New seed for objects: a given number or random. Returns {name: seed}."""
    out = {}
    for obj in _objs(names):
        mod = ops.conifer_modifier(obj)
        s = random.randint(0, 99999) if seed is None else int(seed)
        set_input(mod, ops._ids(mod)["Seed"], s)
        obj.update_tag()
        out[obj.name] = s
    return out


def foliage_visible(show=True, names=None):
    """Show / hide needles and leaves in the viewport (render always has them)."""
    done = []
    for obj in _objs(names):
        mod = ops.conifer_modifier(obj)
        set_input(mod, ops._ids(mod)["Visible in Viewport"], bool(show))
        obj.update_tag()
        done.append(obj.name)
    return dict(updated=done, show=bool(show))


def delete(names):
    """Delete Easy Conifer objects (by name, list, or None = all in the scene)."""
    gone = []
    for obj in _objs(names):
        gone.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)
    return dict(deleted=gone)


def realize(names):
    """Turn objects into plain meshes for export (modifier applied, instances realised, foliage on).
    Irreversible for these objects. Returns {name: triangles}."""
    out = {}
    for obj in _objs(names):
        mod = ops.conifer_modifier(obj)
        ids = ops._ids(mod)
        set_input(mod, ids["Visible in Viewport"], True)
        if "Realize Instances" in ids:
            set_input(mod, ids["Realize Instances"], True)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        old = obj.data
        obj.modifiers.remove(mod)
        obj.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
        me.calc_loop_triangles()
        out[obj.name] = len(me.loop_triangles)
    return out


def rebuild():
    """Recreate the generator node groups from the add-on and move every object to them."""
    with bpy.context.temp_override(**_override()):
        r = bpy.ops.object.easy_conifer_rebuild()
    return dict(result=sorted(r))


# ---------------------------------------------------------------- textures
def bake(species="ALL", resolution=2048, seed=0, density=1.0):
    """Re-bake twig atlases (species key, list or "ALL"; see bake_species()). Slow: ~1–2 min per
    species at 2048 on CPU, blocks Blender. Result goes to the user folder and is used at once."""
    keys = list(twig_baker.SPECIES) if species == "ALL" else ([species] if isinstance(species, str) else species)
    bad = [k for k in keys if k not in twig_baker.SPECIES]
    if bad:
        raise ValueError("unknown species %s; see bake_species()" % bad)
    try:
        out_dir = bpy.utils.extension_path_user(__package__, path="textures", create=True)
    except Exception:
        import os
        out_dir = os.path.join(bpy.utils.user_resource('DATAFILES'), "easy_conifer", "textures")
    import time
    done = {}
    for sp in keys:
        t = time.time()
        twig_baker.bake_atlas(sp, out_dir, resolution=int(resolution), seed=int(seed),
                              density_scale=float(density), report=lambda *a: None)
        mat = bpy.data.materials.get(materials.needle_material_name(sp))
        if mat:
            materials.assign_atlas(mat, sp)
        done[sp] = round(time.time() - t, 1)
    return dict(folder=out_dir, seconds=done)


def bake_species():
    """Keys accepted by bake()."""
    return list(twig_baker.SPECIES)


def reset_textures():
    """Delete re-baked atlases and go back to the ones shipped with the add-on."""
    with bpy.context.temp_override(**_override()):
        r = bpy.ops.object.easy_conifer_reset_textures()
    return dict(result=sorted(r))


# ---------------------------------------------------------------- view
def frame(names=None, camera_view=False):
    """Frame objects in the first 3D view (for get_viewport_screenshot). Needs the UI (not -b)."""
    objs = _objs(names)
    screen = bpy.context.screen
    for area in (screen.areas if screen else []):
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            for o in bpy.context.scene.objects:
                if o is not None:
                    o.select_set(o in objs)
            if objs:
                bpy.context.view_layer.objects.active = objs[0]
            with bpy.context.temp_override(area=area, region=region):
                if camera_view:
                    bpy.ops.view3d.view_camera()
                else:
                    bpy.ops.view3d.view_selected()
            return dict(framed=[o.name for o in objs])
    return dict(framed=[], note="no 3D view (background mode?)")


def _override():
    win = bpy.context.window or (bpy.context.window_manager.windows[0]
                                 if bpy.context.window_manager.windows else None)
    return dict(window=win) if win else {}


__all__ = ["help", "version", "presets_list", "forms", "parameter_names", "parameters", "info", "scene_info",
           "add", "add_many", "add_row", "add_hedge", "set_params", "apply_preset", "apply_form", "new_seed",
           "foliage_visible", "delete", "realize", "rebuild", "bake", "bake_species", "reset_textures", "frame",
           "tri_count"]
