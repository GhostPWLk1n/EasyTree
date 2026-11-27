# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — high-poly broadleaf twigs (poplar, willow, maple, ash, linden).
# Copyright (C) 2026 Pavel Fomin
"""Polygonal twigs with real leaves for the texture atlas (see twig_baker.py).

Tile convention: unit square, twig base at the bottom centre, shoot towards +Y.
Two leaf builders:
    grid leaf  — a grid deformed by a half-width profile along the midrib
                 (poplar, willow, ash leaflets);
    polar leaf — rings around the blade base with an outline radius R(phi)
                 (maple: palmate lobes, linden: cordate with a basal sinus).
"""

import math

import numpy as np

SPECIES = {
    'POPLAR': dict(leaf_col=(0.032, 0.085, 0.020), young_col=(0.07, 0.14, 0.03), col_var=0.14,
                   stem_col=(0.13, 0.11, 0.07), stem_r=0.0055, vein=1.25),
    'WILLOW': dict(leaf_col=(0.075, 0.125, 0.050), young_col=(0.11, 0.17, 0.05), col_var=0.15,
                   stem_col=(0.32, 0.20, 0.045), stem_r=0.0035, vein=1.18),
    'MAPLE': dict(leaf_col=(0.045, 0.125, 0.020), young_col=(0.09, 0.19, 0.03), col_var=0.14,
                  stem_col=(0.10, 0.08, 0.045), stem_r=0.006, vein=1.25),
    'ASH': dict(leaf_col=(0.040, 0.110, 0.025), young_col=(0.08, 0.16, 0.03), col_var=0.12,
                stem_col=(0.12, 0.12, 0.09), stem_r=0.008, vein=1.2),
    'LINDEN': dict(leaf_col=(0.050, 0.130, 0.024), young_col=(0.10, 0.18, 0.03), col_var=0.14,
                   stem_col=(0.16, 0.045, 0.030), stem_r=0.005, vein=1.22),
    # shrubs
    'COTONEASTER': dict(leaf_col=(0.025, 0.070, 0.016), young_col=(0.07, 0.13, 0.03), col_var=0.2,
                        stem_col=(0.08, 0.05, 0.04), stem_r=0.004, vein=1.12),
    'PHYSOCARPUS': dict(leaf_col=(0.050, 0.120, 0.025), young_col=(0.09, 0.17, 0.03), col_var=0.2,
                        stem_col=(0.14, 0.08, 0.05), stem_r=0.0045, vein=1.2),
    'HAZEL': dict(leaf_col=(0.055, 0.130, 0.030), young_col=(0.10, 0.18, 0.04), col_var=0.13,
                  stem_col=(0.15, 0.10, 0.07), stem_r=0.005, vein=1.28),
    'BOXELDER': dict(leaf_col=(0.070, 0.160, 0.040), young_col=(0.11, 0.21, 0.05), col_var=0.13,
                     stem_col=(0.12, 0.16, 0.09), stem_r=0.006, vein=1.2),
}


def _norm(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-9)


def _saw(x):
    return x - np.floor(x)


def _frame(direction, up):
    d = _norm(np.asarray(direction, float))
    side = _norm(np.cross(d, up))
    return d, side, np.cross(side, d)


def _colour(sp, rng, young=0.0):
    c = np.asarray(sp['leaf_col']) * (1 - young) + np.asarray(sp['young_col']) * young
    return c * (1.0 + rng.uniform(-sp['col_var'], sp['col_var']))


# ----------------------------------------------------------------- outlines
def hw_poplar(u, rng):            # deltoid: broad truncate base, long acuminate tip, crenate
    base = 0.75 + 0.25 * np.clip(u / 0.12, 0, 1) ** 0.5
    s = np.where(u < 0.2, base, base * ((1 - u) / 0.8) ** 1.25)
    s = np.where(u < 0.015, 0.25, s)
    return s * (1 + 0.04 * _saw(u * 16 + rng.uniform()))


def hw_willow(u, rng):            # narrow lanceolate, finely serrate
    s = np.sin(math.pi * np.clip(u, 0, 1) ** 0.85) ** 0.8 * (1 - u) ** 0.15
    return s * (1 + 0.025 * _saw(u * 40))


def hw_leaflet(u, rng):           # ash leaflet: lanceolate, serrate, acuminate
    s = np.sin(math.pi * np.clip(u, 0, 1) ** 0.9) ** 0.9 * (1 - u) ** 0.25
    teeth = np.where((u > 0.15) & (u < 0.92), 1 + 0.06 * _saw(u * 14 + rng.uniform()), 1.0)
    return s * teeth


def r_maple(phi, rng):            # 5 acuminate lobes, open basal sinus
    lobes = ((0.0, 1.0), (0.95, 0.92), (-0.95, 0.92), (1.85, 0.6), (-1.85, 0.6))
    r = np.full_like(phi, 0.52)
    for c, a in lobes:
        c = c + rng.uniform(-0.06, 0.06)
        r = np.maximum(r, 0.52 + (a - 0.52) * np.exp(-((phi - c) / 0.3) ** 2))
    # a few big teeth on the lobes
    r *= 1 + 0.08 * np.exp(-((_saw(phi * 4.5) - 0.5) / 0.12) ** 2) * (r > 0.62)
    r = np.where(np.abs(phi) > 2.55, 0.12 + (r - 0.12) * np.clip((math.pi - np.abs(phi)) / 0.59, 0, 1), r)
    return r


def r_linden(phi, rng):           # cordate, acuminate, slightly oblique base
    r = 0.5 * (1 + np.cos(phi))                                  # cardioid
    r = r * (1 + 0.22 * np.exp(-(phi / 0.13) ** 2))              # drawn-out tip
    r = r * (1 + 0.1 * np.sign(phi) * np.clip((np.abs(phi) - 1.6) / 1.4, 0, 1))  # oblique base
    r = r * (1 + 0.035 * _saw(phi * 26 / math.pi))               # serration
    return np.maximum(r, 0.03)


def hw_cotoneaster(u, rng):       # elliptic, acute, entire margin
    return np.sin(math.pi * np.clip(u, 0, 1) ** 0.95) ** 0.75 * (1 - u) ** 0.08


def hw_negundo(u, rng):           # box-elder leaflet: ovate, a few coarse teeth
    s = np.sin(math.pi * np.clip(u, 0, 1) ** 0.8) ** 0.85 * (1 - u) ** 0.2
    return s * np.where((u > 0.3) & (u < 0.85), 1 + 0.13 * np.exp(-((_saw(u * 4.5 + rng.uniform()) - 0.5) / 0.15) ** 2), 1.0)


def r_physocarpus(phi, rng):      # 3 (-5) lobes, crenate
    lobes = ((0.0, 1.0), (0.85, 0.78), (-0.85, 0.78), (1.75, 0.45), (-1.75, 0.45))
    r = np.full_like(phi, 0.5)
    for c, a in lobes:
        r = np.maximum(r, 0.5 + (a - 0.5) * np.exp(-((phi - c - rng.uniform(-0.05, 0.05)) / 0.34) ** 2))
    r *= 1 + 0.05 * np.abs(np.sin(phi * 9))
    return np.where(np.abs(phi) > 2.5, 0.15 + (r - 0.15) * np.clip((math.pi - np.abs(phi)) / 0.64, 0, 1), r)


def r_hazel(phi, rng):            # broad obovate-round, cordate, cuspidate, double serrate
    r = 0.5 * (1 + np.cos(phi)) ** 0.75 * 0.62 + 0.18 * np.cos(phi / 2) ** 2
    r = r * (1 + 0.28 * np.exp(-(phi / 0.1) ** 2))
    r = r * (1 + 0.04 * _saw(phi * 13 / math.pi) + 0.02 * _saw(phi * 26 / math.pi))
    return np.maximum(r, 0.04)


# ----------------------------------------------------------------- builders
def grid_leaf(mb, sp, origin, direction, up, length, width, col, rng, hw_fn, rows=26, cols=9,
              fold=0.2, curl=0.0, laterals=8.0):
    d, side, nrm = _frame(direction, up)
    u = np.linspace(0.0, 1.0, rows)
    v = np.linspace(-1.0, 1.0, cols)
    U, V = np.meshgrid(u, v, indexing='ij')
    hw = hw_fn(u, rng)[:, None] * width * 0.5
    x, y = V * hw, U * length
    z = fold * np.abs(x) + (curl + rng.uniform(-0.08, 0.08)) * length * (U - 0.4) ** 2 \
        + rng.uniform(-0.2, 0.2) * x * U
    pts = (np.asarray(origin)[None, None, :] + x[..., None] * side + y[..., None] * d + z[..., None] * nrm).reshape(-1, 3)
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a = i * cols + j
            faces += [(a, a + cols, a + 1), (a + 1, a + cols, a + cols + 1)]
    av = np.abs(V)
    phase = (y - np.abs(x) * 0.9) / length * laterals
    lateral = np.clip(1 - np.abs(_saw(phase) - 0.5) * 2 / 0.16, 0, 1) * (U > 0.08) * (U < 0.88)
    vein = np.maximum(np.clip(1 - av / 0.14, 0, 1), 0.7 * lateral).reshape(-1)
    shade = (1 + (sp['vein'] - 1) * vein) * (1 - 0.1 * np.clip((av.reshape(-1) - 0.75) / 0.25, 0, 1))
    mb.add(pts, faces, np.asarray(col)[None, :] * shade[:, None], 1.0, 1.0)


def polar_leaf(mb, sp, origin, direction, up, size, col, rng, r_fn, vein_angles, rings=12, segs=72,
               fold=0.12, cup=0.1, lateral_scale=1.0):
    d, side, nrm = _frame(direction, up)
    phi = np.linspace(-math.pi, math.pi, segs, endpoint=False)
    R = r_fn(phi, rng) * size
    f = np.linspace(1.0 / rings, 1.0, rings)
    F, P = np.meshgrid(f, phi, indexing='ij')
    RR = F * R[None, :]
    x = RR * np.sin(P) * lateral_scale
    y = RR * np.cos(P)
    z = fold * np.abs(x) + cup * size * F ** 2 + rng.uniform(-0.05, 0.05) * x
    ring_pts = (np.asarray(origin)[None, None, :] + x[..., None] * side + y[..., None] * d + z[..., None] * nrm).reshape(-1, 3)
    pts = np.concatenate([np.asarray(origin)[None, :], ring_pts])
    faces = []
    for j in range(segs):
        faces.append((0, 1 + j, 1 + (j + 1) % segs))
    for i in range(rings - 1):
        for j in range(segs):
            a = 1 + i * segs + j
            b = 1 + i * segs + (j + 1) % segs
            faces += [(a, a + segs, b), (b, a + segs, b + segs)]
    arc = np.full(P.shape, 1e3)
    for c in vein_angles:
        arc = np.minimum(arc, np.abs(P - c) * RR)
    vein = np.clip(1 - arc / (0.012 * size), 0, 1) * (F < 0.9)
    vein = np.concatenate([[1.0], vein.reshape(-1)])
    edge = np.concatenate([[0.0], np.clip((F.reshape(-1) - 0.85) / 0.15, 0, 1)])
    shade = (1 + (sp['vein'] - 1) * vein) * (1 - 0.1 * edge)
    mb.add(pts, faces, np.asarray(col)[None, :] * shade[:, None], 1.0, 1.0)


def _petiole(mb, add_tube, sp, p, d, length, r=0.0012):
    pts = np.stack([p, p + d * length * 0.5 + np.array([0, 0, 0.004]), p + d * length])
    add_tube(mb, pts, r, r * 0.8, np.asarray(sp['stem_col']) * 1.2, sides=4)
    return pts[-1]


def _leaf_dir(stem_dir, side_sign, rng, lo=0.35, hi=0.95):
    sd = _norm(np.asarray(stem_dir, float))
    perp = np.array([-sd[1], sd[0], 0.0]) * side_sign
    a = rng.uniform(lo, hi)
    return _norm(sd * math.cos(a) + perp * math.sin(a) + np.array([0, 0, rng.uniform(-0.1, 0.2)]))


def _up(rng, tilt=0.3):
    return _norm(np.array([0.0, 0.0, 1.0]) + rng.normal(0, tilt, 3))


def _main(polyline, add_tube, mb, sp, rng, length=0.9, bend=0.06, n=22, r0=1.2, r1=0.45, x0=0.0):
    main = polyline((x0, 0.02, 0.0), (rng.uniform(-0.1, 0.1), 1.0), length, rng.uniform(-bend, bend),
                    rng, n=n, lift=0.05)
    add_tube(mb, main, sp['stem_r'] * r0, sp['stem_r'] * r1, np.asarray(sp['stem_col']), sides=5)
    return main


def _at(main, t):
    i = min(int(t * (len(main) - 1)), len(main) - 2)
    return main[i], main[i + 1] - main[i]


# ------------------------------------------------------------------ species
def poplar(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['POPLAR']

    def leaf(p, sd, side, scale=1.0, young=0.0):
        d = _leaf_dir(sd, side, rng)
        tip = _petiole(mb, add_tube, sp, p, d, 0.07 * scale * rng.uniform(0.8, 1.2))   # long petiole
        L = 0.19 * scale * rng.uniform(0.85, 1.1)
        grid_leaf(mb, sp, tip, _leaf_dir(d, side, rng, -0.3, 0.3), _up(rng, 0.3), L, L * 1.0,
                  _colour(sp, rng, young), rng, hw_poplar, fold=0.1, laterals=6)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng)
        for i, t in enumerate(np.linspace(0.06, 0.92, int(rng.integers(9, 12)))):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.0 - 0.3 * max(0, t - 0.7) / 0.3, max(0, t - 0.65) / 0.35)
    else:
        main = _main(polyline, add_tube, mb, sp, rng, 0.16, 0.0, 5, 1.6, 1.0)
        for k in range(int(rng.integers(4, 6))):
            a = -1.3 + 2.6 * (k + rng.uniform(0.2, 0.8)) / 5
            leaf(main[-1], (math.sin(a), math.cos(a), 0), 1 if a > 0 else -1, 1.7)


def willow(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['WILLOW']

    def leaf(p, sd, side, scale=1.0, young=0.0):
        d = _leaf_dir(sd, side, rng, 0.25, 0.6)          # leaves point along the shoot
        tip = _petiole(mb, add_tube, sp, p, d, 0.012 * scale)
        L = 0.17 * scale * rng.uniform(0.85, 1.1)
        grid_leaf(mb, sp, tip, d, _up(rng, 0.5), L, L * 0.17, _colour(sp, rng, young), rng, hw_willow,
                  rows=22, cols=5, fold=0.25, curl=rng.uniform(-0.15, 0.1), laterals=12)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.95, 0.1, 26, 1.0, 0.5)
        for i, t in enumerate(np.linspace(0.04, 0.95, int(rng.integers(22, 28)))):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.0 - 0.4 * max(0, t - 0.75) / 0.25, max(0, t - 0.7) / 0.3)
    else:
        main = _main(polyline, add_tube, mb, sp, rng, 0.6, 0.12, 14, 1.0, 0.5)
        for i, t in enumerate(np.linspace(0.05, 0.95, int(rng.integers(12, 16)))):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.6 * (1.0 - 0.4 * max(0, t - 0.75) / 0.25))


def maple(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['MAPLE']
    veins = (0.0, 0.95, -0.95, 1.85, -1.85)

    def leaf(p, d, scale=1.0, young=0.0):
        tip = _petiole(mb, add_tube, sp, p, d, 0.12 * scale * rng.uniform(0.85, 1.15), 0.0016)
        polar_leaf(mb, sp, tip, d, _up(rng, 0.3), 0.15 * scale * rng.uniform(0.9, 1.1),
                   _colour(sp, rng, young), rng, r_maple, veins, fold=0.08, cup=0.08)

    def pair(p, sd, scale, young=0.0):
        for side in (-1, 1):  # opposite leaves
            leaf(p, _leaf_dir(sd, side, rng, 0.7, 1.2), scale, young)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.62, 0.04, 10, 1.3, 0.8)
        for k, t in enumerate((0.15, 0.48, 0.8)):
            p, sd = _at(main, t)
            pair(p, sd, 1.05 - 0.2 * k, 0.25 * k)
        leaf(main[-1], _norm(main[-1] - main[-2]), 0.75, 0.6)
    else:
        main = _main(polyline, add_tube, mb, sp, rng, 0.12, 0.0, 4, 1.4, 1.1)
        pair(main[-1], main[-1] - main[-2], 1.45)
        leaf(main[-1], _norm(main[-1] - main[-2]), 1.05, 0.3)


def ash(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['ASH']

    def compound(p, d, scale=1.0, young=0.0):
        """Pinnate leaf: rachis with 4-6 opposite leaflet pairs and a terminal one."""
        d = _norm(np.asarray(d, float))
        L = 0.55 * scale * rng.uniform(0.9, 1.05)
        rach = polyline(p, d[:2], L, rng.uniform(-0.05, 0.05), rng, n=12, lift=0.05)
        add_tube(mb, rach, 0.0022, 0.0012, np.asarray(sp['stem_col']) * 1.1, sides=4)
        n = int(rng.integers(4, 7))
        col = _colour(sp, rng, young)
        for k, t in enumerate(np.linspace(0.2, 0.86, n)):
            q, rd = _at(rach, t)
            for side in (-1, 1):
                ld = _leaf_dir(rd, side, rng, 0.85, 1.15)
                Ll = 0.13 * scale * (0.8 + 0.25 * t) * rng.uniform(0.9, 1.08)
                grid_leaf(mb, sp, q + ld * 0.006, ld, _up(rng, 0.35), Ll, Ll * 0.32, col * rng.uniform(0.93, 1.07),
                          rng, hw_leaflet, rows=18, cols=7, fold=0.18, laterals=9)
        Ll = 0.14 * scale
        grid_leaf(mb, sp, rach[-1], _norm(rach[-1] - rach[-2]), _up(rng, 0.3), Ll, Ll * 0.32, col, rng, hw_leaflet,
                  rows=18, cols=7, fold=0.18, laterals=9)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.3, 0.02, 6, 1.4, 1.0)
        p, sd = _at(main, 0.35)
        for side in (-1, 1):
            compound(p, _leaf_dir(sd, side, rng, 0.6, 0.85), 0.95)
        compound(main[-1], (rng.uniform(-0.1, 0.1), 1.0, 0.0), 1.05, 0.3)
    else:
        compound(np.array([0.0, 0.03, 0.0]), (rng.uniform(-0.08, 0.08), 1.0, 0.0), 1.65)


def linden(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['LINDEN']
    veins = (0.0, 0.7, -0.7, 1.5, -1.5)

    def leaf(p, sd, side, scale=1.0, young=0.0):
        d = _leaf_dir(sd, side, rng, 0.9, 1.4)           # distichous, spread to the sides
        tip = _petiole(mb, add_tube, sp, p, d, 0.05 * scale * rng.uniform(0.85, 1.15))
        polar_leaf(mb, sp, tip, _leaf_dir(d, side, rng, -0.2, 0.3), _up(rng, 0.35), 0.18 * scale * rng.uniform(0.9, 1.1),
                   _colour(sp, rng, young), rng, r_linden, veins, fold=0.06, cup=0.06, lateral_scale=0.82)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.85, 0.05, 20)
        for i, t in enumerate(np.linspace(0.08, 0.9, int(rng.integers(7, 9)))):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.15 - 0.35 * t, max(0, t - 0.6) / 0.4)
    else:
        main = _main(polyline, add_tube, mb, sp, rng, 0.45, 0.04, 10)
        for i, t in enumerate(np.linspace(0.15, 0.85, 3)):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.3 - 0.3 * t)


# ------------------------------------------------------------------- shrubs
def cotoneaster(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['COTONEASTER']

    def leaf(p, sd, side, scale=1.0, young=0.0):
        d = _leaf_dir(sd, side, rng, 0.7, 1.2)
        tip = _petiole(mb, add_tube, sp, p, d, 0.012 * scale, 0.001)
        L = 0.085 * scale * rng.uniform(0.85, 1.12)
        grid_leaf(mb, sp, tip, d, _up(rng, 0.3), L, L * 0.6, _colour(sp, rng, young), rng, hw_cotoneaster,
                  rows=16, cols=7, fold=0.22, laterals=5)

    def shoot(p0, d, length, n, scale=1.0, young_from=0.65):
        sh = polyline(p0, d[:2], length, rng.uniform(-0.08, 0.08), rng, n=10, lift=0.1)
        add_tube(mb, sh, sp['stem_r'] * 0.8, sp['stem_r'] * 0.4, np.asarray(sp['stem_col']), sides=4)
        for i, t in enumerate(np.linspace(0.08, 0.95, n)):
            q, sd = _at(sh, t)
            leaf(q, sd, 1 if i % 2 else -1, scale * (1 - 0.3 * max(0, t - 0.8) / 0.2), max(0, t - young_from) / (1 - young_from))
        return sh

    if kind == 'BRANCHLET':   # arching shoot with distichous leaves and short side shoots
        main = _main(polyline, add_tube, mb, sp, rng, 0.92, 0.12, 20)
        for i, t in enumerate(np.linspace(0.05, 0.94, 16)):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.0, max(0, t - 0.7) / 0.3)
        for i, t in enumerate((0.25, 0.45, 0.65)):
            p, sd = _at(main, t)
            side = 1 if i % 2 else -1
            shoot(p, np.array([-sd[1] * side, sd[0] * side, 0]) * 0.8 + _norm(sd) * 0.6, 0.22 - 0.05 * i, 6, 0.9)
    else:
        shoot(np.array([0.0, 0.03, 0.0]), np.array([rng.uniform(-0.1, 0.1), 1.0, 0.0]), 0.85, 11, 1.7)


def physocarpus(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['PHYSOCARPUS']
    veins = (0.0, 0.85, -0.85)

    def leaf(p, sd, side, scale=1.0, young=0.0):
        d = _leaf_dir(sd, side, rng, 0.5, 1.0)
        tip = _petiole(mb, add_tube, sp, p, d, 0.035 * scale, 0.0013)
        polar_leaf(mb, sp, tip, d, _up(rng, 0.3), 0.12 * scale * rng.uniform(0.88, 1.1), _colour(sp, rng, young),
                   rng, r_physocarpus, veins, fold=0.1, cup=0.08)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.9, 0.1, 20)
        for i, t in enumerate(np.linspace(0.06, 0.92, 9)):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.15 - 0.4 * t, max(0, t - 0.65) / 0.35)
    else:
        main = _main(polyline, add_tube, mb, sp, rng, 0.35, 0.05, 8, 1.2, 0.8)
        for i, t in enumerate(np.linspace(0.15, 0.95, 4)):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.8 - 0.4 * t, 0.3 * t)


def hazel(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['HAZEL']
    veins = (0.0, 0.55, -0.55, 1.1, -1.1)

    def leaf(p, sd, side, scale=1.0, young=0.0):
        d = _leaf_dir(sd, side, rng, 0.9, 1.35)        # distichous
        tip = _petiole(mb, add_tube, sp, p, d, 0.025 * scale, 0.0014)
        polar_leaf(mb, sp, tip, _leaf_dir(d, side, rng, -0.2, 0.3), _up(rng, 0.3), 0.2 * scale * rng.uniform(0.88, 1.1),
                   _colour(sp, rng, young), rng, r_hazel, veins, fold=0.07, cup=0.05, lateral_scale=0.92)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.88, 0.06, 18)
        for i, t in enumerate(np.linspace(0.1, 0.9, 6)):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.05 - 0.35 * t, max(0, t - 0.6) / 0.4)
    else:
        main = _main(polyline, add_tube, mb, sp, rng, 0.4, 0.05, 8)
        for i, t in enumerate(np.linspace(0.2, 0.9, 3)):
            p, sd = _at(main, t)
            leaf(p, sd, 1 if i % 2 else -1, 1.25 - 0.3 * t)


def boxelder(kind, rng, mb, add_tube, polyline):
    sp = SPECIES['BOXELDER']

    def compound(p, d, scale=1.0, young=0.0):
        d = _norm(np.asarray(d, float))
        n_pairs = int(rng.integers(1, 3))                # 3 or 5 leaflets
        L = (0.22 + 0.1 * n_pairs) * scale
        rach = polyline(p, d[:2], L, rng.uniform(-0.04, 0.04), rng, n=10, lift=0.04)
        add_tube(mb, rach, 0.0024, 0.0016, np.asarray(sp['stem_col']), sides=4)
        col = _colour(sp, rng, young)
        for t in np.linspace(0.5, 0.82, n_pairs):
            q, rd = _at(rach, t)
            for side in (-1, 1):
                ld = _leaf_dir(rd, side, rng, 0.8, 1.15)
                Ll = 0.17 * scale * rng.uniform(0.9, 1.08)
                grid_leaf(mb, sp, q + ld * 0.01, ld, _up(rng, 0.3), Ll, Ll * 0.55, col * rng.uniform(0.94, 1.06),
                          rng, hw_negundo, rows=18, cols=7, fold=0.15, laterals=6)
        Ll = 0.2 * scale
        grid_leaf(mb, sp, rach[-1], _norm(rach[-1] - rach[-2]), _up(rng, 0.3), Ll, Ll * 0.6, col, rng, hw_negundo,
                  rows=18, cols=7, fold=0.15, laterals=6)

    if kind == 'BRANCHLET':
        main = _main(polyline, add_tube, mb, sp, rng, 0.35, 0.03, 6, 1.3, 1.0)
        p, sd = _at(main, 0.4)
        for side in (-1, 1):                            # opposite compound leaves
            compound(p, _leaf_dir(sd, side, rng, 0.55, 0.85), 1.0)
        compound(main[-1], (rng.uniform(-0.1, 0.1), 1.0, 0.0), 1.05, 0.3)
    else:
        compound(np.array([0.0, 0.03, 0.0]), (rng.uniform(-0.08, 0.08), 1.0, 0.0), 1.55)


BUILDERS = {'POPLAR': poplar, 'WILLOW': willow, 'MAPLE': maple, 'ASH': ash, 'LINDEN': linden,
            'COTONEASTER': cotoneaster, 'PHYSOCARPUS': physocarpus, 'HAZEL': hazel, 'BOXELDER': boxelder}


def build_broadleaf_twig(species, kind, seed, mb, add_tube, polyline):
    BUILDERS[species](kind, np.random.default_rng(seed), mb, add_tube, polyline)


# --------------------------------------------------------- clipped shrubs
# Hedge atlas (species "<NAME>_HEDGE"):
#   tile 0 SHOOT   — a leafy shoot (base at the bottom) for the "fuzz" sticking out of the clipped surface
#   tile 1 BARE    — bare forked branches (V-forks of a pruned shrub) for the inside, a few leaves at the tips
#   tile 2, 3 CLUSTER — a dense mat of leaves centred in the tile, laid on the clipped surface
HEDGE_KINDS = ('SHOOT', 'BARE', 'CLUSTER', 'CLUSTER')


def _hedge_leaf(species, rng, mb, add_tube):
    sp = SPECIES[species]
    if species == 'COTONEASTER':
        def leaf(p, sd, side, scale=1.0, young=0.0):
            d = _leaf_dir(sd, side, rng, 0.6, 1.3)
            tip = _petiole(mb, add_tube, sp, p, d, 0.01 * scale, 0.001)
            L = 0.075 * scale * rng.uniform(0.85, 1.12)
            # strongly varied leaf planes: every leaf catches light and reflections differently
            grid_leaf(mb, sp, tip, d, _up(rng, 0.75), L, L * 0.6, _colour(sp, rng, young), rng, hw_cotoneaster,
                      rows=12, cols=7, fold=0.3, curl=rng.uniform(-0.2, 0.15), laterals=5)
    else:  # PHYSOCARPUS
        def leaf(p, sd, side, scale=1.0, young=0.0):
            d = _leaf_dir(sd, side, rng, 0.5, 1.1)
            tip = _petiole(mb, add_tube, sp, p, d, 0.025 * scale, 0.0012)
            polar_leaf(mb, sp, tip, d, _up(rng, 0.75), 0.055 * scale * rng.uniform(0.88, 1.1), _colour(sp, rng, young),
                       rng, r_physocarpus, (0.0, 0.85, -0.85), rings=8, segs=48, fold=0.1, cup=0.08)
    return sp, leaf


def build_hedge_tile(species, kind, seed, mb, add_tube, polyline):
    rng = np.random.default_rng(seed)
    sp, leaf = _hedge_leaf(species, rng, mb, add_tube)
    stem = np.asarray(sp['stem_col'])

    def shoot(p0, d, length, n_leaves, scale, r=1.0, young_from=0.6):
        sh = polyline(np.asarray(p0, float), d, length, rng.uniform(-0.1, 0.1), rng, n=8, lift=0.1)
        add_tube(mb, sh, sp['stem_r'] * 0.7 * r, sp['stem_r'] * 0.35 * r, stem, sides=4)
        for i, t in enumerate(np.linspace(0.1, 0.97, n_leaves)):
            q, sd = _at(sh, t)
            leaf(q, sd, 1 if i % 2 else -1, scale * (1 - 0.3 * max(0, t - 0.8) / 0.2),
                 max(0, t - young_from) / (1 - young_from))
        return sh

    if kind == 'SHOOT':
        main = shoot((0.0, 0.02, 0.0), (rng.uniform(-0.1, 0.1), 1.0), 0.9, 12, 1.9)
        for t, side in ((0.35, 1), (0.55, -1), (0.72, 1)):
            q, sd = _at(main, t)
            perp = np.array([-sd[1], sd[0]]) * side
            shoot(q, _norm(np.asarray(sd[:2]) * 0.6 + perp * 0.8), 0.25, 5, 1.6, 0.7)
    elif kind == 'BARE':
        def fork(p, d, length, depth, r):
            d = _norm(np.asarray(d, float))
            for _ in range(4):                      # keep the whole fork inside the tile
                end2 = p[:2] + d * length
                if abs(end2[0]) < 0.4 and end2[1] < 0.9:
                    break
                length *= 0.7
            br = polyline(p, d, length, rng.uniform(-0.04, 0.04), rng, n=5, lift=0.0)
            add_tube(mb, br, r, r * 0.75, stem * rng.uniform(0.85, 1.1), sides=5)
            if depth >= 3:
                if rng.random() < 0.35:   # a few leaves left at the tips inside the shrub
                    leaf(br[-1], br[-1] - br[-2], 1 if rng.random() < 0.5 else -1, 1.4 if species == 'COTONEASTER' else 0.8)
                return
            for s in (-1, 1):            # V-fork after each pruning cut
                a = s * rng.uniform(0.25, 0.45)
                ca, sa = math.cos(a), math.sin(a)
                fork(br[-1], (d[0] * ca - d[1] * sa, d[0] * sa + d[1] * ca), length * rng.uniform(0.62, 0.78),
                     depth + 1, r * 0.66)
        for x0, a in ((-0.06, -0.25), (0.0, 0.05), (0.07, 0.3)):
            fork(np.array([x0, 0.02, 0.0]), (math.sin(a), math.cos(a)), 0.3, 0, 0.012)
    else:  # CLUSTER — an open mat of leaves facing outwards, with gaps between them
        n = int(rng.integers(9, 12))
        for k in range(n):
            a = (k + rng.uniform(0, 1)) / n * 2 * math.pi
            r0 = rng.uniform(0.0, 0.1)
            p0 = (math.cos(a) * r0, 0.5 + math.sin(a) * r0, rng.uniform(-0.02, 0.02))
            shoot(p0, (math.cos(a), math.sin(a)), rng.uniform(0.28, 0.38), int(rng.integers(4, 6)), 2.0,
                  0.75, young_from=0.7)
        for k in range(5):               # a few leaves on top in the middle
            a = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0.0, 0.1)
            leaf(np.array([math.cos(a) * rr, 0.5 + math.sin(a) * rr, 0.04]), (math.cos(a), math.sin(a), 0),
                 1, 2.0)
