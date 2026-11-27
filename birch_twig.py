# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — high-poly birch twigs (Betula pendula) for the texture atlas.
# Copyright (C) 2026 Pavel Fomin
"""Polygonal birch twigs with real leaves, built for twig_baker.bake_atlas.

Tile convention (same as conifers): unit square, twig base at the bottom
centre, the shoot runs towards +Y. On the tree the card's +Y is pointed along
the hanging direction, so "up" in the tile is "down" on a weeping birch.

    BRANCHLET — long pendulous shoot with alternate leaves and short shoots
                (brachyblasts) carrying 2–3 leaves each
    SPRAY     — a short-shoot rosette: a stub of twig with 3–5 leaves
"""

import math

import numpy as np

BIRCH = dict(
    leaf_len=0.15, leaf_w=0.105,
    leaf_col=(0.062, 0.150, 0.024), young_col=(0.110, 0.200, 0.030), col_var=0.16,
    vein_light=1.22,
    stem_col=(0.075, 0.034, 0.020), stem_r=0.0045,
    petiole=0.04,
)


def _norm(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-9)


def _leaf_outline(u, rng):
    """Half-width (0..1) of a deltoid-ovate, acuminate, double-serrate birch leaf."""
    s = np.sin(math.pi * np.clip(u, 0, 1) ** 0.72) ** 0.9        # widest at ~38 % of length
    s *= (1.0 - u) ** 0.18                                        # acuminate tip
    s *= np.clip(u / 0.06, 0.0, 1.0) ** 0.5 * 0.85 + 0.15         # broad-cuneate base
    big = (u * 11.0 + rng.uniform(0, 1)) % 1.0                    # primary teeth
    small = (u * 22.0) % 1.0                                      # secondary teeth
    teeth = 1.0 + 0.075 * big + 0.03 * small
    teeth = np.where((u > 0.12) & (u < 0.93), teeth, 1.0)
    return s * teeth


def _add_leaf(mb, origin, direction, up, length, width, col, rng, rows=30, cols=11):
    """A leaf blade as a deformed grid: folded along the midrib, slightly curled."""
    d = _norm(np.asarray(direction, float))
    side = _norm(np.cross(d, up))
    nrm = np.cross(side, d)
    u = np.linspace(0.0, 1.0, rows)
    v = np.linspace(-1.0, 1.0, cols)
    U, V = np.meshgrid(u, v, indexing='ij')
    hw = _leaf_outline(u, rng)[:, None] * width * 0.5
    x = V * hw                                   # across
    y = U * length                               # along
    fold = rng.uniform(0.12, 0.3)
    curl = rng.uniform(-0.12, 0.08)
    twist = rng.uniform(-0.25, 0.25)
    z = fold * np.abs(x) + curl * length * (U - 0.4) ** 2 + twist * x * U
    pts = (origin[None, None, :] + x[..., None] * side + y[..., None] * d + z[..., None] * nrm).reshape(-1, 3)
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a = i * cols + j
            faces.append((a, a + cols, a + 1))
            faces.append((a + 1, a + cols, a + cols + 1))
    # colour: per-leaf tone, lighter midrib and pinnate lateral veins
    av = np.abs(V)
    midrib = np.clip(1.0 - av / 0.12, 0, 1)
    phase = (y - np.abs(x) * 0.9) / length * 7.0
    lateral = np.clip(1.0 - np.abs((phase % 1.0) - 0.5) * 2.0 / 0.16, 0, 1) * (U > 0.08) * (U < 0.85)
    vein = np.maximum(midrib, lateral * 0.7).reshape(-1)
    edge = np.clip((av.reshape(-1) - 0.75) / 0.25, 0, 1)
    shade = (1.0 + (BIRCH['vein_light'] - 1.0) * vein) * (1.0 - 0.12 * edge)
    c = np.asarray(col)[None, :] * shade[:, None]
    mb.add(pts, faces, c, 1.0, 1.0)


def _stem(mb, add_tube, pts, r0, r1):
    add_tube(mb, pts, r0, r1, np.asarray(BIRCH['stem_col']), sides=5)


def _leaf_colour(rng, young=0.0):
    c = np.asarray(BIRCH['leaf_col']) * (1 - young) + np.asarray(BIRCH['young_col']) * young
    return c * (1.0 + rng.uniform(-BIRCH['col_var'], BIRCH['col_var']))


def _leaf_on(mb, add_tube, p, stem_dir, side_sign, rng, scale=1.0, young=0.0):
    """Petiole + blade attached at p, pointing forward-sideways from the stem."""
    sd = _norm(np.asarray(stem_dir, float))
    perp = np.array([-sd[1], sd[0], 0.0]) * side_sign
    ang = rng.uniform(0.35, 0.95)
    d = _norm(sd * math.cos(ang) + perp * math.sin(ang) + np.array([0, 0, rng.uniform(-0.15, 0.25)]))
    pet_len = BIRCH['petiole'] * rng.uniform(0.7, 1.2) * scale
    pet = np.stack([p, p + d * pet_len * 0.5 + np.array([0, 0, 0.004]), p + d * pet_len])
    add_tube(mb, pet, 0.0012, 0.0009, np.asarray(BIRCH['stem_col']) * 1.3, sides=4)
    up = _norm(np.array([0.0, 0.0, 1.0]) + rng.normal(0, 0.35, 3))
    L = BIRCH['leaf_len'] * scale * rng.uniform(0.8, 1.12)
    _add_leaf(mb, pet[-1], d, up, L, BIRCH['leaf_w'] * L / BIRCH['leaf_len'], _leaf_colour(rng, young), rng)


def build_birch_twig(kind, seed, mb, add_tube, polyline):
    rng = np.random.default_rng(seed)
    if kind == 'BRANCHLET':
        main = polyline((0.0, 0.02, 0.0), (rng.uniform(-0.12, 0.12), 1.0), 0.9, rng.uniform(-0.08, 0.08),
                        rng, n=24, lift=0.05)
        _stem(mb, add_tube, main, BIRCH['stem_r'] * 1.25, BIRCH['stem_r'] * 0.4)
        nodes = np.linspace(0.05, 0.93, int(rng.integers(11, 14)))
        for i, t in enumerate(nodes):
            idx = min(int(t * (len(main) - 1)), len(main) - 2)
            p = main[idx]
            sd = main[idx + 1] - main[idx]
            side = 1.0 if i % 2 == 0 else -1.0
            if rng.random() < 0.5 and t < 0.8:
                # short shoot (brachyblast) with 2-3 leaves
                perp = np.array([-sd[1], sd[0], 0.0]) * side
                stub_d = _norm(_norm(sd) * 0.6 + _norm(perp) * 0.8)
                tip = p + stub_d * rng.uniform(0.025, 0.045)
                add_tube(mb, np.stack([p, (p + tip) / 2, tip]), 0.0022, 0.0018, np.asarray(BIRCH['stem_col']), sides=4)
                for k in range(int(rng.integers(2, 4))):
                    _leaf_on(mb, add_tube, tip, stub_d, (1.0 if k % 2 else -1.0), rng, 0.95)
            else:
                young = max(0.0, (t - 0.6) / 0.4)
                _leaf_on(mb, add_tube, p, sd, side, rng, 1.0 - 0.35 * young, young)
    else:  # SPRAY — short-shoot rosette
        stub = polyline((0.0, 0.02, 0.0), (rng.uniform(-0.15, 0.15), 1.0), 0.14, 0.0, rng, n=5, lift=0.05)
        _stem(mb, add_tube, stub, BIRCH['stem_r'] * 1.6, BIRCH['stem_r'] * 1.0)
        tip = stub[-1]
        n = int(rng.integers(3, 6))
        for k in range(n):
            a = -1.35 + 2.7 * (k + rng.uniform(0.2, 0.8)) / n
            d = np.array([math.sin(a), math.cos(a), 0.0])
            _leaf_on(mb, add_tube, tip, d, 1.0 if a > 0 else -1.0, rng, 1.75)
