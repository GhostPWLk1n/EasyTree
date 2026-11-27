# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — "Broadleaf Generator" geometry-node group
# (birch, poplar, willow, maple, ash, linden).
# Copyright (C) 2026 Pavel Fomin
"""Builds the "Broadleaf Generator" node group.

Geometry:  leaning, wavy trunk that runs to *Leader Height* (lower values make
           a decurrent crown of several stems); scaffold branches in a spiral
           or in opposite decussate pairs, each long enough to reach an
           elliptical crown outline (*Crown Width*); they rise, arch over
           (*Arch*) and may turn their tips up (*Tip Upturn*); second-order
           branches.
Cards:     leafy twigs are curves that bend from the branch direction towards
           the ground (*Weeping*); cross-board cards are chained along them
           every *Card Length*, so leaves keep their real size even on 3 m
           willow curtains (atlas tiles 0, 1); short-shoot rosettes are
           single quads (tiles 2, 3).
"""

import math

import bpy

from .nodes_builder import NB, _build_interface, _retire, interface_defaults as _defaults

GROUP_NAME = "Broadleaf Generator"
LEGACY_GROUP_NAMES = ("Birch Generator",)
NODES_VERSION = 8

D = math.radians

INTERFACE = [
    ("Shape", [
        ("Height", 'FLOAT', 16.0, 1.0, 40.0, 'DISTANCE', "Total height of the tree"),
        ("Trunk Radius", 'FLOAT', 0.17, 0.01, 1.5, 'DISTANCE', "Trunk radius at the base"),
        ("Crown Base", 'FLOAT', 0.3, 0.0, 0.9, 'FACTOR', "Bare part of the trunk below the crown, as a fraction of height"),
        ("Lean", 'FLOAT', D(4), 0.0, D(30), 'ANGLE', "Lean of the trunk"),
        ("Trunk Wiggle", 'FLOAT', 0.3, 0.0, 2.0, 'FACTOR', "Waviness of the trunk"),
        ("Leader Height", 'FLOAT', 0.97, 0.3, 1.0, 'FACTOR', "Where the main trunk ends; lower — the crown splits into several stems"),
        ("Stems", 'INT', 1, 1, 60, 'NONE', "Stems from the ground: 1 — tree, more — shrub or multi-stem tree"),
        ("Stem Spread", 'FLOAT', D(25), 0.0, D(80), 'ANGLE', "Outward tilt of the stems (when Stems > 1)"),
        ("Seed", 'INT', 0, 0, 100000, 'NONE', "Random seed"),
    ]),
    ("Branches", [
        ("Branch Count", 'INT', 48, 3, 300, 'NONE', "Scaffold branches along the crown (spiral)"),
        ("Branch Length", 'FLOAT', 0.85, 0.1, 1.5, 'FACTOR', "Branch reach: 1 — tips touch the crown outline"),
        ("Crown Width", 'FLOAT', 0.5, 0.08, 1.6, 'FACTOR', "Crown diameter relative to tree height (elliptical outline)"),
        ("Opposite", 'BOOLEAN', False, None, None, None, "Opposite decussate branching (maple, ash) instead of a spiral"),
        ("Angle Bottom", 'FLOAT', D(72), 0.0, D(150), 'ANGLE', "Branch angle from vertical at the bottom of the crown"),
        ("Angle Top", 'FLOAT', D(18), 0.0, D(150), 'ANGLE', "Branch angle from vertical near the top"),
        ("Arch", 'FLOAT', 0.35, -0.5, 2.0, 'NONE', "How much branches arch over and down towards their tips"),
        ("Tip Upturn", 'FLOAT', 0.0, -1.0, 2.0, 'NONE', "How much branch tips turn up (ash, linden)"),
        ("Branch Thickness", 'FLOAT', 0.03, 0.002, 0.2, 'NONE', "Branch base radius relative to its length"),
        ("Branch Jitter", 'FLOAT', 0.2, 0.0, 1.0, 'FACTOR', "Random variation of length, angle and curvature"),
        ("Branch Resolution", 'INT', 9, 3, 48, 'NONE', "Points per scaffold branch"),
    ]),
    ("Secondary Branches", [
        ("Secondary Density", 'FLOAT', 3.5, 0.0, 20.0, 'NONE', "Second-order branches per metre of scaffold branch"),
        ("Secondary Length", 'FLOAT', 0.45, 0.0, 1.5, 'FACTOR', "Length relative to the parent branch"),
        ("Secondary Angle", 'FLOAT', D(50), 0.0, 1.6, 'ANGLE', "Angle to the parent branch"),
        ("Secondary Droop", 'FLOAT', 0.35, -0.5, 2.0, 'NONE', "How much second-order branches sag"),
    ]),
    ("Leaves", [
        ("Leaves", 'BOOLEAN', True, None, None, None, "Generate leaf cards"),
        ("Twig Density", 'FLOAT', 7.0, 0.0, 40.0, 'NONE', "Leafy twigs per metre of branch"),
        ("Twig Length", 'FLOAT', 0.6, 0.05, 6.0, 'DISTANCE', "Length of the leafy twigs (long — willow curtains)"),
        ("Weeping", 'FLOAT', 0.75, 0.0, 1.0, 'FACTOR', "0 — twigs follow the branch, 1 — twigs bend to hang straight down"),
        ("Card Length", 'FLOAT', 0.6, 0.05, 3.0, 'DISTANCE', "Real length of one twig card; cards are chained along longer twigs"),
        ("Card Size", 'FLOAT', 1.0, 0.2, 3.0, 'FACTOR', "Twig card size multiplier"),
        ("Twig Wood", 'BOOLEAN', False, None, None, None, "Also build thin twig geometry under the cards"),
        ("Flatness", 'FLOAT', 0.0, 0.0, 1.0, 'FACTOR', "Height of the second board of twig crosses: 0 — full cross, 1 — single card"),
        ("Spray Size", 'FLOAT', 0.3, 0.02, 2.0, 'DISTANCE', "Size of the leaf-rosette cards (single quads)"),
        ("Spray Spacing", 'FLOAT', 0.25, 0.02, 3.0, 'DISTANCE', "Distance between leaf rosettes along the branches"),
        ("Bare Inner Part", 'FLOAT', 0.12, 0.0, 1.0, 'FACTOR', "Inner part of scaffold branches without leaves"),
        ("Leaf Color", 'RGBA', (0.062, 0.150, 0.024, 1.0), None, None, None,
         "Leaf colour (the baked texture is re-tinted towards it; yellow for autumn)"),
        ("Color Variation", 'FLOAT', 0.2, 0.0, 1.0, 'FACTOR', "Random brightness variation per card"),
        ("Hue Variation", 'FLOAT', 0.03, 0.0, 0.3, 'FACTOR', "Random hue shift per card"),
        ("Inner Shade", 'FLOAT', 0.45, 0.0, 1.0, 'FACTOR', "Leaves near the trunk / inside the crown are darker, outer ones lighter"),
        ("Top Light", 'FLOAT', 0.15, 0.0, 1.0, 'FACTOR', "Upper part of the crown is lighter, lower part darker"),
        ("Edge Color", 'RGBA', (0.12, 0.22, 0.035, 1.0), None, None, None, "Tint of the leaves on the crown surface (fresh growth)"),
        ("Edge Color Amount", 'FLOAT', 0.15, 0.0, 1.0, 'FACTOR', "How strongly the crown surface is tinted with Edge Color"),
        ("Leaf Gloss", 'FLOAT', 0.15, 0.0, 1.0, 'FACTOR', "Glossy wax coating of the leaves (Coat layer)"),
        ("Leaf Sheen", 'FLOAT', 0.0, 0.0, 1.0, 'FACTOR', "Velvety hairy leaves (Sheen layer)"),
        ("Visible in Viewport", 'BOOLEAN', True, None, None, None, "Show leaf cards in the viewport (always rendered)"),
    ]),
    ("Wind", [
        ("Wind", 'BOOLEAN', False, None, None, None, "Animate wind sway"),
        ("Wind Direction", 'FLOAT', 0.0, -6.2832, 6.2832, 'ANGLE', "Wind direction in the XY plane"),
        ("Wind Strength", 'FLOAT', 0.3, 0.0, 5.0, 'NONE', "Sway amplitude"),
        ("Wind Speed", 'FLOAT', 0.5, 0.0, 10.0, 'NONE', "Sway speed"),
    ]),
    ("Mesh", [
        ("Trunk Resolution", 'INT', 12, 3, 64, 'NONE', "Trunk cross-section vertices"),
        ("Branch Profile", 'INT', 5, 3, 32, 'NONE', "Branch cross-section vertices"),
        ("Bark Material", 'MATERIAL', None, None, None, None, "Material for trunk and branches"),
        ("Leaf Material", 'MATERIAL', None, None, None, None, "Material for the leaf cards"),
    ]),
]


def interface_defaults():
    return _defaults(INTERFACE)


def build_broadleaf_group():
    _retire(GROUP_NAME)
    tree = bpy.data.node_groups.new(GROUP_NAME, 'GeometryNodeTree')
    tree.description = "Broadleaf tree generator — Easy Conifer"
    _build_interface(tree, INTERFACE)
    tree["easy_conifer_broadleaf_version"] = NODES_VERSION
    try:
        tree.is_modifier = True
    except Exception:
        pass

    b = NB(tree)
    b.gi = b.node("NodeGroupInput")
    go = b.node("NodeGroupOutput")
    H = b.I("Height")
    Z = (0.0, 0.0, 1.0)
    TWO_PI = 2.0 * math.pi

    # ---------------------------------------------------------------- trunk
    b.section("trunk")
    nst = b.mx(b.I("Stems"), 1.0)
    multi = b.switch(b.cmp('GREATER_THAN', b.I("Stems"), 1.5), 0.0, 1.0, 'FLOAT')
    wig = b.mul(b.mul(b.I("Trunk Wiggle"), H), 0.012)

    def stem_az(k):
        # k is a field (stem index); a constant 0 for a single trunk
        return b.add(b.rand(0.0, TWO_PI, k, b.seed(1)), b.mul(multi, b.mul(k, 2.39996323)))

    def stem_tan(k):
        spread = b.mul(b.I("Stem Spread"), b.rand(0.55, 1.0, k, b.seed(7)))
        return b.math('TANGENT', b.mn(b.lerp(multi, b.I("Lean"), b.mx(spread, b.I("Lean"))), 1.45))

    def trunk_offset(z, k):
        """Horizontal offset of stem k's axis at height z (a field)."""
        n = b.node("ShaderNodeTexNoise", {"Scale": 1.0, "Detail": 0.0}, noise_dimensions='3D')
        b.feed(b.sock_in(n, "Vector"), b.xyz(b.div(z, b.mx(b.mul(H, 0.55), 0.5)),
                                              b.add(b.mul(b.I("Seed"), 0.731), b.mul(k, 1.37)), 0.0))
        nx, ny, _ = b.sep(b.sock_out(n, "Color"))
        a = stem_az(k)
        # single trunk: gentle bow; stems of a shrub: straight from a small ring
        bow = b.lerp(multi, b.math('SQRT', b.clamp01(b.div(z, H))), 1.0)
        lz = b.add(b.mul(stem_tan(k), b.mul(z, bow)), b.mul(multi, b.mul(b.I("Trunk Radius"), 2.5)))
        return b.xyz(b.add(b.mul(b.cos(a), lz), b.mul(b.sub(nx, 0.5), wig)),
                     b.add(b.mul(b.sin(a), lz), b.mul(b.sub(ny, 0.5), wig)), 0.0)

    top = b.mul(H, b.I("Leader Height"))
    # 1 for an excurrent leader, 0 for a crown that splits into stems
    excurrent = b.clamp01(b.div(b.sub(b.I("Leader Height"), 0.4), 0.55))

    def trunk_radius(z):
        """Trunk radius at absolute height z; a short (decurrent) trunk keeps its thickness."""
        tzr = b.clamp01(b.div(z, top))
        taper = b.lerp(excurrent, b.sub(1.0, b.mul(0.55, tzr)), b.pow(b.sub(1.0, tzr), 1.05))
        base = b.mul(b.I("Trunk Radius"), taper)
        flare = b.pow(b.clamp01(b.sub(1.0, b.div(z, b.mul(H, 0.035)))), 2.0)
        return b.mx(b.mul(base, b.add(1.0, b.mul(flare, 0.6))), 0.004)

    stem_pts = b.store(b.sock_out(b.node("GeometryNodePoints", {"Count": nst})), "ec_k", b.index())
    trunk = b.instance_realize(stem_pts, b.line_template(b.mx(b.div(H, 0.3), 12.0)))
    tz_ = b.mul(b.spline_factor(), top)
    trunk = b.set_position(trunk, pos=b.vadd(trunk_offset(tz_, b.named("ec_k")), b.xyz(0.0, 0.0, tz_)))
    tzabs = b.sep(b.position())[2]
    trunk = b.set_radius(trunk, trunk_radius(tzabs))
    trunk = b.store(trunk, "ec_u", b.div(tzabs, H))
    trunk = b.store(trunk, "ec_kind", 2.0)

    # ----------------------------------------------------- scaffold branches
    b.section("scaffold origins")
    z0 = b.mul(H, b.I("Crown Base"))
    zc = b.sub(b.mn(b.mul(top, 0.985), b.mul(H, 0.94)), z0)
    N = b.I("Branch Count")
    pts = b.node("GeometryNodePoints", {"Count": N})
    i = b.index()
    bj = b.I("Branch Jitter")
    opp = b.switch(b.I("Opposite"), 0.0, 1.0, 'FLOAT')
    slot = b.lerp(opp, i, b.floor(b.div(i, 2.0)))            # pair index when opposite
    nslots = b.lerp(opp, N, b.math('CEIL', b.div(N, 2.0)))
    t = b.clamp01(b.add(b.div(b.add(slot, 0.5), nslots),
                        b.mul(b.div(b.lerp(opp, 0.6, 0.25), nslots), b.rand(-1.0, 1.0, slot, b.seed(2)))))
    z = b.add(z0, b.mul(t, zc))
    az_spiral = b.mul(i, 2.39996323)
    az_opp = b.add(b.mul(slot, math.pi / 2), b.mul(b.math('FLOORED_MODULO', i, 2.0), math.pi))
    az = b.add(b.lerp(opp, az_spiral, az_opp), b.mul(b.lerp(opp, 0.5, 0.25), b.rand(-1.0, 1.0, i, b.seed(3))))
    kb = b.math('FLOORED_MODULO', b.add(i, b.floor(b.rand(0.0, 1000.0, slot, b.seed(9)))), nst)   # stem of this branch
    # on a shrub, branches mostly face away from the centre, around their stem's direction
    az = b.lerp(multi, az, b.add(stem_az(kb), b.rand(-1.5, 1.5, i, b.seed(8))))
    th = b.add(b.lerp(t, b.I("Angle Bottom"), b.I("Angle Top")), b.mul(b.mul(bj, 0.6), b.rand(-1.0, 1.0, i, b.seed(5))))
    # reach: distance from the trunk along the initial direction to the crown ellipse
    ez = b.mul(b.add(z0, H), 0.5)
    ea = b.mx(b.mul(b.sub(H, z0), 0.5), 0.1)
    eR = b.mx(b.mul(b.mul(b.I("Crown Width"), H), 0.5), 0.1)
    sn, cs = b.sin(th), b.cos(th)
    qa = b.add(b.div(b.mul(sn, sn), b.mul(eR, eR)), b.div(b.mul(cs, cs), b.mul(ea, ea)))
    dz = b.sub(z, ez)
    qb = b.div(b.mul(b.mul(2.0, cs), dz), b.mul(ea, ea))
    qc = b.sub(b.div(b.mul(dz, dz), b.mul(ea, ea)), 1.0)
    disc = b.mx(b.sub(b.mul(qb, qb), b.mul(b.mul(4.0, qa), qc)), 0.0)
    reach = b.div(b.add(b.mul(qb, -1.0), b.math('SQRT', disc)), b.mul(2.0, qa))
    hx, hy, _ = b.sep(trunk_offset(z, kb))           # the stem is off-axis: shorten/lengthen the reach
    reach = b.mx(b.sub(reach, b.add(b.mul(hx, b.cos(az)), b.mul(hy, b.sin(az)))), b.mul(reach, 0.2))
    L = b.mul(b.mul(reach, b.I("Branch Length")), b.add(1.0, b.mul(bj, b.rand(-1.0, 1.0, i, b.seed(4)))))
    L = b.mx(L, 0.15)
    curv = b.mul(b.mul(bj, 1.5), b.rand(-1.0, 1.0, i, b.seed(6)))
    pg = b.sock_out(pts)
    pg = b.store(pg, "ec_z", z)
    pg = b.store(pg, "ec_az", az)
    pg = b.store(pg, "ec_len", L)
    pg = b.store(pg, "ec_th", th)
    pg = b.store(pg, "ec_cv", curv)
    pg = b.store(pg, "ec_k", kb)

    b.section("scaffold branches")
    br = b.instance_realize(pg, b.line_template(b.I("Branch Resolution")))
    u = b.spline_factor()
    Lb, thb, azb, zb = b.named("ec_len"), b.named("ec_th"), b.named("ec_az"), b.named("ec_z")
    azu = b.add(azb, b.mul(b.named("ec_cv"), b.mul(u, 0.5)))
    rho = b.mul(b.mul(Lb, u), b.sin(thb))
    rise = b.mul(Lb, b.add(b.sub(b.mul(u, b.cos(thb)), b.mul(b.I("Arch"), b.mul(u, u))),
                           b.mul(b.I("Tip Upturn"), b.mul(u, b.mul(u, u)))))
    basep = b.vadd(trunk_offset(zb, b.named("ec_k")), b.xyz(0.0, 0.0, zb))
    br = b.set_position(br, pos=b.vadd(basep, b.xyz(b.mul(b.cos(azu), rho), b.mul(b.sin(azu), rho), rise)))
    r0 = b.mn(b.mul(b.I("Branch Thickness"), Lb), b.mul(trunk_radius(zb), 0.7))
    br = b.set_radius(br, b.add(b.mul(r0, b.sub(1.0, b.mul(u, 0.85))), 0.002))
    br = b.store(br, "ec_u", u)
    br = b.store(br, "ec_kind", 0.0)

    # --------------------------------------------------- secondary branches
    b.section("secondary origins")
    c2p = b.node("GeometryNodeCurveToPoints", mode='LENGTH')
    b.feed(b.sock_in(c2p, "Curve"), br)
    b.feed(b.sock_in(c2p, "Length"), b.div(1.0, b.mx(b.I("Secondary Density"), 0.01)))
    sp = b.sock_out(c2p, "Points")
    T = b.sock_out(c2p, "Tangent")
    pu = b.named("ec_u")
    keep = b.bool_op('AND', b.cmp('GREATER_THAN', pu, 0.12), b.cmp('LESS_THAN', pu, 0.93))
    keep = b.bool_op('AND', keep, b.cmp('GREATER_THAN', b.I("Secondary Density"), 0.05))
    sp = b.store(sp, "ec_t", T, 'FLOAT_VECTOR')
    sp = b.store(sp, "ec_pr", b.sock_out(b.node("GeometryNodeInputRadius")))
    sp = b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": sp, "Selection": b.bool_op('NOT', keep)}))
    si = b.index()
    Tn = b.named("ec_t", 'FLOAT_VECTOR')
    side = b.sub(b.mul(b.math('FLOORED_MODULO', si, 2.0), 2.0), 1.0)
    sv = b.vscale(b.vnorm(b.vadd(b.vcross(Tn, Z), (0.0003, 0.0002, 0.0))), side)
    sa = b.add(b.I("Secondary Angle"), b.mul(0.2, b.rand(-1.0, 1.0, si, b.seed(11))))
    sdir = b.vnorm(b.vadd(b.vadd(b.vscale(Tn, b.cos(sa)), b.vscale(sv, b.sin(sa))),
                          b.xyz(0.0, 0.0, b.rand(-0.15, 0.35, si, b.seed(12)))))
    spu = b.named("ec_u")
    sl = b.mul(b.mul(b.I("Secondary Length"), b.named("ec_len")), b.pow(b.mx(b.sub(1.0, spu), 0.0), 0.6))
    sl = b.mul(sl, b.mul(b.add(0.4, b.mul(0.6, b.clamp01(b.mul(spu, 3.0)))), b.rand(0.7, 1.15, si, b.seed(13))))
    sl = b.mx(sl, 0.08)
    sp = b.store(sp, "ec_o", b.position(), 'FLOAT_VECTOR')
    sp = b.store(sp, "ec_d", sdir, 'FLOAT_VECTOR')
    sp = b.store(sp, "ec_sl", sl)

    b.section("secondary branches")
    sec = b.instance_realize(sp, b.line_template(4))
    us = b.spline_factor()
    slb = b.named("ec_sl")
    spos = b.vadd(b.vadd(b.named("ec_o", 'FLOAT_VECTOR'), b.vscale(b.named("ec_d", 'FLOAT_VECTOR'), b.mul(slb, us))),
                  b.xyz(0.0, 0.0, b.mul(b.mul(b.I("Secondary Droop"), -1.0), b.mul(slb, b.mul(us, us)))))
    sec = b.set_position(sec, pos=spos)
    sec = b.set_radius(sec, b.add(b.mul(b.mul(b.named("ec_pr"), 0.4), b.sub(1.0, b.mul(us, 0.8))), 0.0015))
    sec = b.store(sec, "ec_u", us)
    sec = b.store(sec, "ec_len", slb)
    sec = b.store(sec, "ec_kind", 1.0)

    skel = b.join(trunk, br, sec)
    skel = b.store(skel, "bark_r", b.sock_out(b.node("GeometryNodeInputRadius")))
    # branch order for the bark shader: 0 trunk, 1 scaffold (white), 2 secondary (dark)
    k = b.named("ec_kind")
    level = b.switch(b.cmp('EQUAL', k, 1.0), b.switch(b.cmp('EQUAL', k, 0.0), 0.0, 1.0, 'FLOAT'), 2.0, 'FLOAT')
    skel = b.store(skel, "bark_level", level)

    # ----------------------------------------------------------------- bark
    b.section("bark mesh")
    kind = b.named("ec_kind")

    def to_mesh(sel, resolution, caps=True):
        sepg = b.node("GeometryNodeSeparateGeometry", {"Geometry": skel, "Selection": sel}, domain='CURVE')
        circ = b.node("GeometryNodeCurvePrimitiveCircle", {"Resolution": resolution, "Radius": 1.0})
        cap_p = b.node("GeometryNodeCaptureAttribute", domain='POINT')
        cap_p.capture_items.new('FLOAT', "UV X")
        b.feed(b.sock_in(cap_p, "Geometry"), b.sock_out(circ))
        b.links.new(b.spline_factor(), b.sock_in(cap_p, "UV X"))
        cap_c = b.node("GeometryNodeCaptureAttribute", domain='POINT')
        cap_c.capture_items.new('FLOAT', "UV Y")
        b.feed(b.sock_in(cap_c, "Geometry"), b.sock_out(sepg, "Selection"))
        b.links.new(b.sock_out(b.node("GeometryNodeSplineParameter"), "Length"), b.sock_in(cap_c, "UV Y"))
        c2m = b.node("GeometryNodeCurveToMesh", {"Curve": b.sock_out(cap_c, 0), "Profile Curve": b.sock_out(cap_p, 0),
                                                 "Scale": b.sock_out(b.node("GeometryNodeInputRadius")),
                                                 "Fill Caps": caps})
        uv = b.xyz(b.sock_out(cap_p, "UV X"), b.mul(b.sock_out(cap_c, "UV Y"), 0.5), 0.0)
        return b.store(b.sock_out(c2m), "UVMap", uv, 'FLOAT2', 'CORNER')

    bark = b.join(to_mesh(b.cmp('EQUAL', kind, 2.0), b.I("Trunk Resolution")),
                  to_mesh(b.cmp('EQUAL', kind, 0.0), b.I("Branch Profile")),
                  to_mesh(b.cmp('EQUAL', kind, 1.0), 4, caps=False))
    bark = b.sock_out(b.node("GeometryNodeSetShadeSmooth", {"Mesh": bark}))
    rm = b.node("GeometryNodeRemoveAttribute", {"Geometry": bark, "Name": "ec_*"})
    b._set_menu(rm, "pattern_mode", 'WILDCARD', "Wildcard")
    bark = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": b.sock_out(rm),
                                                          "Material": b.I("Bark Material")}))

    # ---------------------------------------------------------- leaf cards
    b.section("leaf cards")

    def quad(vertical=False, vfac=None):
        grid = b.node("GeometryNodeMeshGrid", {"Size X": 1.0, "Size Y": 1.0, "Vertices X": 2, "Vertices Y": 2})
        g = b.store(b.sock_out(grid, "Mesh"), "UVMap", b.sock_out(grid, "UV Map"), 'FLOAT2', 'CORNER')
        ins = {"Geometry": g, "Translation": (0.0, 0.5, 0.0)}
        if vertical:
            ins["Rotation"] = (0.0, math.pi / 2, 0.0)
            ins["Scale"] = b.xyz(vfac, 1.0, 1.0)
        return b.sock_out(b.node("GeometryNodeTransform", ins))

    vf = b.mx(b.sub(1.0, b.I("Flatness")), 0.05)
    cross = b.switch(b.cmp('GREATER_THAN', b.I("Flatness"), 0.95), b.join(quad(), quad(True, vf)), quad())
    single = quad()

    def orient(direction, roll, euler=None):
        r = b.node("FunctionNodeAlignRotationToVector", {"Vector": direction}, axis='Y')
        loc = b.node("FunctionNodeEulerToRotation", {"Euler": euler if euler is not None else b.xyz(0.0, roll, 0.0)})
        r = b.node("FunctionNodeRotateRotation", {"Rotation": b.sock_out(r), "Rotate By": b.sock_out(loc)},
                   rotation_space='LOCAL')
        return b.sock_out(r)

    def flip(idx, k):
        return b.sub(b.mul(b.cmp('GREATER_THAN', b.rand(0.0, 1.0, idx, b.seed(k)), 0.5), 2.0), 1.0)

    def outer_points(spacing):
        """Points along scaffold (outer part) and secondary branches."""
        c = b.node("GeometryNodeCurveToPoints", mode='LENGTH')
        b.feed(b.sock_in(c, "Curve"), b.join(trunk, br, sec))
        b.feed(b.sock_in(c, "Length"), b.mx(spacing, 0.01))
        p = b.store(b.sock_out(c, "Points"), "ec_t", b.sock_out(c, "Tangent"), 'FLOAT_VECTOR')
        k = b.named("ec_kind")
        ok = b.bool_op('OR', b.cmp('EQUAL', k, 1.0),
                       b.bool_op('AND', b.cmp('EQUAL', k, 0.0), b.cmp('GREATER_EQUAL', b.named("ec_u"), b.I("Bare Inner Part"))))
        # top of the leader; on shrubs the whole upper half of every stem is leafy
        leader = b.bool_op('AND', b.cmp('EQUAL', k, 2.0),
                           b.cmp('GREATER_THAN', b.named("ec_u"), b.lerp(multi, 0.86, b.mul(b.I("Leader Height"), 0.45))))
        ok = b.bool_op('OR', ok, leader)
        return b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": p, "Selection": b.bool_op('NOT', ok)}))

    # leafy twigs: curves bending from the branch direction towards the ground
    tw = outer_points(b.div(1.0, b.mx(b.I("Twig Density"), 0.01)))
    ti = b.index()
    jit = b.xyz(b.rand(-0.6, 0.6, ti, b.seed(21)), b.rand(-0.6, 0.6, ti, b.seed(22)), b.rand(-0.25, 0.45, ti, b.seed(20)))
    d0 = b.vnorm(b.vadd(b.named("ec_t", 'FLOAT_VECTOR'), jit))
    weep = b.I("Weeping")
    d1 = b.vnorm(b.vadd(b.vscale(d0, b.sub(1.0, weep)), b.xyz(0.0, 0.0, b.mul(weep, -1.5))))
    # strongly weeping twigs start bending down right away (no spikes above the crown)
    d0 = b.vnorm(b.vlerp(b.mul(b.mul(weep, weep), 0.45), d0, d1))
    tl = b.mx(b.mul(b.I("Twig Length"), b.rand(0.7, 1.2, ti, b.seed(23))), 0.02)
    tw = b.store(tw, "ec_o", b.position(), 'FLOAT_VECTOR')
    tw = b.store(tw, "ec_d0", d0, 'FLOAT_VECTOR')
    tw = b.store(tw, "ec_d1", d1, 'FLOAT_VECTOR')
    tw = b.store(tw, "ec_tl", tl)
    twc = b.instance_realize(tw, b.line_template(6))
    ut = b.spline_factor()
    td0, td1, ttl = b.named("ec_d0", 'FLOAT_VECTOR'), b.named("ec_d1", 'FLOAT_VECTOR'), b.named("ec_tl")
    tpos = b.vadd(b.named("ec_o", 'FLOAT_VECTOR'),
                  b.vscale(b.vadd(b.vscale(td0, ut), b.vscale(b.vmath('SUBTRACT', td1, td0), b.mul(0.5, b.mul(ut, ut)))), ttl))
    twc = b.set_position(twc, pos=tpos)
    twc = b.store(twc, "ec_tu", ut)
    twc = b.store(twc, "ec_kind", 3.0)
    twc = b.set_radius(twc, b.add(b.mul(0.004, b.sub(1.0, b.mul(ut, 0.7))), 0.001))
    twood = b.node("GeometryNodeCurveToMesh", {"Curve": twc, "Fill Caps": False,
        "Profile Curve": b.sock_out(b.node("GeometryNodeCurvePrimitiveCircle", {"Resolution": 3, "Radius": 1.0})),
        "Scale": b.sock_out(b.node("GeometryNodeInputRadius"))})
    twood = b.store(b.sock_out(twood), "bark_level", 2.0)
    twood = b.store(twood, "bark_r", 0.003)
    rmw = b.node("GeometryNodeRemoveAttribute", {"Geometry": twood, "Name": "ec_*"})
    b._set_menu(rmw, "pattern_mode", 'WILDCARD', "Wildcard")
    twood = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": b.sock_out(rmw), "Material": b.I("Bark Material")}))
    twood = b.switch(b.I("Twig Wood"), None, twood)
    # cards every Card Length along each twig, oriented along the twig at the card's middle
    cl = b.mx(b.I("Card Length"), 0.02)
    cc2p = b.node("GeometryNodeCurveToPoints", mode='LENGTH')
    b.feed(b.sock_in(cc2p, "Curve"), twc)
    b.feed(b.sock_in(cc2p, "Length"), cl)
    cpts = b.sock_out(cc2p, "Points")
    # drop a card that would start with less than half a card of twig left (keep the first)
    rest = b.mul(b.sub(1.0, b.named("ec_tu")), b.named("ec_tl"))
    extra = b.bool_op('AND', b.cmp('GREATER_THAN', b.named("ec_tu"), 0.001), b.cmp('LESS_THAN', rest, b.mul(cl, 0.5)))
    cpts = b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": cpts, "Selection": extra}))
    ci = b.index()
    umid = b.clamp01(b.add(b.named("ec_tu"), b.div(b.mul(cl, 0.5), b.named("ec_tl"))))
    cdir = b.vnorm(b.vadd(b.named("ec_d0", 'FLOAT_VECTOR'),
                          b.vscale(b.vmath('SUBTRACT', b.named("ec_d1", 'FLOAT_VECTOR'), b.named("ec_d0", 'FLOAT_VECTOR')), umid)))
    tsc = b.mul(b.mul(cl, b.I("Card Size")), b.rand(0.85, 1.15, ci, b.seed(23)))
    trot = orient(cdir, b.rand(0.0, math.pi, ci, b.seed(24)))
    twigs = b.node("GeometryNodeInstanceOnPoints", {"Points": cpts, "Instance": cross, "Rotation": trot,
                                                    "Scale": b.xyz(b.mul(tsc, flip(ci, 25)), tsc, tsc)})
    twigs = b.store(b.sock_out(twigs), "ec_tile", b.floor(b.rand(0.0, 1.999, ci, b.seed(26))), 'FLOAT', 'INSTANCE')
    twigs = b.store(twigs, "ec_age", b.rand(0.0, 1.0, ci, b.seed(27)), 'FLOAT', 'INSTANCE')
    twigs = b.store(twigs, "ec_pos", b.position(), 'FLOAT_VECTOR', 'INSTANCE')
    twigs = b.store(twigs, "ec_hue", b.rand(-1.0, 1.0, ci, b.seed(28)), 'FLOAT', 'INSTANCE')

    # leaf rosettes (short shoots) as single quads
    ro = outer_points(b.I("Spray Spacing"))
    ri = b.index()
    rdir = b.vnorm(b.vadd(b.vadd(b.named("ec_t", 'FLOAT_VECTOR'), b.xyz(0.0, 0.0, b.rand(-0.2, 0.6, ri, b.seed(31)))),
                          b.xyz(b.rand(-0.8, 0.8, ri, b.seed(32)), b.rand(-0.8, 0.8, ri, b.seed(33)), 0.0)))
    rrot = orient(rdir, None, b.xyz(b.rand(-0.6, 0.6, ri, b.seed(34)), b.rand(-0.8, 0.8, ri, b.seed(35)), 0.0))
    rsc = b.mul(b.I("Spray Size"), b.rand(0.75, 1.2, ri, b.seed(36)))
    ros = b.node("GeometryNodeInstanceOnPoints", {"Points": ro, "Instance": single, "Rotation": rrot,
                                                  "Scale": b.xyz(b.mul(rsc, flip(ri, 37)), rsc, rsc)})
    ros = b.store(b.sock_out(ros), "ec_tile", b.add(2.0, b.floor(b.rand(0.0, 1.999, ri, b.seed(38)))), 'FLOAT', 'INSTANCE')
    ros = b.store(ros, "ec_age", b.rand(0.0, 1.0, ri, b.seed(39)), 'FLOAT', 'INSTANCE')
    ros = b.store(ros, "ec_pos", b.position(), 'FLOAT_VECTOR', 'INSTANCE')
    ros = b.store(ros, "ec_hue", b.rand(-1.0, 1.0, ri, b.seed(40)), 'FLOAT', 'INSTANCE')

    cards = b.sock_out(b.node("GeometryNodeRealizeInstances", {"Geometry": b.join(twigs, ros)}))
    tile = b.named("ec_tile")
    u0, v0, _ = b.sep(b.named("UVMap", 'FLOAT_VECTOR'))
    uu = b.add(b.add(b.mul(u0, 0.49), 0.005), b.mul(b.math('FLOORED_MODULO', tile, 2.0), 0.5))
    vv = b.add(b.add(b.mul(v0, 0.49), 0.005), b.mul(b.floor(b.div(tile, 2.0)), 0.5))
    cards = b.store(cards, "UVMap", b.xyz(uu, vv, 0.0), 'FLOAT2', 'CORNER')
    # ---- leaf colour per card: crown position, edge tint, hue and brightness variation
    cp = b.named("ec_pos", 'FLOAT_VECTOR')
    cpx, cpy, cpz = b.sep(cp)
    rxy = b.vmath('LENGTH', b.xyz(cpx, cpy, 0.0))
    dzc = b.div(b.sub(cpz, ez), ea)
    rz = b.mul(eR, b.math('SQRT', b.mx(b.sub(1.0, b.mul(dzc, dzc)), 0.06)))   # crown radius at this height
    edge = b.clamp01(b.div(rxy, rz))                                          # 0 axis … 1 crown surface
    edge = b.mx(edge, b.clamp01(b.mul(b.sub(dzc, 0.55), 2.2)))                # the crown top is "surface" too
    tcrown = b.clamp01(b.div(b.sub(cpz, z0), b.mx(b.sub(H, z0), 0.1)))
    # inner leaves darker, outer ones brighter than the base colour (keeps the average brightness)
    shade = b.lerp(b.pow(edge, 0.8), b.sub(1.0, b.I("Inner Shade")), b.add(1.0, b.mul(b.I("Inner Shade"), 0.45)))
    shade = b.mul(shade, b.add(1.0, b.mul(b.I("Top Light"), b.sub(b.mul(tcrown, 2.0), 1.0))))
    cvar = b.add(1.0, b.mul(b.mul(b.I("Color Variation"), 2.0), b.sub(b.named("ec_age"), 0.5)))
    base_col = b.vlerp(b.mul(b.I("Edge Color Amount"), b.pow(edge, 1.5)), b.I("Leaf Color"), b.I("Edge Color"))
    hsv = b.node("FunctionNodeSeparateColor", {"Color": base_col}, mode='HSV')
    hue = b.math('FRACT', b.add(b.sock_out(hsv, 0), b.mul(b.I("Hue Variation"), b.named("ec_hue"))))
    val = b.mul(b.sock_out(hsv, 2), b.mx(b.mul(cvar, shade), 0.05))
    col = b.node("FunctionNodeCombineColor", {0: hue, 1: b.sock_out(hsv, 1), 2: val}, mode='HSV')
    cards = b.store(cards, "needle_color", b.sock_out(col), 'FLOAT_COLOR')
    cards = b.store(cards, "leaf_coat", b.I("Leaf Gloss"))
    cards = b.store(cards, "leaf_sheen", b.I("Leaf Sheen"))
    rm2 = b.node("GeometryNodeRemoveAttribute", {"Geometry": cards, "Name": "ec_*"})
    b._set_menu(rm2, "pattern_mode", 'WILDCARD', "Wildcard")
    cards = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": b.sock_out(rm2),
                                                           "Material": b.I("Leaf Material")}))
    is_vp = b.sock_out(b.node("GeometryNodeIsViewport"))
    show = b.bool_op('AND', b.I("Leaves"), b.bool_op('OR', b.I("Visible in Viewport"), b.bool_op('NOT', is_vp)))
    leaves = b.switch(show, None, cards)

    # ---------------------------------------------------------- wind + output
    b.section("output")
    result = b.join(bark, twood, leaves)
    p = b.position()
    px, py, pz = b.sep(p)
    tz = b.clamp01(b.div(pz, H))
    radial = b.div(b.vmath('LENGTH', b.xyz(px, py, 0.0)), H)
    time = b.sock_out(b.node("GeometryNodeInputSceneTime"), "Seconds")
    wspeed = b.I("Wind Speed")
    sway = b.add(0.65, b.mul(0.35, b.sin(b.mul(time, b.mul(wspeed, 2.7)))))
    wdir = b.xyz(b.cos(b.I("Wind Direction")), b.sin(b.I("Wind Direction")), 0.0)
    big = b.vscale(wdir, b.mul(b.mul(b.I("Wind Strength"), b.mul(tz, tz)), b.mul(sway, b.mul(H, 0.03))))
    noise = b.node("ShaderNodeTexNoise", {"Scale": 0.6, "Detail": 1.0}, noise_dimensions='4D')
    b.feed(b.sock_in(noise, "Vector"), p)
    b.feed(b.sock_in(noise, "W"), b.mul(time, wspeed))
    # birch twigs flutter more than conifer branches
    flutter = b.vscale(b.vadd(b.sock_out(noise, "Color"), (-0.5, -0.5, -0.5)),
                       b.mul(b.mul(b.I("Wind Strength"), radial), b.mul(H, 0.2)))
    result = b.set_position(result, offset=b.vadd(big, flutter), selection=b.I("Wind"))
    b.feed(b.sock_in(go, 0), result)
    go.location = (b.col * 190 + 300, b.section_y)
    b.gi.location = (-400, 0)
    return tree


def ensure_broadleaf_group(force=False):
    tree = bpy.data.node_groups.get(GROUP_NAME)
    if tree and not force and tree.get("easy_conifer_broadleaf_version") == NODES_VERSION:
        return tree
    return build_broadleaf_group()
