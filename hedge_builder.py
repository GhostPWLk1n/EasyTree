# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — "Clipped Shrub Generator": pruned shrubs and hedges for urban visualisation.
# Copyright (C) 2026 Pavel Fomin
"""A clipped shrub is a shell of foliage around almost bare inner branches.

Shape:   a superellipsoid (Roundness: 0 — box, 1 — ball) with an optional top
         taper (trapezoid hedge), a cut flat bottom and noise (Unevenness)
         for the natural form; sized by Width (X) × Depth (Y) × Height.
Foliage: three layers of leaf-mat cards (atlas tiles 2, 3) offset inwards
         along the surface normal by up to Foliage Depth: an open outer layer
         you see through, a mid layer and a dark deep layer closing the view;
         plus leafy shoots sticking out ("fuzz", tile 0).
Inside:  a few square (4-sided) stems from the ground and cross-planes with
         baked bare V-forked branches (tile 1) — no branch geometry.
"""

import math

import bpy

from .nodes_builder import NB, _build_interface, _retire, interface_defaults as _defaults

GROUP_NAME = "Clipped Shrub Generator"
NODES_VERSION = 4
D = math.radians

INTERFACE = [
    ("Shape", [
        ("Width", 'FLOAT', 1.6, 0.1, 100.0, 'DISTANCE', "Size along X (hedge length)"),
        ("Depth", 'FLOAT', 1.0, 0.1, 20.0, 'DISTANCE', "Size along Y"),
        ("Height", 'FLOAT', 1.0, 0.1, 10.0, 'DISTANCE', "Height of the shrub"),
        ("Roundness", 'FLOAT', 0.2, 0.0, 1.0, 'FACTOR', "0 — box with sharp corners, 1 — ball / ellipsoid"),
        ("Top Taper", 'FLOAT', 1.0, 0.1, 1.5, 'FACTOR', "Width of the top relative to the bottom (trapezoid hedge < 1)"),
        ("Bottom Cut", 'FLOAT', 0.05, 0.0, 0.6, 'FACTOR', "Flat cut of the lower part (clearance above the ground)"),
        ("Unevenness", 'FLOAT', 0.02, 0.0, 0.5, 'FACTOR', "Bumpy, irregular outline (natural, unclipped shrub)"),
        ("Seed", 'INT', 0, 0, 100000, 'NONE', "Random seed"),
    ]),
    ("Foliage", [
        ("Leaves", 'BOOLEAN', True, None, None, None, "Generate foliage cards"),
        ("Card Size", 'FLOAT', 0.26, 0.03, 2.0, 'DISTANCE', "Size of the leaf-mat cards on the surface"),
        ("Surface Density", 'FLOAT', 110.0, 0.5, 600.0, 'NONE', "Outer-layer cards per square metre"),
        ("Inner Layer", 'FLOAT', 1.2, 0.0, 3.0, 'FACTOR', "Density of the mid and deep layers (relative to the outer one)"),
        ("Foliage Depth", 'FLOAT', 0.18, 0.0, 2.0, 'DISTANCE', "Thickness of the leafy shell: how deep the inner layers sit"),
        ("Card Tilt", 'FLOAT', D(30), 0.0, D(90), 'ANGLE', "Random tilt of surface cards from the surface"),
        ("Surface Roughness", 'FLOAT', 0.25, 0.0, 1.0, 'FACTOR', "How far cards sink in / stick out of the surface: low — crisp clipped edges"),
        ("Fuzz Density", 'FLOAT', 3.0, 0.0, 100.0, 'NONE', "Leafy shoots sticking out, per square metre"),
        ("Fuzz Size", 'FLOAT', 0.3, 0.03, 2.0, 'DISTANCE', "Length of the sticking-out shoots"),
        ("Visible in Viewport", 'BOOLEAN', True, None, None, None, "Show foliage in the viewport (always rendered)"),
    ]),
    ("Leaf Colour", [
        ("Leaf Color", 'RGBA', (0.025, 0.070, 0.016, 1.0), None, None, None, "Leaf colour (texture is re-tinted towards it)"),
        ("Color Variation", 'FLOAT', 0.2, 0.0, 1.0, 'FACTOR', "Random brightness variation per card"),
        ("Hue Variation", 'FLOAT', 0.03, 0.0, 0.3, 'FACTOR', "Random hue shift per card"),
        ("Inner Shade", 'FLOAT', 0.5, 0.0, 1.0, 'FACTOR', "Under-layer and inner leaves darker, surface lighter"),
        ("Top Light", 'FLOAT', 0.15, 0.0, 1.0, 'FACTOR', "Top lighter, bottom darker"),
        ("Edge Color", 'RGBA', (0.07, 0.15, 0.025, 1.0), None, None, None, "Tint of fresh growth on the surface and the shoots"),
        ("Edge Color Amount", 'FLOAT', 0.25, 0.0, 1.0, 'FACTOR', "How strongly the surface is tinted with Edge Color"),
        ("Leaf Gloss", 'FLOAT', 0.5, 0.0, 1.0, 'FACTOR', "Glossy coat of the leaves"),
        ("Leaf Sheen", 'FLOAT', 0.0, 0.0, 1.0, 'FACTOR', "Velvety leaves"),
    ]),
    ("Inside", [
        ("Stems per Metre", 'FLOAT', 4.0, 0.0, 30.0, 'NONE', "Stems from the ground per metre of width"),
        ("Stem Radius", 'FLOAT', 0.015, 0.002, 0.2, 'DISTANCE', "Radius of the stems (4-sided)"),
        ("Stem Height", 'FLOAT', 0.45, 0.1, 1.0, 'FACTOR', "How high the stems go, relative to the height"),
        ("Inner Branch Density", 'FLOAT', 4.0, 0.0, 60.0, 'NONE', "Planes with baked bare branches, per square metre of the shell"),
        ("Inner Branch Size", 'FLOAT', 0.45, 0.05, 3.0, 'DISTANCE', "Size of the bare-branch planes"),
    ]),
    ("Mesh", [
        ("Shape Resolution", 'INT', 8, 3, 32, 'NONE', "Resolution of the hidden shape the cards are spread on"),
        ("Bark Material", 'MATERIAL', None, None, None, None, "Material for the stems"),
        ("Leaf Material", 'MATERIAL', None, None, None, None, "Material for the cards (hedge atlas)"),
    ]),
]


def interface_defaults():
    return _defaults(INTERFACE)


def build_hedge_group():
    _retire(GROUP_NAME)
    tree = bpy.data.node_groups.new(GROUP_NAME, 'GeometryNodeTree')
    tree.description = "Clipped shrub / hedge generator — Easy Conifer"
    _build_interface(tree, INTERFACE)
    tree["easy_conifer_hedge_version"] = NODES_VERSION
    try:
        tree.is_modifier = True
    except Exception:
        pass
    b = NB(tree)
    b.gi = b.node("NodeGroupInput")
    go = b.node("NodeGroupOutput")
    W, Dp, H = b.I("Width"), b.I("Depth"), b.I("Height")
    Z = (0.0, 0.0, 1.0)

    # ------------------------------------------------------------ the shape
    b.section("shape")
    expo = b.lerp(b.I("Roundness"), 12.0, 2.0)

    def shell(depth=None):
        """The shape's surface, moved inwards along its normal by `depth` metres."""
        res = b.I("Shape Resolution")
        cube = b.node("GeometryNodeMeshCube", {"Size": (2.0, 2.0, 2.0), "Vertices X": res, "Vertices Y": res,
                                               "Vertices Z": res})
        px, py, pz = b.sep(b.position())
        ssum = b.add(b.add(b.pow(b.math('ABSOLUTE', px), expo), b.pow(b.math('ABSOLUTE', py), expo)),
                     b.pow(b.math('ABSOLUTE', pz), expo))
        f = b.pow(b.mx(ssum, 1e-6), b.div(-1.0, expo))
        qx, qy, qz = b.mul(px, f), b.mul(py, f), b.mul(pz, f)
        qz = b.mx(qz, b.sub(b.mul(b.I("Bottom Cut"), 2.0), 1.0))
        k = b.lerp(b.mul(b.add(qz, 1.0), 0.5), 1.0, b.I("Top Taper"))
        qx, qy = b.mul(qx, k), b.mul(qy, k)
        nz = b.node("ShaderNodeTexNoise", {"Scale": 1.4, "Detail": 2.0}, noise_dimensions='4D')
        b.feed(b.sock_in(nz, "Vector"), b.xyz(qx, qy, qz))
        b.feed(b.sock_in(nz, "W"), b.mul(b.I("Seed"), 0.37))
        bump = b.add(1.0, b.mul(b.mul(b.sub(b.sock_out(nz, "Factor" if any(s.name == "Factor" for s in nz.outputs) else "Fac"), 0.5), 2.0),
                                b.I("Unevenness")))
        g = bump
        pos = b.xyz(b.mul(b.mul(qx, g), b.mul(W, 0.5)), b.mul(b.mul(qy, g), b.mul(Dp, 0.5)),
                    b.mul(b.mul(b.add(b.mul(qz, g), 1.0), 0.5), H))
        m = b.set_position(b.sock_out(cube, "Mesh"), pos=pos)
        if depth is not None:   # offset in metres — right for long hedges too, never past the core
            lim = b.mul(b.mn(b.mn(W, Dp), b.mul(H, 2.0)), 0.4)
            d = b.mn(depth, lim)
            m = b.set_position(m, offset=b.vscale(b.sock_out(b.node("GeometryNodeInputNormal")), b.mul(d, -1.0)))
        # drop the underside: nothing is seen there
        nrm = b.sock_out(b.node("GeometryNodeInputNormal"))
        under = b.cmp('LESS_THAN', b.sep(nrm)[2], -0.75)
        return b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": m, "Selection": under}, domain='FACE'))

    def scatter(mesh, density, seed_k):
        d = b.node("GeometryNodeDistributePointsOnFaces", distribute_method='RANDOM')
        b.feed(b.sock_in(d, "Mesh"), mesh)
        b.feed(b.sock_in(d, "Density"), density)
        b.feed(b.sock_in(d, "Seed"), b.seed(seed_k))
        pts = b.store(b.sock_out(d, "Points"), "ec_n", b.sock_out(d, "Normal"), 'FLOAT_VECTOR')
        return pts

    def quad(centered, vertical=False):
        grid = b.node("GeometryNodeMeshGrid", {"Size X": 1.0, "Size Y": 1.0, "Vertices X": 2, "Vertices Y": 2})
        g = b.store(b.sock_out(grid, "Mesh"), "UVMap", b.sock_out(grid, "UV Map"), 'FLOAT2', 'CORNER')
        ins = {"Geometry": g, "Translation": (0.0, 0.0 if centered else 0.5, 0.0)}
        if vertical:
            ins["Rotation"] = (0.0, math.pi / 2, 0.0)
        return b.sock_out(b.node("GeometryNodeTransform", ins))

    def rot_normal(n, euler):
        r = b.node("FunctionNodeAlignRotationToVector", {"Vector": n}, axis='Z')
        loc = b.node("FunctionNodeEulerToRotation", {"Euler": euler})
        return b.sock_out(b.node("FunctionNodeRotateRotation", {"Rotation": b.sock_out(r), "Rotate By": b.sock_out(loc)},
                                 rotation_space='LOCAL'))

    def rot_up(direction, roll):
        r = b.node("FunctionNodeAlignRotationToVector", {"Vector": direction}, axis='Y')
        loc = b.node("FunctionNodeEulerToRotation", {"Euler": b.xyz(0.0, roll, 0.0)})
        return b.sock_out(b.node("FunctionNodeRotateRotation", {"Rotation": b.sock_out(r), "Rotate By": b.sock_out(loc)},
                                 rotation_space='LOCAL'))

    def tag(inst, tile_lo, tile_n, depth, k):
        ii = b.index()
        tile = b.add(tile_lo, b.floor(b.rand(0.0, tile_n - 0.001, ii, b.seed(k))))
        g = b.store(inst, "ec_tile", tile, 'FLOAT', 'INSTANCE')
        g = b.store(g, "ec_dep", b.add(depth, b.rand(-0.1, 0.1, ii, b.seed(k + 1))), 'FLOAT', 'INSTANCE')
        g = b.store(g, "ec_age", b.rand(0.0, 1.0, ii, b.seed(k + 2)), 'FLOAT', 'INSTANCE')
        g = b.store(g, "ec_hue", b.rand(-1.0, 1.0, ii, b.seed(k + 3)), 'FLOAT', 'INSTANCE')
        return b.store(g, "ec_pos", b.position(), 'FLOAT_VECTOR', 'INSTANCE')

    outer = shell()
    fd = b.I("Foliage Depth")

    # --------------------------------------------------------- surface layer
    b.section("surface")
    cs = b.I("Card Size")
    tilt = b.I("Card Tilt")

    def mat_layer(mesh, density, size_k, depth, k):
        pts = scatter(mesh, density, k)
        i = b.index()
        n = b.named("ec_n", 'FLOAT_VECTOR')
        e = b.xyz(b.mul(tilt, b.rand(-1.0, 1.0, i, b.seed(k + 4))), b.mul(tilt, b.rand(-1.0, 1.0, i, b.seed(k + 5))),
                  b.rand(0.0, 2 * math.pi, i, b.seed(k + 6)))
        rough = b.I("Surface Roughness")
        off = b.vscale(n, b.mul(cs, b.mul(b.rand(-1.0, 0.3, i, b.seed(k + 7)), rough)))
        pts = b.set_position(pts, offset=off)
        sc = b.mul(b.mul(cs, size_k), b.rand(0.85, 1.2, i, b.seed(k + 8)))
        inst = b.node("GeometryNodeInstanceOnPoints", {"Points": pts, "Instance": quad(True), "Rotation": rot_normal(n, e),
                                                       "Scale": b.xyz(sc, sc, sc)})
        return tag(b.sock_out(inst), 2.0, 2.0, depth, k + 10)

    dens = b.I("Surface Density")
    surf = mat_layer(outer, dens, 1.0, 1.0, 100)                       # open, you see through it
    mid = mat_layer(shell(b.mul(fd, 0.5)), b.mul(dens, b.mul(b.I("Inner Layer"), 0.6)), 1.0, 0.45, 200)
    deep = mat_layer(shell(fd), b.mul(dens, b.mul(b.I("Inner Layer"), 0.4)), 1.15, 0.0, 250)
    under = b.join(mid, deep)

    # ------------------------------------------------------------------ fuzz
    b.section("fuzz")
    fz = scatter(outer, b.I("Fuzz Density"), 300)
    fi = b.index()
    fn = b.named("ec_n", 'FLOAT_VECTOR')
    fdir = b.vnorm(b.vadd(b.vadd(fn, b.xyz(0.0, 0.0, 0.35)),
                          b.xyz(b.rand(-0.4, 0.4, fi, b.seed(301)), b.rand(-0.4, 0.4, fi, b.seed(302)), b.rand(-0.2, 0.3, fi, b.seed(303)))))
    fsc = b.mul(b.I("Fuzz Size"), b.rand(0.7, 1.25, fi, b.seed(304)))
    fz = b.set_position(fz, offset=b.vscale(fn, b.mul(fsc, -0.35)))
    fuzz = b.node("GeometryNodeInstanceOnPoints", {"Points": fz, "Instance": quad(False),
                                                   "Rotation": rot_up(fdir, b.rand(0.0, math.pi, fi, b.seed(305))),
                                                   "Scale": b.xyz(fsc, fsc, fsc)})
    fuzz = tag(b.sock_out(fuzz), 0.0, 1.0, 1.0, 310)

    # -------------------------------------------------- inner bare branches
    b.section("inside")
    ib = scatter(shell(b.add(b.mul(fd, 1.3), 0.1)), b.I("Inner Branch Density"), 400)
    ii = b.index()
    idir = b.vnorm(b.vadd(b.vscale(b.named("ec_n", 'FLOAT_VECTOR'), 0.6), b.xyz(0.0, 0.0, 0.8)))
    isc = b.mul(b.I("Inner Branch Size"), b.rand(0.75, 1.2, ii, b.seed(401)))
    cross = b.join(quad(False), quad(False, True))
    inner = b.node("GeometryNodeInstanceOnPoints", {"Points": ib, "Instance": cross,
                                                    "Rotation": rot_up(idir, b.rand(0.0, math.pi, ii, b.seed(402))),
                                                    "Scale": b.xyz(isc, isc, isc)})
    inner = tag(b.sock_out(inner), 1.0, 1.0, 0.0, 410)

    # ------------------------------------------------- cards → mesh, UV, colour
    b.section("cards")
    cards = b.sock_out(b.node("GeometryNodeRealizeInstances", {"Geometry": b.join(surf, under, fuzz, inner)}))
    tile = b.named("ec_tile")
    u0, v0, _ = b.sep(b.named("UVMap", 'FLOAT_VECTOR'))
    uu = b.add(b.add(b.mul(u0, 0.49), 0.005), b.mul(b.math('FLOORED_MODULO', tile, 2.0), 0.5))
    vv = b.add(b.add(b.mul(v0, 0.49), 0.005), b.mul(b.floor(b.div(tile, 2.0)), 0.5))
    cards = b.store(cards, "UVMap", b.xyz(uu, vv, 0.0), 'FLOAT2', 'CORNER')
    dep = b.clamp01(b.named("ec_dep"))
    cz = b.clamp01(b.div(b.sep(b.named("ec_pos", 'FLOAT_VECTOR'))[2], H))
    shade = b.lerp(dep, b.sub(1.0, b.I("Inner Shade")), b.add(1.0, b.mul(b.I("Inner Shade"), 0.3)))
    shade = b.mul(shade, b.add(1.0, b.mul(b.I("Top Light"), b.sub(b.mul(cz, 2.0), 1.0))))
    cvar = b.add(1.0, b.mul(b.mul(b.I("Color Variation"), 2.0), b.sub(b.named("ec_age"), 0.5)))
    base_col = b.vlerp(b.mul(b.I("Edge Color Amount"), b.mul(dep, b.named("ec_age"))), b.I("Leaf Color"), b.I("Edge Color"))
    hsv = b.node("FunctionNodeSeparateColor", {"Color": base_col}, mode='HSV')
    hue = b.math('FRACT', b.add(b.sock_out(hsv, 0), b.mul(b.I("Hue Variation"), b.named("ec_hue"))))
    val = b.mul(b.sock_out(hsv, 2), b.mx(b.mul(cvar, shade), 0.05))
    col = b.node("FunctionNodeCombineColor", {0: hue, 1: b.sock_out(hsv, 1), 2: val}, mode='HSV')
    cards = b.store(cards, "needle_color", b.sock_out(col), 'FLOAT_COLOR')
    cards = b.store(cards, "leaf_coat", b.I("Leaf Gloss"))
    cards = b.store(cards, "leaf_sheen", b.I("Leaf Sheen"))
    rm = b.node("GeometryNodeRemoveAttribute", {"Geometry": cards, "Name": "ec_*"})
    b._set_menu(rm, "pattern_mode", 'WILDCARD', "Wildcard")
    cards = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": b.sock_out(rm), "Material": b.I("Leaf Material")}))
    is_vp = b.sock_out(b.node("GeometryNodeIsViewport"))
    show = b.bool_op('AND', b.I("Leaves"), b.bool_op('OR', b.I("Visible in Viewport"), b.bool_op('NOT', is_vp)))
    foliage = b.switch(show, None, cards)

    # ------------------------------------------------------------------ stems
    b.section("stems")
    nst = b.mx(b.math('ROUND', b.mul(b.I("Stems per Metre"), W)), 3.0)
    sp = b.node("GeometryNodePoints", {"Count": nst})
    si = b.index()
    bx = b.mul(b.mul(W, 0.25), b.rand(-1.0, 1.0, si, b.seed(501)))
    by = b.mul(b.mul(Dp, 0.25), b.rand(-1.0, 1.0, si, b.seed(502)))
    spg = b.store(b.sock_out(sp), "ec_b", b.xyz(bx, by, 0.0), 'FLOAT_VECTOR')
    stems = b.instance_realize(spg, b.line_template(3))
    us = b.spline_factor()
    base = b.named("ec_b", 'FLOAT_VECTOR')
    bxx, byy, _ = b.sep(base)
    # fan out a little but stay well inside the foliage shell
    top = b.xyz(b.mul(bxx, 1.35), b.mul(byy, 1.35), b.mul(b.I("Stem Height"), H))
    spos = b.vadd(base, b.vscale(b.vmath('SUBTRACT', top, base), us))
    stems = b.set_position(stems, pos=spos)
    stems = b.set_radius(stems, b.mul(b.I("Stem Radius"), b.sub(1.0, b.mul(us, 0.6))))
    sq = b.node("GeometryNodeCurvePrimitiveCircle", {"Resolution": 4, "Radius": 1.0})
    cap = b.node("GeometryNodeCaptureAttribute", domain='POINT')
    cap.capture_items.new('FLOAT', "UV X")
    b.feed(b.sock_in(cap, "Geometry"), b.sock_out(sq))
    b.links.new(b.spline_factor(), b.sock_in(cap, "UV X"))
    capl = b.node("GeometryNodeCaptureAttribute", domain='POINT')
    capl.capture_items.new('FLOAT', "UV Y")
    b.feed(b.sock_in(capl, "Geometry"), stems)
    b.links.new(b.sock_out(b.node("GeometryNodeSplineParameter"), "Length"), b.sock_in(capl, "UV Y"))
    smesh = b.node("GeometryNodeCurveToMesh", {"Curve": b.sock_out(capl, 0), "Profile Curve": b.sock_out(cap, 0),
                                               "Scale": b.sock_out(b.node("GeometryNodeInputRadius")), "Fill Caps": False})
    sm = b.store(b.sock_out(smesh), "UVMap", b.xyz(b.sock_out(cap, "UV X"), b.mul(b.sock_out(capl, "UV Y"), 0.5), 0.0),
                 'FLOAT2', 'CORNER')
    sm = b.store(sm, "bark_r", b.I("Stem Radius"))
    sm = b.store(sm, "bark_level", 1.0)
    rms = b.node("GeometryNodeRemoveAttribute", {"Geometry": sm, "Name": "ec_*"})
    b._set_menu(rms, "pattern_mode", 'WILDCARD', "Wildcard")
    sm = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": b.sock_out(rms), "Material": b.I("Bark Material")}))

    b.feed(b.sock_in(go, 0), b.join(sm, foliage))
    go.location = (b.col * 190 + 300, b.section_y)
    b.gi.location = (-400, 0)
    return tree


def ensure_hedge_group(force=False):
    tree = bpy.data.node_groups.get(GROUP_NAME)
    if tree and not force and tree.get("easy_conifer_hedge_version") == NODES_VERSION:
        return tree
    return build_hedge_group()
