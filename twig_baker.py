# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — high-poly twig generator and texture-atlas baker.
# Copyright (C) 2026 Pavel Fomin
"""Builds polygonal conifer twigs (real needles) and bakes them into a 2x2
texture atlas used by the cross-board cards of the tree:

    tile 0, 1 — "branchlets": a whole second-order twig with side shoots
    tile 2, 3 — "sprays": a small shoot with a few side shoots

Maps (all PNG, same layout):
    <species>_albedo.png  sRGB colour + straight alpha
    <species>_normal.png  tangent-space normal, OpenGL (+Y up)
    <species>_mask.png    R = ambient occlusion, G = needle/leaf mask, B = thickness, A = random id per leaf

Species: SPRUCE, FIR (needles), BIRCH (birch_twig.py), POPLAR, WILLOW, MAPLE, ASH, LINDEN
(broadleaf_twig.py).
Each tile is a unit square: the twig base is at the bottom centre, the stem
runs up (+V). The baker renders the twig from above with an orthographic
camera in a temporary scene; the user's scene is not touched.
"""

import math
import os

import bpy
import numpy as np

TILE_LAYOUT = ((0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5))  # UV offsets of tiles 0..3

# ----------------------------------------------------------------------------
#  Species settings (all lengths in tile units: a tile is 1 x 1)
# ----------------------------------------------------------------------------
SPECIES = {
    'SPRUCE': dict(
        needle_len=0.055, needle_w=0.0036, needle_angle=math.radians(55), needle_spread=math.radians(14),
        density=560.0, phyllotaxis='RADIAL',
        needle_col=(0.021, 0.060, 0.018), tip_col=(0.060, 0.120, 0.025), col_var=0.22,
        stem_col=(0.150, 0.050, 0.020), stem_r=0.0055,
        shoot_angle=math.radians(50), shoot_bend=0.18,
    ),
    'FIR': dict(
        needle_len=0.068, needle_w=0.0052, needle_angle=math.radians(78), needle_spread=math.radians(8),
        density=420.0, phyllotaxis='TWO_ROWS',
        needle_col=(0.015, 0.045, 0.018), tip_col=(0.035, 0.090, 0.025), col_var=0.15,
        stem_col=(0.090, 0.060, 0.025), stem_r=0.006,
        shoot_angle=math.radians(62), shoot_bend=0.08,
    ),
    'BIRCH': dict(  # leaves: see birch_twig.BIRCH
        needle_col=(0.062, 0.150, 0.024), ao_distance=0.025,
    ),
}
# broadleaf species: leaves in broadleaf_twig.py
from .broadleaf_twig import SPECIES as _BL  # noqa: E402
for _k, _v in _BL.items():
    SPECIES[_k] = dict(needle_col=_v['leaf_col'], ao_distance=0.025)
# clipped-shrub (hedge) atlases: same leaves, different tiles (see broadleaf_twig.HEDGE_KINDS)
HEDGE_SPECIES = ('COTONEASTER', 'PHYSOCARPUS')
for _k in HEDGE_SPECIES:
    SPECIES[_k + '_HEDGE'] = dict(needle_col=_BL[_k]['leaf_col'], ao_distance=0.03, hedge=_k)

# reference needle colour of each species (what the baked albedo looks like);
# the material multiplies needles by needle_color / REF to re-tint them
REF_COLOR = {k: v['needle_col'] for k, v in SPECIES.items()}


# ----------------------------------------------------------------------------
#  Geometry helpers
# ----------------------------------------------------------------------------
def _norm(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-9)


def _polyline(p0, direction, length, bend, rng, n=14, lift=0.0):
    """A gently curved shoot in the XY plane (plus a slight arch in Z)."""
    d = np.array([direction[0], direction[1], 0.0])
    d /= np.linalg.norm(d)
    side = np.array([-d[1], d[0], 0.0])
    t = np.linspace(0.0, 1.0, n)
    wobble = rng.uniform(-0.3, 0.3) * np.sin(t * math.pi * rng.uniform(1.0, 2.0))
    curve = bend * t * t + 0.015 * wobble
    pts = (np.asarray(p0)[None, :] + length * (t[:, None] * d[None, :] + curve[:, None] * side[None, :]))
    pts[:, 2] += length * (lift * np.sin(t * math.pi) * 0.25)
    return pts


def _resample(pts, spacing):
    """Points every `spacing` along a polyline with tangents and arc param 0..1."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1]
    if total <= spacing:
        return np.zeros((0, 3)), np.zeros((0, 3)), np.zeros(0), total
    s = np.arange(spacing * 0.5, total, spacing)
    idx = np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1)
    f = ((s - cum[idx]) / np.maximum(seg[idx], 1e-9))[:, None]
    p = pts[idx] * (1 - f) + pts[idx + 1] * f
    tang = _norm(pts[idx + 1] - pts[idx])
    return p, tang, s / total, total


class MeshBuilder:
    def __init__(self):
        self.verts, self.faces = [], []
        self.albedo, self.needle, self.thick, self.rid = [], [], [], []
        self.nv = 0
        self._rng = np.random.default_rng(1234)

    def add(self, verts, faces, col, needle, thick):
        verts = np.asarray(verts, dtype=np.float32).reshape(-1, 3)
        faces = np.asarray(faces, dtype=np.int64) + self.nv
        self.verts.append(verts)
        self.faces.append(faces)
        n = len(verts)
        self.albedo.append(np.broadcast_to(np.asarray(col, np.float32).reshape(-1, 3), (n, 3))
                           if np.asarray(col).ndim == 1 else np.asarray(col, np.float32))
        self.needle.append(np.full(n, needle, np.float32))
        self.thick.append(np.full(n, thick, np.float32))
        self.rid.append(np.full(n, self._rng.random(), np.float32))   # one random id per leaf / part
        self.nv += n

    def to_object(self, name, collection):
        verts = np.concatenate(self.verts)
        faces = np.concatenate(self.faces)
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", verts.ravel())
        k = faces.shape[1]
        mesh.loops.add(len(faces) * k)
        mesh.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
        mesh.polygons.add(len(faces))
        mesh.polygons.foreach_set("loop_start", (np.arange(len(faces)) * k).astype(np.int32))
        mesh.update(calc_edges=True)
        mesh.validate()
        mesh.shade_smooth()
        for aname, data, dtype in (("albedo", np.concatenate(self.albedo), 'FLOAT_COLOR'),
                                   ("needle", np.concatenate(self.needle), 'FLOAT'),
                                   ("thick", np.concatenate(self.thick), 'FLOAT'),
                                   ("rid", np.concatenate(self.rid), 'FLOAT')):
            attr = mesh.attributes.new(aname, dtype, 'POINT')
            if dtype == 'FLOAT_COLOR':
                rgba = np.concatenate([data, np.ones((len(data), 1), np.float32)], axis=1)
                attr.data.foreach_set("color", rgba.ravel())
            else:
                attr.data.foreach_set("value", data)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        return obj


def _add_tube(mb, pts, r0, r1, col, sides=6):
    n = len(pts)
    tang = _norm(np.gradient(pts, axis=0))
    up = np.array([0.0, 0.0, 1.0])
    s = _norm(np.cross(tang, up))
    u = np.cross(s, tang)
    r = np.linspace(r0, r1, n)[:, None]
    ang = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    ring = (np.cos(ang)[None, :, None] * s[:, None, :] + np.sin(ang)[None, :, None] * u[:, None, :])
    verts = pts[:, None, :] + ring * r[:, :, None]
    faces = []
    for i in range(n - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            faces.append((a, b, b + sides))       # triangles only, so all
            faces.append((a, b + sides, a + sides))  # parts share one face size
    mb.add(verts.reshape(-1, 3), faces, col, 0.0, 0.2)


def _add_needles(mb, pts, sp, rng, length_scale=1.0):
    """Polygonal needles along a shoot polyline."""
    spacing = 1.0 / sp['density']
    base, tang, u, total = _resample(pts, spacing)
    n = len(base)
    if n == 0:
        return
    up = np.array([0.0, 0.0, 1.0])
    s = _norm(np.cross(tang, up))
    v = np.cross(s, tang)
    k = np.arange(n)
    if sp['phyllotaxis'] == 'RADIAL':
        # spiral around the shoot, mostly over the upper side and flanks
        phi = (k * 2.39996323) % (2 * math.pi)
        phi = -0.35 * math.pi + phi / (2 * math.pi) * 1.7 * math.pi + rng.uniform(-0.2, 0.2, n)
        radial = np.cos(phi)[:, None] * s + np.sin(phi)[:, None] * v
    else:
        # two flat rows, a few short needles on top
        side = np.where(k % 2 == 0, 1.0, -1.0)
        top = rng.random(n) < 0.18
        radial = _norm(side[:, None] * s + (np.where(top, 1.6, 0.18))[:, None] * v)
    a = sp['needle_angle'] + rng.normal(0.0, sp['needle_spread'], n)
    d = _norm(np.cos(a)[:, None] * tang + np.sin(a)[:, None] * radial)
    # shorter at the very base and towards the shoot tip
    taper = np.clip(np.minimum(u * 6.0 + 0.35, 1.0) * (1.0 - 0.45 * np.clip((u - 0.75) / 0.25, 0, 1)), 0.3, 1.0)
    length = sp['needle_len'] * length_scale * taper * rng.uniform(0.85, 1.12, n)
    if sp['phyllotaxis'] == 'TWO_ROWS':
        length = np.where(top, length * 0.55, length)
    w = sp['needle_w'] * rng.uniform(0.85, 1.1, n)
    e1 = _norm(np.cross(d, v + 1e-4))
    e2 = np.cross(e1, d)
    p_base = base + radial * sp['stem_r'] * 0.5
    ring_c = p_base + d * (length * 0.18)[:, None]
    hw, hh = (w * 0.5)[:, None], (w * 0.32)[:, None]
    verts = np.stack([p_base,
                      ring_c + e1 * hw, ring_c + e2 * hh, ring_c - e1 * hw, ring_c - e2 * hh,
                      p_base + d * length[:, None]], axis=1)              # (n, 6, 3)
    tri = np.array([(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
                    (1, 5, 2), (2, 5, 3), (3, 5, 4), (4, 5, 1)])
    faces = (tri[None, :, :] + (np.arange(n) * 6)[:, None, None]).reshape(-1, 3)
    # colour: per-needle jitter, young growth at the shoot tip is lighter
    jitter = 1.0 + rng.uniform(-sp['col_var'], sp['col_var'], n)
    young = np.clip((u - 0.62) / 0.38, 0.0, 1.0) ** 1.5
    col = (np.asarray(sp['needle_col'])[None, :] * (1 - young[:, None]) +
           np.asarray(sp['tip_col'])[None, :] * young[:, None]) * jitter[:, None]
    col = np.repeat(col, 6, axis=0)
    # needle tips a touch lighter, bases darker
    shade = np.tile(np.array([0.7, 1.0, 1.0, 1.0, 1.0, 1.15]), n)[:, None]
    mb.add(verts.reshape(-1, 3), faces, col * shade, 1.0, 1.0)


def build_twig(species, kind, seed, collection, density_scale=1.0):
    """kind: 'BRANCHLET' or 'SPRAY'. Returns the created object."""
    if species == 'BIRCH':
        from .birch_twig import build_birch_twig
        mb = MeshBuilder()
        build_birch_twig(kind, seed, mb, _add_tube, _polyline)
        return mb.to_object("twig_%s_%s_%d" % (species, kind, seed), collection)
    if SPECIES[species].get('hedge'):
        from .broadleaf_twig import build_hedge_tile
        mb = MeshBuilder()
        build_hedge_tile(SPECIES[species]['hedge'], kind, seed, mb, _add_tube, _polyline)
        return mb.to_object("twig_%s_%s_%d" % (species, kind, seed), collection)
    if species in _BL:
        from .broadleaf_twig import build_broadleaf_twig
        mb = MeshBuilder()
        build_broadleaf_twig(species, kind, seed, mb, _add_tube, _polyline)
        return mb.to_object("twig_%s_%s_%d" % (species, kind, seed), collection)
    sp = dict(SPECIES[species])
    sp['density'] *= density_scale
    rng = np.random.default_rng(seed)
    mb = MeshBuilder()
    stem_col = np.asarray(sp['stem_col'])

    if kind == 'BRANCHLET':
        main_len, n_side, side_max, t0, t1 = 0.95, int(rng.integers(9, 13)), 0.46, 0.12, 0.9
    else:
        main_len, n_side, side_max, t0, t1 = 0.92, int(rng.integers(3, 6)), 0.36, 0.3, 0.85
    main = _polyline((0.0, 0.02, 0.0), (rng.uniform(-0.05, 0.05), 1.0), main_len, rng.uniform(-0.04, 0.04),
                     rng, n=18, lift=0.15)
    _add_tube(mb, main, sp['stem_r'] * 1.2, sp['stem_r'] * 0.45, stem_col)
    _add_needles(mb, main, sp, rng)

    ts = np.linspace(t0, t1, n_side) + rng.uniform(-0.02, 0.02, n_side)
    for i, t in enumerate(ts):
        side = 1.0 if i % 2 == 0 else -1.0
        idx = min(int(t * (len(main) - 1)), len(main) - 2)
        p0 = main[idx]
        tang = _norm(main[idx + 1] - main[idx])
        ang = sp['shoot_angle'] + rng.uniform(-0.12, 0.12)
        ca, sa = math.cos(ang), math.sin(ang) * side
        d = (tang[0] * ca - tang[1] * sa, tang[0] * sa + tang[1] * ca)
        # longest shoots near the base, tapering to the tip (triangular outline)
        L = side_max * (1.0 - (t - t0) / (t1 - t0 + 1e-6) * 0.72) * rng.uniform(0.82, 1.05)
        L = min(L, (0.47 - abs(p0[0])) / max(abs(math.sin(ang)), 0.3), 0.98 - p0[1])
        shoot = _polyline(p0, d, L, -side * sp['shoot_bend'] * rng.uniform(0.6, 1.2), rng, n=10, lift=0.3)
        _add_tube(mb, shoot, sp['stem_r'] * 0.8, sp['stem_r'] * 0.35, stem_col * 1.1)
        _add_needles(mb, shoot, sp, rng, 0.95)
        # tertiary shoots on the long lower shoots of a branchlet
        if kind == 'BRANCHLET' and L > 0.24:
            for j in range(int(rng.integers(1, 3))):
                tt = rng.uniform(0.35, 0.7)
                jdx = int(tt * (len(shoot) - 1))
                q0 = shoot[jdx]
                st = _norm(shoot[jdx + 1] - shoot[jdx])
                s2 = 1.0 if j % 2 == 0 else -1.0
                a2 = sp['shoot_angle'] * 0.9
                d2 = (st[0] * math.cos(a2) - st[1] * math.sin(a2) * s2,
                      st[0] * math.sin(a2) * s2 + st[1] * math.cos(a2))
                L2 = L * rng.uniform(0.25, 0.4)
                end = q0[:2] + np.asarray(d2) * L2
                if abs(end[0]) > 0.48 or end[1] > 0.98 or end[1] < 0.02:
                    continue
                sh2 = _polyline(q0, d2, L2, 0.05, rng, n=6, lift=0.2)
                _add_tube(mb, sh2, sp['stem_r'] * 0.5, sp['stem_r'] * 0.3, stem_col * 1.15)
                _add_needles(mb, sh2, sp, rng, 0.85)
    return mb.to_object("twig_%s_%s_%d" % (species, kind, seed), collection)


# ----------------------------------------------------------------------------
#  Baking
# ----------------------------------------------------------------------------
def _pass_material(ao_distance=0.012):
    """Emission material that outputs one of four passes, chosen by a Value node."""
    mat = bpy.data.materials.new("EC_bake_pass")
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    emit = N.new("ShaderNodeEmission")
    sel = N.new("ShaderNodeValue")
    sel.name = "pass"
    alb = N.new("ShaderNodeAttribute"); alb.attribute_name = "albedo"
    ndl = N.new("ShaderNodeAttribute"); ndl.attribute_name = "needle"
    thk = N.new("ShaderNodeAttribute"); thk.attribute_name = "thick"
    geo = N.new("ShaderNodeNewGeometry")
    nrm = N.new("ShaderNodeVectorMath"); nrm.operation = 'MULTIPLY_ADD'
    L.new(geo.outputs["Normal"], nrm.inputs[0])
    nrm.inputs[1].default_value = (0.5, 0.5, 0.5)
    nrm.inputs[2].default_value = (0.5, 0.5, 0.5)
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = ao_distance
    ao.samples = 16
    mask = N.new("ShaderNodeCombineXYZ")
    L.new(ao.outputs["AO"], mask.inputs[0])
    L.new(ndl.outputs["Fac"], mask.inputs[1])
    L.new(thk.outputs["Fac"], mask.inputs[2])
    # pass 0 -> albedo, 1 -> normal, 2 -> mask
    is1 = N.new("ShaderNodeMath"); is1.operation = 'COMPARE'
    L.new(sel.outputs[0], is1.inputs[0]); is1.inputs[1].default_value = 1.0; is1.inputs[2].default_value = 0.1
    is2 = N.new("ShaderNodeMath"); is2.operation = 'COMPARE'
    L.new(sel.outputs[0], is2.inputs[0]); is2.inputs[1].default_value = 2.0; is2.inputs[2].default_value = 0.1
    m1 = N.new("ShaderNodeMix"); m1.data_type = 'VECTOR'
    L.new(is1.outputs[0], m1.inputs[0])
    L.new(alb.outputs["Vector"], m1.inputs[4]); L.new(nrm.outputs[0], m1.inputs[5])
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'VECTOR'
    L.new(is2.outputs[0], m2.inputs[0])
    L.new(m1.outputs[1], m2.inputs[4]); L.new(mask.outputs[0], m2.inputs[5])
    # pass 3 -> random id per leaf (stored in the mask's alpha)
    rid = N.new("ShaderNodeAttribute"); rid.attribute_name = "rid"
    is3 = N.new("ShaderNodeMath"); is3.operation = 'COMPARE'
    L.new(sel.outputs[0], is3.inputs[0]); is3.inputs[1].default_value = 3.0; is3.inputs[2].default_value = 0.1
    m3 = N.new("ShaderNodeMix"); m3.data_type = 'VECTOR'
    L.new(is3.outputs[0], m3.inputs[0])
    L.new(m2.outputs[1], m3.inputs[4]); L.new(rid.outputs["Vector"], m3.inputs[5])
    L.new(m3.outputs[1], emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 1.0
    L.new(emit.outputs[0], out.inputs["Surface"])
    return mat, sel


def _read_exr(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def _dilate(rgb, alpha, iterations=12):
    """Bleed colours into transparent pixels so mip-maps have no dark halo."""
    rgb = rgb.copy()
    filled = alpha > 0.02
    for _ in range(iterations):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(alpha.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            m = np.roll(np.roll(filled, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * m[..., None]
            cnt += m
        new = (~filled) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]
        filled = filled | new
        if filled.all():
            break
    return rgb


def _linear_to_srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def _save_png(name, rgba, path, non_color):
    h, w = rgba.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    img.pixels.foreach_set(np.clip(rgba, 0, 1).astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def bake_atlas(species, out_dir, resolution=2048, seed=0, samples=16, density_scale=1.0, report=print):
    """Build 4 high-poly twigs and bake them into <species>_{albedo,normal,mask}.png."""
    os.makedirs(out_dir, exist_ok=True)
    tile = resolution // 2
    scene = bpy.data.scenes.new("EC_twig_bake")
    try:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = samples
        scene.cycles.use_denoising = False
        scene.cycles.max_bounces = 0
        scene.cycles.film_transparent_glass = True
        scene.render.film_transparent = True
        scene.cycles.filter_width = 1.0
        scene.render.resolution_x = scene.render.resolution_y = tile
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'OPEN_EXR'
        scene.render.image_settings.color_depth = '16'
        scene.view_settings.view_transform = 'Standard'
        world = bpy.data.worlds.new("EC_bake_world")
        world.color = (0, 0, 0)
        scene.world = world
        cam = bpy.data.objects.new("EC_bake_cam", bpy.data.cameras.new("EC_bake_cam"))
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = 1.0
        cam.data.clip_end = 10.0
        cam.location = (0.0, 0.5, 2.0)
        scene.collection.objects.link(cam)
        scene.camera = cam
        mat, sel = _pass_material(SPECIES[species].get('ao_distance', 0.012))

        albedo = np.zeros((resolution, resolution, 4), np.float32)
        normal = np.zeros((resolution, resolution, 4), np.float32)
        mask = np.zeros((resolution, resolution, 4), np.float32)
        if SPECIES[species].get('hedge'):
            from .broadleaf_twig import HEDGE_KINDS as kinds
        else:
            kinds = ('BRANCHLET', 'BRANCHLET', 'SPRAY', 'SPRAY')
        tmp = os.path.join(out_dir, "_tmp_pass.exr")
        for t, kind in enumerate(kinds):
            obj = build_twig(species, kind, seed * 10 + t + 1, scene.collection, density_scale)
            obj.data.materials.append(mat)
            passes = []
            for p in range(4):
                sel.outputs[0].default_value = float(p)
                scene.render.filepath = tmp
                bpy.ops.render.render(write_still=True, scene=scene.name)
                passes.append(_read_exr(tmp))
            a = passes[0][..., 3]
            inv = np.where(a > 1e-4, 1.0 / np.maximum(a, 1e-4), 0.0)[..., None]  # un-premultiply
            ox, oy = int(TILE_LAYOUT[t][0] * resolution), int(TILE_LAYOUT[t][1] * resolution)
            sl = (slice(oy, oy + tile), slice(ox, ox + tile))
            albedo[sl + (slice(0, 3),)] = _dilate(passes[0][..., :3] * inv, a)
            albedo[sl + (3,)] = a
            nrm = passes[1][..., :3] * inv
            v = nrm * 2.0 - 1.0                      # keep normals in the front hemisphere (no edge-on artefacts)
            v[..., 2] = np.maximum(v[..., 2], 0.3)
            v /= np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6)
            nrm = v * 0.5 + 0.5
            nrm = np.where(a[..., None] > 0.02, nrm, (0.5, 0.5, 1.0))
            normal[sl + (slice(0, 3),)] = _dilate(nrm, a)
            normal[sl + (3,)] = 1.0
            mk = passes[2][..., :3] * inv
            mask[sl + (slice(0, 3),)] = _dilate(mk, a)
            mask[sl + (3,)] = _dilate(np.repeat((passes[3][..., :1] * inv), 3, axis=2), a)[..., 0]
            me = obj.data
            bpy.data.objects.remove(obj)
            bpy.data.meshes.remove(me)
            report("  baked tile %d (%s)" % (t, kind))
        if os.path.exists(tmp):
            os.remove(tmp)
        # renormalise the normal map
        n = normal[..., :3] * 2 - 1
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
        normal[..., :3] = n * 0.5 + 0.5
        albedo[..., :3] = _linear_to_srgb(albedo[..., :3])
        paths = {}
        for key, data, nc in (("albedo", albedo, False), ("normal", normal, True), ("mask", mask, True)):
            path = os.path.join(out_dir, "%s_%s.png" % (species.lower(), key))
            _save_png("EC_%s_%s" % (species, key), data, path, nc)
            paths[key] = path
        return paths
    finally:
        cam_data = scene.camera.data if scene.camera else None
        for o in list(scene.collection.objects):
            bpy.data.objects.remove(o)
        if cam_data:
            bpy.data.cameras.remove(cam_data)
        w = scene.world
        bpy.data.scenes.remove(scene)
        if w:
            bpy.data.worlds.remove(w)
        m = bpy.data.materials.get("EC_bake_pass")
        if m:
            bpy.data.materials.remove(m)
