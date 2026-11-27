# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — procedural spruce / fir generator for Blender (Geometry Nodes).
# Copyright (C) 2026 Pavel Fomin
"""Builds the "Conifer Generator" geometry-node group from Python.

The tree is monopodial: one straight leader, branches in whorls, flat
second-order twigs as cross-board cards and sprays as single quads, both showing
baked high-poly twigs from a texture atlas (twig_baker.py).
"""

import math
import bpy

GROUP_NAME = "Conifer Generator"
CLUSTER_GROUP_NAME = "Conifer Needle Cluster"
NODES_VERSION = 9  # bump when the graph changes; stored on the group


# --------------------------------------------------------------------------
#  Tiny node-building helper
# --------------------------------------------------------------------------
class NB:
    def __init__(self, tree):
        self.tree = tree
        self.nodes = tree.nodes
        self.links = tree.links
        self.col = 0
        self.row = 0
        self.section_y = 0
        self.gi = None

    # ---- layout --------------------------------------------------------
    def section(self, label):
        """Start a new horizontal band of nodes (just for readability)."""
        self.section_y -= 900 if self.col else 0
        self.col = 0
        self.row = 0
        self._label = label

    def _place(self, node):
        node.location = (self.col * 190, self.section_y - self.row * 170)
        self.row += 1
        if self.row > 4:
            self.row = 0
            self.col += 1

    # ---- sockets -------------------------------------------------------
    @staticmethod
    def _enabled(sockets):
        return [s for s in sockets if s.enabled]

    def sock_in(self, node, key):
        if isinstance(key, int):
            return self._enabled(node.inputs)[key]
        for s in node.inputs:
            if s.enabled and s.name == key:
                return s
        for s in node.inputs:
            if s.name == key:
                return s
        raise KeyError("%s has no input %r" % (node.bl_idname, key))

    def sock_out(self, node, key=0):
        if isinstance(key, int):
            return self._enabled(node.outputs)[key]
        for s in node.outputs:
            if s.enabled and s.name == key:
                return s
        for s in node.outputs:
            if s.name == key:
                return s
        raise KeyError("%s has no output %r" % (node.bl_idname, key))

    def feed(self, sock, val):
        if val is None:
            return
        if isinstance(val, bpy.types.NodeSocket):
            self.links.new(val, sock)
        else:
            sock.default_value = val

    def node(self, idname, inputs=None, **props):
        n = self.nodes.new(idname)
        for k, v in props.items():
            if hasattr(n, k):
                setattr(n, k, v)
            else:  # Blender 5.x turned several enum properties into menu sockets
                self.sock_in(n, k.replace("_", " ").title()).default_value = v
        if inputs:
            items = inputs.items() if isinstance(inputs, dict) else enumerate(inputs)
            for k, v in items:
                self.feed(self.sock_in(n, k), v)
        self._place(n)
        return n

    def I(self, name):
        return self.sock_out(self.gi, name)

    # ---- scalar math ---------------------------------------------------
    def math(self, op, a, b=None, c=None, clamp=False):
        ins = [a] + ([b] if b is not None else []) + ([c] if c is not None else [])
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate(ins):
            self.feed(self.sock_in(n, i), v)
        return self.sock_out(n)

    def add(self, a, b): return self.math('ADD', a, b)
    def sub(self, a, b): return self.math('SUBTRACT', a, b)
    def mul(self, a, b): return self.math('MULTIPLY', a, b)
    def div(self, a, b): return self.math('DIVIDE', a, b)
    def pow(self, a, b): return self.math('POWER', a, b)
    def mn(self, a, b): return self.math('MINIMUM', a, b)
    def mx(self, a, b): return self.math('MAXIMUM', a, b)
    def floor(self, a): return self.math('FLOOR', a)
    def sin(self, a): return self.math('SINE', a)
    def cos(self, a): return self.math('COSINE', a)
    def madd(self, a, b, c): return self.math('MULTIPLY_ADD', a, b, c)
    def clamp01(self, a): return self.math('ADD', a, 0.0, clamp=True)

    def lerp(self, f, a, b):
        n = self.node("ShaderNodeMix", data_type='FLOAT', clamp_factor=False)
        self.feed(self.sock_in(n, "Factor"), f)
        self.feed(self.sock_in(n, "A"), a)
        self.feed(self.sock_in(n, "B"), b)
        return self.sock_out(n)

    def vlerp(self, f, a, b):
        n = self.node("ShaderNodeMix", data_type='VECTOR', clamp_factor=True)
        self.feed(self.sock_in(n, 0), f)
        self.feed(self.sock_in(n, 1), a)
        self.feed(self.sock_in(n, 2), b)
        return self.sock_out(n)

    def cmp(self, op, a, b):
        n = self.node("FunctionNodeCompare", data_type='FLOAT', operation=op)
        self.feed(self.sock_in(n, 0), a)
        self.feed(self.sock_in(n, 1), b)
        return self.sock_out(n)

    def bool_op(self, op, a, b=None):
        n = self.node("FunctionNodeBooleanMath", operation=op)
        self.feed(self.sock_in(n, 0), a)
        if b is not None:
            self.feed(self.sock_in(n, 1), b)
        return self.sock_out(n)

    # ---- vectors -------------------------------------------------------
    def vmath(self, op, a, b=None, scale=None):
        n = self.node("ShaderNodeVectorMath", operation=op)
        ins = self._enabled(n.inputs)
        vec_ins = [s for s in ins if s.name == "Vector"]
        self.feed(vec_ins[0], a)
        if b is not None:
            self.feed(vec_ins[1], b)
        if scale is not None:
            self.feed(self.sock_in(n, "Scale"), scale)
        out = "Value" if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else "Vector"
        return self.sock_out(n, out)

    def vadd(self, a, b): return self.vmath('ADD', a, b)
    def vscale(self, a, s): return self.vmath('SCALE', a, scale=s)
    def vnorm(self, a): return self.vmath('NORMALIZE', a)
    def vcross(self, a, b): return self.vmath('CROSS_PRODUCT', a, b)

    def xyz(self, x=0.0, y=0.0, z=0.0):
        return self.sock_out(self.node("ShaderNodeCombineXYZ", {"X": x, "Y": y, "Z": z}))

    def sep(self, v):
        n = self.node("ShaderNodeSeparateXYZ", {"Vector": v})
        return self.sock_out(n, "X"), self.sock_out(n, "Y"), self.sock_out(n, "Z")

    # ---- fields / attributes ------------------------------------------
    def rand(self, lo, hi, id_=None, seed=0):
        n = self.node("FunctionNodeRandomValue", data_type='FLOAT')
        self.feed(self.sock_in(n, "Min"), lo)
        self.feed(self.sock_in(n, "Max"), hi)
        if id_ is not None:
            self.feed(self.sock_in(n, "ID"), id_)
        self.feed(self.sock_in(n, "Seed"), seed)
        return self.sock_out(n)

    def seed(self, k):
        return self.add(self.I("Seed"), float(k))

    def named(self, name, dtype='FLOAT'):
        n = self.node("GeometryNodeInputNamedAttribute", {"Name": name}, data_type=dtype)
        return self.sock_out(n, "Attribute")

    def store(self, geo, name, value, dtype='FLOAT', domain='POINT', selection=None):
        n = self.node("GeometryNodeStoreNamedAttribute", data_type=dtype, domain=domain)
        self.feed(self.sock_in(n, "Geometry"), geo)
        self.feed(self.sock_in(n, "Name"), name)
        self.feed(self.sock_in(n, "Value"), value)
        if selection is not None:
            self.feed(self.sock_in(n, "Selection"), selection)
        return self.sock_out(n)

    def position(self):
        return self.sock_out(self.node("GeometryNodeInputPosition"))

    def index(self):
        return self.sock_out(self.node("GeometryNodeInputIndex"))

    def spline_factor(self):
        return self.sock_out(self.node("GeometryNodeSplineParameter"), "Factor")

    def switch(self, cond, a_false, b_true, kind='GEOMETRY'):
        n = self.node("GeometryNodeSwitch", input_type=kind)
        self.feed(self.sock_in(n, "Switch"), cond)
        self.feed(self.sock_in(n, "False"), a_false)
        self.feed(self.sock_in(n, "True"), b_true)
        return self.sock_out(n)

    def join(self, *geos):
        n = self.node("GeometryNodeJoinGeometry")
        s = self.sock_in(n, "Geometry")
        for g in reversed(geos):
            self.links.new(g, s)
        return self.sock_out(n)

    def line_template(self, count):
        """A straight curve from (0,0,0) to (1,0,0) with `count` points."""
        ln = self.node("GeometryNodeCurvePrimitiveLine", {"Start": (0, 0, 0), "End": (1, 0, 0)})
        rs = self.node("GeometryNodeResampleCurve")
        self._set_menu(rs, "mode", 'COUNT', "Count")
        self.feed(self.sock_in(rs, "Curve"), self.sock_out(ln))
        self.feed(self.sock_in(rs, "Count"), count)
        return self.sock_out(rs)

    def _set_menu(self, node, prop, enum_value, menu_value):
        if hasattr(node, prop):
            setattr(node, prop, enum_value)
        else:
            self.sock_in(node, prop.replace("_", " ").title()).default_value = menu_value

    def instance_realize(self, points, instance):
        inst = self.node("GeometryNodeInstanceOnPoints")
        self.feed(self.sock_in(inst, "Points"), points)
        self.feed(self.sock_in(inst, "Instance"), instance)
        real = self.node("GeometryNodeRealizeInstances")
        self.feed(self.sock_in(real, "Geometry"), self.sock_out(inst))
        return self.sock_out(real)

    def set_position(self, geo, pos=None, offset=None, selection=None):
        n = self.node("GeometryNodeSetPosition")
        self.feed(self.sock_in(n, "Geometry"), geo)
        if pos is not None:
            self.feed(self.sock_in(n, "Position"), pos)
        if offset is not None:
            self.feed(self.sock_in(n, "Offset"), offset)
        if selection is not None:
            self.feed(self.sock_in(n, "Selection"), selection)
        return self.sock_out(n)

    def set_radius(self, curve, r):
        n = self.node("GeometryNodeSetCurveRadius")
        self.feed(self.sock_in(n, "Curve"), curve)
        self.feed(self.sock_in(n, "Radius"), r)
        return self.sock_out(n)


# --------------------------------------------------------------------------
#  Interface
# --------------------------------------------------------------------------
# (name, socket type, default, min, max, subtype, description)
INTERFACE = [
    ("Shape", [
        ("Height", 'FLOAT', 12.0, 0.5, 80.0, 'DISTANCE', "Total height of the tree"),
        ("Trunk Radius", 'FLOAT', 0.2, 0.005, 3.0, 'DISTANCE', "Trunk radius at the base"),
        ("Crown Base", 'FLOAT', 0.05, 0.0, 0.9, 'FACTOR', "Bare part of the trunk below the crown, as a fraction of height"),
        ("Seed", 'INT', 0, 0, 100000, 'NONE', "Random seed"),
    ]),
    ("Whorls", [
        ("Whorl Spacing", 'FLOAT', 0.45, 0.05, 3.0, 'DISTANCE', "Distance between branch whorls (one year of growth)"),
        ("Spacing Jitter", 'FLOAT', 0.3, 0.0, 1.0, 'FACTOR', "Randomness of whorl spacing"),
        ("Branches per Whorl", 'INT', 5, 1, 12, 'NONE', "Main branches in each whorl"),
        ("Interwhorl Branches", 'INT', 2, 0, 12, 'NONE', "Short branches between whorls"),
        ("Azimuth Jitter", 'FLOAT', 0.35, 0.0, 3.1416, 'ANGLE', "Random rotation of branches around the trunk"),
    ]),
    ("Branches", [
        ("Branch Length", 'FLOAT', 0.3, 0.02, 1.5, 'FACTOR', "Longest branch as a fraction of tree height"),
        ("Crown Shape", 'FLOAT', 1.0, 0.2, 4.0, 'NONE', "Profile exponent: <1 — rounded crown, 1 — cone, >1 — narrow spire"),
        ("Skirt", 'FLOAT', 0.15, 0.0, 1.0, 'FACTOR', "Shortening of the lowest branches"),
        ("Angle Bottom", 'FLOAT', math.radians(105), 0.0, 3.1416, 'ANGLE', "Branch angle from vertical at the bottom of the crown"),
        ("Angle Top", 'FLOAT', math.radians(55), 0.0, 3.1416, 'ANGLE', "Branch angle from vertical near the top"),
        ("Droop", 'FLOAT', 0.25, -1.0, 2.0, 'NONE', "How much branches sag in the middle"),
        ("Tip Upturn", 'FLOAT', 0.2, -1.0, 2.0, 'NONE', "How much branch tips turn up"),
        ("Branch Thickness", 'FLOAT', 0.007, 0.0005, 0.1, 'NONE', "Branch base radius relative to its length"),
        ("Branch Jitter", 'FLOAT', 0.15, 0.0, 1.0, 'FACTOR', "Random variation of length and angle"),
        ("Branch Resolution", 'INT', 9, 3, 48, 'NONE', "Points per branch curve"),
    ]),
    ("Twigs", [
        ("Twig Density", 'FLOAT', 9.0, 0.0, 60.0, 'NONE', "Second-order twigs (branchlet cards) per metre of branch"),
        ("Twig Length", 'FLOAT', 0.32, 0.0, 1.5, 'FACTOR', "Twig length relative to the parent branch"),
        ("Twig Angle", 'FLOAT', math.radians(55), 0.0, 1.6, 'ANGLE', "Angle between twig and parent branch"),
        ("Twig Hang", 'FLOAT', 0.15, -1.0, 2.0, 'NONE', "0 — flat comb, >0 — twigs hang down (Norway spruce)"),
        ("Twig Wood", 'BOOLEAN', False, None, None, None, "Also build twig wood geometry (the stems are already in the card texture)"),
        ("Twig Profile", 'INT', 4, 3, 8, 'NONE', "Twig wood cross-section vertices (4 — square)"),
    ]),
    ("Needles", [
        ("Needles", 'BOOLEAN', True, None, None, None, "Generate needle cards"),
        ("Card Size", 'FLOAT', 1.0, 0.2, 3.0, 'FACTOR', "Branchlet card size relative to twig length"),
        ("Spray Size", 'FLOAT', 0.3, 0.02, 2.0, 'DISTANCE', "Size of single-polygon spray cards along the branches"),
        ("Spray Spacing", 'FLOAT', 0.16, 0.02, 2.0, 'DISTANCE', "Distance between spray cards along the branches"),
        ("Flatness", 'FLOAT', 0.0, 0.0, 1.0, 'FACTOR', "Height of the vertical board of branchlet crosses: 0 — full cross, 1 — flat card only"),
        ("Bare Inner Part", 'FLOAT', 0.3, 0.0, 1.0, 'FACTOR', "Inner part of main branches without sprays"),
        ("Dry Lower Part", 'FLOAT', 0.0, 0.0, 1.0, 'FACTOR', "Lower part of the tree without needles (dry branches)"),
        ("Needle Color", 'RGBA', (0.021, 0.060, 0.018, 1.0), None, None, None,
         "Needle colour (the baked texture colour is re-tinted towards it)"),
        ("Color Variation", 'FLOAT', 0.2, 0.0, 1.0, 'FACTOR', "Random brightness variation per card"),
        ("Visible in Viewport", 'BOOLEAN', True, None, None, None, "Show needle cards in the viewport (always rendered)"),
    ]),
    ("Cones", [
        ("Cones", 'BOOLEAN', False, None, None, None, "Hang cones on the upper branches"),
        ("Cone Count", 'INT', 40, 0, 2000, 'NONE', "Number of cones"),
        ("Cone Size", 'FLOAT', 0.12, 0.01, 0.5, 'DISTANCE', "Cone length"),
        ("Cone Zone", 'FLOAT', 0.35, 0.0, 1.0, 'FACTOR', "Upper fraction of the crown where cones grow"),
        ("Cones Hang", 'BOOLEAN', True, None, None, None, "On — hanging (spruce), off — standing up (fir)"),
    ]),
    ("Wind", [
        ("Wind", 'BOOLEAN', False, None, None, None, "Animate wind sway"),
        ("Wind Direction", 'FLOAT', 0.0, -6.2832, 6.2832, 'ANGLE', "Wind direction in the XY plane"),
        ("Wind Strength", 'FLOAT', 0.3, 0.0, 5.0, 'NONE', "Sway amplitude"),
        ("Wind Speed", 'FLOAT', 0.5, 0.0, 10.0, 'NONE', "Sway speed"),
    ]),
    ("Mesh", [
        ("Trunk Resolution", 'INT', 10, 3, 64, 'NONE', "Trunk cross-section vertices"),
        ("Branch Profile", 'INT', 5, 3, 32, 'NONE', "Branch cross-section vertices"),
        ("Bark Material", 'MATERIAL', None, None, None, None, "Material for trunk and branches"),
        ("Needle Material", 'MATERIAL', None, None, None, None, "Material for needles"),
        ("Cone Material", 'MATERIAL', None, None, None, None, "Material for cones"),
        ("Realize Instances", 'BOOLEAN', False, None, None, None, "Convert cone instances to real mesh (for export)"),
    ]),
]

_SOCKET_TYPES = {
    'FLOAT': 'NodeSocketFloat', 'INT': 'NodeSocketInt', 'BOOLEAN': 'NodeSocketBool',
    'RGBA': 'NodeSocketColor', 'MATERIAL': 'NodeSocketMaterial',
}


def _build_interface(tree, interface=None):
    tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    for panel_name, sockets in (interface or INTERFACE):
        panel = tree.interface.new_panel(panel_name, default_closed=panel_name not in ("Shape", "Branches"))
        for name, typ, default, lo, hi, subtype, desc in sockets:
            s = tree.interface.new_socket(name, in_out='INPUT', socket_type=_SOCKET_TYPES[typ], parent=panel)
            s.description = desc
            if subtype and subtype != 'NONE' and hasattr(s, "subtype"):
                try:
                    s.subtype = subtype
                except Exception:
                    pass
            if default is not None:
                s.default_value = default
            if lo is not None and hasattr(s, "min_value"):
                s.min_value = lo
                s.max_value = hi
            if typ == 'BOOLEAN' and hasattr(s, "force_non_field"):
                s.force_non_field = True


def interface_defaults(interface=None):
    """name -> default value for every non-material input."""
    return {name: default for _, socks in (interface or INTERFACE)
            for name, typ, default, *_ in socks if typ != 'MATERIAL'}


def input_identifiers(tree):
    """name -> socket identifier, used to set modifier values from presets."""
    out = {}
    for it in tree.interface.items_tree:
        if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.socket_type != 'NodeSocketGeometry':
            out[it.name] = it.identifier
    return out


def _retire(name):
    """Remove an outdated group, or rename it if objects still use it."""
    old = bpy.data.node_groups.get(name)
    if old is None:
        return
    if old.users:
        old.name = name + " (old)"
    else:
        bpy.data.node_groups.remove(old)


# --------------------------------------------------------------------------
#  Main group
# --------------------------------------------------------------------------
def build_main_group():
    _retire(CLUSTER_GROUP_NAME)  # old needle-spray group from 0.1

    _retire(GROUP_NAME)
    tree = bpy.data.node_groups.new(GROUP_NAME, 'GeometryNodeTree')
    tree.description = "Monopodial conifer (spruce / fir) generator — Easy Conifer"
    _build_interface(tree)
    tree["easy_conifer_version"] = NODES_VERSION
    try:
        tree.is_modifier = True
    except Exception:
        pass

    b = NB(tree)
    b.gi = b.node("NodeGroupInput")
    go = b.node("NodeGroupOutput")
    H = b.I("Height")
    TWO_PI = 2.0 * math.pi
    Z = (0.0, 0.0, 1.0)

    def trunk_radius(tz):
        """Trunk radius at relative height tz (0..1), with a root flare."""
        base = b.mul(b.I("Trunk Radius"), b.pow(b.clamp01(b.sub(1.0, tz)), 0.85))
        flare = b.pow(b.clamp01(b.sub(1.0, b.div(tz, 0.03))), 2.0)
        return b.mx(b.mul(base, b.add(1.0, b.mul(flare, 0.5))), 0.003)

    # ------------------------------------------------------------------ trunk
    b.section("trunk")
    trunk = b.node("GeometryNodeCurvePrimitiveLine", {"Start": (0, 0, 0), "End": b.xyz(0, 0, H)})
    rs = b.node("GeometryNodeResampleCurve")
    b._set_menu(rs, "mode", 'COUNT', "Count")
    b.feed(b.sock_in(rs, "Curve"), b.sock_out(trunk))
    b.feed(b.sock_in(rs, "Count"), b.mx(b.div(H, 0.12), 8.0))
    trunk_c = b.sock_out(rs)
    tz_tr = b.div(b.sep(b.position())[2], H)
    trunk_c = b.set_radius(trunk_c, trunk_radius(tz_tr))
    trunk_c = b.store(trunk_c, "ec_u", tz_tr)
    trunk_c = b.store(trunk_c, "ec_kind", 2.0)

    # ------------------------------------------------------- branch origins
    b.section("branch origins")
    z0 = b.mul(H, b.I("Crown Base"))
    crown = b.sub(H, z0)
    spacing = b.I("Whorl Spacing")
    n_whorls = b.mx(b.floor(b.div(b.mul(crown, 0.97), spacing)), 1.0)
    n_main = b.I("Branches per Whorl")
    slots = b.add(n_main, b.I("Interwhorl Branches"))
    pts = b.node("GeometryNodePoints", {"Count": b.mul(n_whorls, slots)})
    i = b.index()
    w = b.floor(b.div(b.add(i, 0.01), slots))           # whorl index
    k = b.sub(i, b.mul(w, slots))                         # slot in whorl
    is_iw = b.cmp('GREATER_EQUAL', k, b.sub(n_main, 0.5))  # interwhorl branch?
    is_iw_f = b.switch(is_iw, 0.0, 1.0, 'FLOAT')

    jit = b.I("Spacing Jitter")
    wz = b.add(z0, b.mul(b.add(b.add(w, 0.5), b.mul(jit, b.rand(-0.5, 0.5, w, b.seed(11)))), spacing))
    iwz = b.add(z0, b.mul(b.add(b.add(w, 0.65), b.rand(0.0, 0.7, i, b.seed(12))), spacing))
    z = b.lerp(is_iw_f, wz, iwz)
    z = b.mn(z, b.mul(H, 0.985))
    t = b.clamp01(b.div(b.sub(z, z0), crown))          # 0 bottom of crown … 1 top

    whorl_rot = b.rand(0.0, TWO_PI, w, b.seed(13))
    az_main = b.add(b.add(b.mul(b.div(k, n_main), TWO_PI), whorl_rot),
                    b.mul(b.I("Azimuth Jitter"), b.rand(-1.0, 1.0, i, b.seed(14))))
    az_iw = b.rand(0.0, TWO_PI, i, b.seed(15))
    az = b.lerp(is_iw_f, az_main, az_iw)

    bj = b.I("Branch Jitter")
    profile = b.pow(b.mx(b.sub(1.0, t), 0.0), b.I("Crown Shape"))
    skirt = b.sub(1.0, b.mul(b.I("Skirt"), b.pow(b.clamp01(b.sub(1.0, b.div(t, 0.25))), 2.0)))
    length = b.mul(b.mul(b.mul(b.I("Branch Length"), H), profile), skirt)
    length = b.mul(length, b.lerp(is_iw_f, 1.0, 0.45))
    length = b.mul(length, b.add(1.0, b.mul(bj, b.rand(-1.0, 1.0, i, b.seed(16)))))
    length = b.mx(length, b.mul(spacing, 0.25))

    theta = b.lerp(t, b.I("Angle Bottom"), b.I("Angle Top"))
    theta = b.add(theta, b.mul(b.mul(bj, 0.5), b.rand(-1.0, 1.0, i, b.seed(17))))

    pts_g = b.sock_out(pts)
    pts_g = b.store(pts_g, "ec_z", z)
    pts_g = b.store(pts_g, "ec_az", az)
    pts_g = b.store(pts_g, "ec_len", length)
    pts_g = b.store(pts_g, "ec_th", theta)

    # ------------------------------------------------------ primary branches
    b.section("primary branches")
    tpl = b.line_template(b.I("Branch Resolution"))
    br = b.instance_realize(pts_g, tpl)
    u = b.spline_factor()
    L = b.named("ec_len")
    th = b.named("ec_th")
    a = b.named("ec_az")
    bz = b.named("ec_z")
    rho = b.mul(b.mul(L, u), b.sin(th))
    u2 = b.mul(u, u)
    v = b.mul(L, b.add(b.sub(b.mul(u, b.cos(th)), b.mul(b.I("Droop"), u2)),
                       b.mul(b.I("Tip Upturn"), b.mul(u2, u2))))
    pos = b.xyz(b.mul(b.cos(a), rho), b.mul(b.sin(a), rho), b.add(bz, v))
    br = b.set_position(br, pos=pos)
    r_base = b.mn(b.mul(b.I("Branch Thickness"), L), b.mul(trunk_radius(b.div(bz, H)), 0.6))
    r_br = b.add(b.mul(r_base, b.sub(1.0, b.mul(u, 0.85))), 0.0015)
    br = b.set_radius(br, r_br)
    br = b.store(br, "ec_u", u)
    br = b.store(br, "ec_kind", 0.0)

    # ---------------------------------------------------------- twig origins
    b.section("twig origins")
    c2p = b.node("GeometryNodeCurveToPoints", mode='LENGTH')
    b.feed(b.sock_in(c2p, "Curve"), br)
    b.feed(b.sock_in(c2p, "Length"), b.div(1.0, b.mx(b.I("Twig Density"), 0.01)))
    tw_pts = b.sock_out(c2p, "Points")
    tangent = b.sock_out(c2p, "Tangent")
    pu = b.named("ec_u")
    keep = b.bool_op('AND', b.cmp('GREATER_THAN', pu, 0.06), b.cmp('LESS_THAN', pu, 0.96))
    keep = b.bool_op('AND', keep, b.cmp('GREATER_THAN', b.I("Twig Density"), 0.05))
    tw_pts = b.sock_out(b.node("GeometryNodeDeleteGeometry",
                               {"Geometry": tw_pts, "Selection": b.bool_op('NOT', keep)}))
    ti = b.index()
    side = b.sub(b.mul(b.math('FLOORED_MODULO', ti, 2.0), 2.0), 1.0)
    s_vec = b.vnorm(b.vcross(tangent, Z))
    ta = b.add(b.I("Twig Angle"), b.mul(0.15, b.rand(-1.0, 1.0, ti, b.seed(21))))
    tw_dir = b.vadd(b.vscale(tangent, b.cos(ta)), b.vscale(s_vec, b.mul(side, b.sin(ta))))
    tw_dir = b.vnorm(b.vadd(tw_dir, b.xyz(0.0, 0.0, b.mul(b.I("Twig Hang"), -0.6))))
    pL = b.named("ec_len")
    tw_len = b.mul(b.mul(b.I("Twig Length"), pL), b.pow(b.mx(b.sub(1.0, pu), 0.0), 0.6))
    tw_len = b.mul(tw_len, b.add(0.35, b.mul(0.65, b.clamp01(b.mul(pu, 4.0)))))
    tw_len = b.mul(tw_len, b.rand(0.7, 1.15, ti, b.seed(22)))
    tw_len = b.mx(tw_len, 0.03)
    tw_pts = b.store(tw_pts, "ec_o", b.position(), 'FLOAT_VECTOR')
    tw_pts = b.store(tw_pts, "ec_d", tw_dir, 'FLOAT_VECTOR')
    tw_pts = b.store(tw_pts, "ec_tl", tw_len)

    # ------------------------------------------------------------------ twigs
    b.section("twigs")
    tpl2 = b.line_template(4)
    tw = b.instance_realize(tw_pts, tpl2)
    u_t = b.spline_factor()
    tl = b.named("ec_tl")
    tw_pos = b.vadd(b.vadd(b.named("ec_o", 'FLOAT_VECTOR'),
                           b.vscale(b.named("ec_d", 'FLOAT_VECTOR'), b.mul(tl, u_t))),
                    b.xyz(0.0, 0.0, b.mul(b.mul(b.I("Twig Hang"), -0.35), b.mul(tl, b.mul(u_t, u_t)))))
    tw = b.set_position(tw, pos=tw_pos)
    tw = b.set_radius(tw, b.add(b.mul(b.mul(b.I("Branch Thickness"), b.mul(tl, 0.7)),
                                      b.sub(1.0, b.mul(u_t, 0.8))), 0.0012))
    tw = b.store(tw, "ec_u", u_t)
    tw = b.store(tw, "ec_kind", 1.0)

    skel = b.join(trunk_c, br, tw)

    # ------------------------------------------------------------------- bark
    b.section("bark mesh")
    kind = b.named("ec_kind")
    trunk_sel = b.cmp('EQUAL', kind, 2.0)

    def to_mesh(curve_geo, sel, resolution, caps=True):
        sep = b.node("GeometryNodeSeparateGeometry", {"Geometry": curve_geo, "Selection": sel}, domain='CURVE')
        circ = b.node("GeometryNodeCurvePrimitiveCircle", {"Resolution": resolution, "Radius": 1.0})
        cap_p = b.node("GeometryNodeCaptureAttribute", domain='POINT')
        cap_p.capture_items.new('FLOAT', "UV X")
        b.feed(b.sock_in(cap_p, "Geometry"), b.sock_out(circ))
        b.links.new(b.spline_factor(), b.sock_in(cap_p, "UV X"))
        cap_c = b.node("GeometryNodeCaptureAttribute", domain='POINT')
        cap_c.capture_items.new('FLOAT', "UV Y")
        b.feed(b.sock_in(cap_c, "Geometry"), b.sock_out(sep, "Selection"))
        b.links.new(b.sock_out(b.node("GeometryNodeSplineParameter"), "Length"), b.sock_in(cap_c, "UV Y"))
        radius = b.sock_out(b.node("GeometryNodeInputRadius"))
        c2m = b.node("GeometryNodeCurveToMesh", {"Curve": b.sock_out(cap_c, 0),
                                                 "Profile Curve": b.sock_out(cap_p, 0),
                                                 "Scale": radius, "Fill Caps": caps})
        uv = b.xyz(b.sock_out(cap_p, "UV X"), b.mul(b.sock_out(cap_c, "UV Y"), 0.5), 0.0)
        return b.store(b.sock_out(c2m), "UVMap", uv, 'FLOAT2', 'CORNER')

    branch_sel = b.cmp('EQUAL', kind, 0.0)
    twig_sel = b.bool_op('AND', b.cmp('EQUAL', kind, 1.0), b.I("Twig Wood"))
    bark = b.join(to_mesh(skel, trunk_sel, b.I("Trunk Resolution")),
                  to_mesh(skel, branch_sel, b.I("Branch Profile")))
    bark = b.sock_out(b.node("GeometryNodeSetShadeSmooth", {"Mesh": bark}))
    # twig wood hides inside the needle cards: two segments are enough
    twig_curves = b.node("GeometryNodeResampleCurve")
    b._set_menu(twig_curves, "mode", 'COUNT', "Count")
    b.feed(b.sock_in(twig_curves, "Curve"), skel)
    b.feed(b.sock_in(twig_curves, "Selection"), b.cmp('EQUAL', kind, 1.0))
    b.feed(b.sock_in(twig_curves, "Count"), 3)
    twig_wood = to_mesh(b.sock_out(twig_curves), twig_sel, b.I("Twig Profile"), caps=False)
    bark = b.join(bark, twig_wood)
    rm = b.node("GeometryNodeRemoveAttribute", {"Geometry": bark, "Name": "ec_*"})
    b._set_menu(rm, "pattern_mode", 'WILDCARD', "Wildcard")
    bark = b.sock_out(rm)
    bark = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": bark, "Material": b.I("Bark Material")}))

    # ------------------------------------------------------------ needle cards
    # Cards show baked twig images from a 2x2 atlas (see twig_baker.py):
    #   tiles 0,1 — branchlets: one cross-board (2 quads) per second-order twig
    #   tiles 2,3 — sprays: one single quad per spray along the main branches
    b.section("needle cards")
    dry_z = b.mul(H, b.I("Dry Lower Part"))

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

    def orient(direction, local_euler):
        r = b.node("FunctionNodeAlignRotationToVector", {"Vector": direction}, axis='Y')
        r = b.node("FunctionNodeAlignRotationToVector", {"Rotation": b.sock_out(r), "Vector": Z},
                   axis='Z', pivot_axis='Y')
        loc = b.node("FunctionNodeEulerToRotation", {"Euler": local_euler})
        r = b.node("FunctionNodeRotateRotation", {"Rotation": b.sock_out(r), "Rotate By": b.sock_out(loc)},
                   rotation_space='LOCAL')
        return b.sock_out(r)

    def flip(i, seed_k):
        return b.sub(b.mul(b.cmp('GREATER_THAN', b.rand(0.0, 1.0, i, b.seed(seed_k)), 0.5), 2.0), 1.0)

    # branchlet crosses: one per twig, from its base towards its (hanging) tip
    bl_pts = b.sock_out(b.node("GeometryNodeDeleteGeometry", {
        "Geometry": tw_pts, "Selection": b.cmp('LESS_THAN', b.sep(b.position())[2], dry_z)}))
    bi = b.index()
    btl = b.named("ec_tl")
    bdir = b.vadd(b.vscale(b.named("ec_d", 'FLOAT_VECTOR'), btl),
                  b.xyz(0.0, 0.0, b.mul(b.mul(b.I("Twig Hang"), -0.35), btl)))
    blen = b.vmath('LENGTH', bdir)
    brot = orient(bdir, b.xyz(0.0, b.rand(-0.35, 0.35, bi, b.seed(61)), 0.0))
    bsc = b.mul(b.mul(blen, b.I("Card Size")), b.rand(0.9, 1.12, bi, b.seed(62)))
    bl = b.node("GeometryNodeInstanceOnPoints", {"Points": bl_pts, "Instance": cross, "Rotation": brot,
                                                 "Scale": b.xyz(b.mul(bsc, flip(bi, 63)), bsc, bsc)})
    bl = b.store(b.sock_out(bl), "ec_tile", b.floor(b.rand(0.0, 1.999, bi, b.seed(64))), 'FLOAT', 'INSTANCE')
    bl = b.store(bl, "ec_age", b.rand(0.0, 1.0, bi, b.seed(65)), 'FLOAT', 'INSTANCE')

    # spray quads along the outer part of main branches and the leader top
    sc2p = b.node("GeometryNodeCurveToPoints", mode='LENGTH')
    b.feed(b.sock_in(sc2p, "Curve"), b.join(trunk_c, br))
    b.feed(b.sock_in(sc2p, "Length"), b.mx(b.I("Spray Spacing"), 0.01))
    sp_pts = b.sock_out(sc2p, "Points")
    s_tan = b.sock_out(sc2p, "Tangent")
    sk = b.named("ec_kind")
    su = b.named("ec_u")
    spz = b.sep(b.position())[2]
    s_branch = b.bool_op('AND', b.cmp('EQUAL', sk, 0.0), b.cmp('GREATER_EQUAL', su, b.I("Bare Inner Part")))
    s_leader = b.bool_op('AND', b.cmp('EQUAL', sk, 2.0), b.cmp('GREATER_THAN', spz, b.sub(H, b.mul(spacing, 1.5))))
    s_keep = b.bool_op('AND', b.bool_op('OR', s_branch, s_leader), b.cmp('GREATER_THAN', spz, dry_z))
    sp_pts = b.store(sp_pts, "ec_t", s_tan, 'FLOAT_VECTOR')
    sp_pts = b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": sp_pts, "Selection": b.bool_op('NOT', s_keep)}))
    si = b.index()
    sside = b.sub(b.mul(b.math('FLOORED_MODULO', si, 2.0), 2.0), 1.0)
    yaw = b.mul(sside, b.rand(0.45, 1.0, si, b.seed(71)))
    pitch = b.add(b.mul(b.I("Twig Hang"), 0.3), b.rand(-0.15, 0.2, si, b.seed(72)))
    roll = b.rand(-0.45, 0.45, si, b.seed(73))
    srot = orient(b.named("ec_t", 'FLOAT_VECTOR'), b.xyz(pitch, roll, yaw))
    tz_s = b.clamp01(b.div(spz, H))
    ssc = b.mul(b.mul(b.I("Spray Size"), b.rand(0.8, 1.15, si, b.seed(74))), b.sub(1.0, b.mul(tz_s, 0.35)))
    sprays = b.node("GeometryNodeInstanceOnPoints", {"Points": sp_pts, "Instance": single, "Rotation": srot,
                                                     "Scale": b.xyz(b.mul(ssc, flip(si, 75)), ssc, ssc)})
    sprays = b.store(b.sock_out(sprays), "ec_tile", b.add(2.0, b.floor(b.rand(0.0, 1.999, si, b.seed(76)))),
                     'FLOAT', 'INSTANCE')
    sprays = b.store(sprays, "ec_age", b.add(0.5, b.mul(0.5, b.named("ec_u"))), 'FLOAT', 'INSTANCE')

    # realise, move UVs into the atlas tile, colour per card
    cards = b.sock_out(b.node("GeometryNodeRealizeInstances", {"Geometry": b.join(bl, sprays)}))
    tile = b.named("ec_tile")
    uv0 = b.named("UVMap", 'FLOAT_VECTOR')
    u0, v0, _ = b.sep(uv0)
    uu = b.add(b.add(b.mul(u0, 0.49), 0.005), b.mul(b.math('FLOORED_MODULO', tile, 2.0), 0.5))
    vv = b.add(b.add(b.mul(v0, 0.49), 0.005), b.mul(b.floor(b.div(tile, 2.0)), 0.5))
    cards = b.store(cards, "UVMap", b.xyz(uu, vv, 0.0), 'FLOAT2', 'CORNER')
    cvar = b.add(1.0, b.mul(b.mul(b.I("Color Variation"), 2.0), b.sub(b.named("ec_age"), 0.5)))  # per card
    cards = b.store(cards, "needle_color", b.vscale(b.I("Needle Color"), cvar), 'FLOAT_COLOR')
    rm2 = b.node("GeometryNodeRemoveAttribute", {"Geometry": cards, "Name": "ec_*"})
    b._set_menu(rm2, "pattern_mode", 'WILDCARD', "Wildcard")
    cards = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": b.sock_out(rm2),
                                                           "Material": b.I("Needle Material")}))
    is_vp = b.sock_out(b.node("GeometryNodeIsViewport"))
    show_needles = b.bool_op('AND', b.I("Needles"),
                             b.bool_op('OR', b.I("Visible in Viewport"), b.bool_op('NOT', is_vp)))
    needles = b.switch(show_needles, None, cards)

    # ------------------------------------------------------------------ cones
    b.section("cones")
    cz_from = b.sub(H, b.mul(crown, b.I("Cone Zone")))
    cone_src = b.node("GeometryNodeSeparateGeometry", domain='CURVE')
    b.feed(b.sock_in(cone_src, "Geometry"), skel)
    b.feed(b.sock_in(cone_src, "Selection"), b.cmp('EQUAL', b.named("ec_kind"), 0.0))
    ends = b.node("GeometryNodeCurveToPoints", mode='EVALUATED')
    b.feed(b.sock_in(ends, "Curve"), b.sock_out(cone_src, "Selection"))
    end_pts = b.sock_out(ends, "Points")
    cu = b.named("ec_u")
    cpz = b.sep(b.position())[2]
    cone_ok = b.bool_op('AND', b.cmp('GREATER_THAN', cu, 0.55), b.cmp('GREATER_THAN', cpz, cz_from))
    end_pts = b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": end_pts,
                                                                "Selection": b.bool_op('NOT', cone_ok)}))
    # pick a random subset of candidate points
    cidx = b.index()
    cnt_node = b.node("GeometryNodeAttributeDomainSize", component='POINTCLOUD')
    b.feed(b.sock_in(cnt_node, "Geometry"), end_pts)
    n_cand = b.mx(b.sock_out(cnt_node, "Point Count"), 1.0)
    prob = b.div(b.I("Cone Count"), n_cand)
    pick = b.cmp('LESS_THAN', b.rand(0.0, 1.0, cidx, b.seed(41)), prob)
    end_pts = b.sock_out(b.node("GeometryNodeDeleteGeometry", {"Geometry": end_pts,
                                                                "Selection": b.bool_op('NOT', pick)}))
    cs = b.I("Cone Size")
    cone_mesh = b.node("GeometryNodeMeshUVSphere", {"Segments": 10, "Rings": 6, "Radius": 0.5})
    cone_shape = b.node("GeometryNodeTransform", {"Geometry": b.sock_out(cone_mesh, "Mesh"),
                                                  "Scale": b.xyz(b.mul(cs, 0.36), b.mul(cs, 0.36), cs),
                                                  "Translation": b.xyz(0.0, 0.0, b.mul(cs, 0.45))})
    taper = b.node("GeometryNodeSetPosition")
    b.feed(b.sock_in(taper, "Geometry"), b.sock_out(cone_shape))
    cp = b.position()
    cpx, cpy, cpzz = b.sep(cp)
    shrink = b.lerp(b.clamp01(b.div(cpzz, cs)), 1.0, 0.55)
    b.feed(b.sock_in(taper, "Position"), b.xyz(b.mul(cpx, shrink), b.mul(cpy, shrink), cpzz))
    cone_geo = b.sock_out(b.node("GeometryNodeSetShadeSmooth", {"Mesh": b.sock_out(taper)}))
    cone_geo = b.sock_out(b.node("GeometryNodeSetMaterial", {"Geometry": cone_geo,
                                                              "Material": b.I("Cone Material")}))
    cone_dir = b.switch(b.I("Cones Hang"), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), 'VECTOR')
    cri = b.index()
    tilt = b.xyz(b.rand(-0.25, 0.25, cri, b.seed(42)), b.rand(-0.25, 0.25, cri, b.seed(43)), 0.0)
    c_rot = b.node("FunctionNodeAlignRotationToVector", {"Vector": b.vadd(cone_dir, tilt)}, axis='Z')
    csc = b.rand(0.75, 1.2, cri, b.seed(44))
    cones = b.node("GeometryNodeInstanceOnPoints", {"Points": end_pts, "Instance": cone_geo,
                                                    "Rotation": b.sock_out(c_rot),
                                                    "Scale": b.xyz(csc, csc, csc)})
    cones = b.switch(b.I("Cones"), None, b.sock_out(cones))

    # ------------------------------------------------------------- wind + output
    b.section("output")
    result = b.join(bark, needles, cones)
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
    flutter = b.vscale(b.vadd(b.sock_out(noise, "Color"), (-0.5, -0.5, -0.5)),
                       b.mul(b.mul(b.I("Wind Strength"), radial), b.mul(H, 0.12)))
    result = b.set_position(result, offset=b.vadd(big, flutter), selection=b.I("Wind"))
    realized = b.sock_out(b.node("GeometryNodeRealizeInstances", {"Geometry": result}))
    result = b.switch(b.I("Realize Instances"), result, realized)
    b.feed(b.sock_in(go, 0), result)
    go.location = (b.col * 190 + 300, b.section_y)
    b.gi.location = (-400, 0)
    return tree


def ensure_group(force=False):
    tree = bpy.data.node_groups.get(GROUP_NAME)
    if tree and not force and tree.get("easy_conifer_version") == NODES_VERSION:
        return tree
    return build_main_group()
