# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — species presets. Copyright (C) 2026 Pavel Fomin
#
# Values are keyed by node-group input names (see nodes_builder.INTERFACE).
# Anything not listed keeps the group default.
import math

D = math.radians

PRESETS = {
    'PICEA_ABIES': ("Ель обыкновенная", "Norway spruce: drooping branches, hanging twig 'combs'", {
                "Height": 14.0, "Trunk Radius": 0.22, "Crown Base": 0.04,
        "Whorl Spacing": 0.45, "Branches per Whorl": 5, "Interwhorl Branches": 2,
        "Branch Length": 0.3, "Crown Shape": 1.0, "Skirt": 0.15,
        "Angle Bottom": D(112), "Angle Top": D(55), "Droop": 0.3, "Tip Upturn": 0.28,
        "Twig Density": 11.0, "Twig Length": 0.32, "Twig Angle": D(55), "Twig Hang": 0.55,
        "Flatness": 0.0, "Bare Inner Part": 0.3,
        "Needle Color": (0.034, 0.088, 0.027, 1.0),
        "Cones": True, "Cones Hang": True, "Cone Size": 0.13, "Cone Count": 40,
    }),
    'PICEA_PUNGENS': ("Ель колючая (голубая)", "Blue spruce: dense, stiff, horizontal branches, blue-grey needles", {
                "Height": 10.0, "Trunk Radius": 0.17, "Crown Base": 0.03,
        "Whorl Spacing": 0.33, "Branches per Whorl": 6, "Interwhorl Branches": 2,
        "Branch Length": 0.28, "Crown Shape": 1.05, "Skirt": 0.05,
        "Angle Bottom": D(96), "Angle Top": D(50), "Droop": 0.08, "Tip Upturn": 0.15,
        "Twig Density": 11.0, "Twig Length": 0.34, "Twig Angle": D(50), "Twig Hang": 0.05,
        "Flatness": 0.0, "Bare Inner Part": 0.15,
        "Needle Color": (0.13, 0.2, 0.22, 1.0), "Color Variation": 0.15,
        "Cones": False,
    }),
    'PICEA_OMORIKA': ("Ель сербская", "Serbian spruce: very narrow column, upturned branch tips", {
                "Height": 15.0, "Trunk Radius": 0.18, "Crown Base": 0.04,
        "Whorl Spacing": 0.42, "Branches per Whorl": 5, "Interwhorl Branches": 2,
        "Branch Length": 0.14, "Crown Shape": 1.3, "Skirt": 0.0,
        "Angle Bottom": D(122), "Angle Top": D(60), "Droop": 0.25, "Tip Upturn": 0.55,
        "Twig Density": 11.0, "Twig Length": 0.32, "Twig Hang": 0.25,
        "Flatness": 0.2, "Bare Inner Part": 0.15,
        "Needle Color": (0.032, 0.08, 0.03, 1.0),
        "Cones": True, "Cones Hang": True, "Cone Size": 0.06, "Cone Count": 30,
    }),
    'ABIES': ("Пихта", "Fir: flat horizontal sprays, needles in two rows, upright cones", {
                "Height": 15.0, "Trunk Radius": 0.2, "Crown Base": 0.04,
        "Whorl Spacing": 0.42, "Branches per Whorl": 5, "Interwhorl Branches": 2,
        "Branch Length": 0.24, "Crown Shape": 1.15, "Skirt": 0.1,
        "Angle Bottom": D(95), "Angle Top": D(62), "Droop": 0.06, "Tip Upturn": 0.08,
        "Twig Density": 11.0, "Twig Length": 0.4, "Twig Angle": D(62), "Twig Hang": -0.05,
                "Flatness": 0.6,
        "Bare Inner Part": 0.15,
        "Needle Color": (0.026, 0.074, 0.03, 1.0),
        "Cones": True, "Cones Hang": False, "Cone Size": 0.11, "Cone Count": 30, "Cone Zone": 0.2,
    }),
    'YOUNG': ("Молодая ёлочка", "Young 2 m spruce — Christmas-tree look", {
                "Height": 2.2, "Trunk Radius": 0.03, "Crown Base": 0.06,
        "Whorl Spacing": 0.16, "Branches per Whorl": 6, "Interwhorl Branches": 3,
        "Branch Length": 0.36, "Crown Shape": 1.0, "Skirt": 0.05,
        "Angle Bottom": D(98), "Angle Top": D(50), "Droop": 0.1, "Tip Upturn": 0.15,
        "Branch Thickness": 0.007, "Branch Resolution": 10,
        "Twig Density": 16.0, "Spray Size": 0.13, "Spray Spacing": 0.06, "Card Size": 1.2, "Twig Length": 0.45, "Twig Hang": 0.1,
                        "Bare Inner Part": 0.05, "Needle Color": (0.042, 0.105, 0.034, 1.0),
        "Cones": False,     }),
    'OLD': ("Старая ель", "Old forest spruce: high crown, dry lower branches, heavy droop", {
                "Height": 26.0, "Trunk Radius": 0.4, "Crown Base": 0.18,
        "Whorl Spacing": 0.6, "Spacing Jitter": 0.45, "Branches per Whorl": 5, "Interwhorl Branches": 3,
        "Branch Length": 0.2, "Crown Shape": 0.9, "Skirt": 0.0,
        "Angle Bottom": D(118), "Angle Top": D(60), "Droop": 0.45, "Tip Upturn": 0.35,
        "Branch Jitter": 0.3,
        "Twig Density": 10.0, "Twig Length": 0.3, "Twig Hang": 0.8,
        "Bare Inner Part": 0.45, "Dry Lower Part": 0.3,
        "Needle Color": (0.03, 0.074, 0.026, 1.0),
        "Cones": True, "Cones Hang": True, "Cone Count": 80, "Cone Size": 0.14,
            }),
}

# which baked twig atlas each preset uses
SPECIES_OF = {
    'PICEA_ABIES': 'SPRUCE', 'PICEA_PUNGENS': 'SPRUCE', 'PICEA_OMORIKA': 'SPRUCE',
    'ABIES': 'FIR', 'YOUNG': 'SPRUCE', 'OLD': 'SPRUCE',
}

ENUM_ITEMS = [(key, label, desc) for key, (label, desc, _) in PRESETS.items()]


def preset_values(key):
    if key in PRESETS:
        return PRESETS[key][2]
    if key in HEDGE_PRESETS:
        return HEDGE_PRESETS[key][2]
    return BROADLEAF_PRESETS[key][2]


def is_broadleaf(key):
    return key in BROADLEAF_PRESETS


is_birch = is_broadleaf  # backwards-compatible name


def apply(mod, ids, key, defaults=None):
    """Write preset values into a Geometry Nodes modifier.

    `defaults` (name -> value) is applied first so that switching presets
    on an existing tree resets everything the preset doesn't mention.
    """
    from .modifier_io import set_input
    values = dict(defaults or {})
    values.update(preset_values(key))
    for name, val in values.items():
        ident = ids.get(name)
        if ident is not None:
            set_input(mod, ident, val)


# ---------------------------------------------------------------- broadleaves
# (label, description, values); the leaf atlas / bark species is in SPECIES_OF
BROADLEAF_PRESETS = {
    'BETULA_PENDULA': ("Берёза повислая", "Silver birch: arching scaffold branches, long hanging twigs", {
        "Height": 17.0, "Trunk Radius": 0.2, "Crown Base": 0.3, "Lean": D(4), "Trunk Wiggle": 0.3,
        "Branch Count": 50, "Branch Length": 0.85, "Crown Width": 0.5,
        "Angle Bottom": D(75), "Angle Top": D(18), "Arch": 0.5,
        "Secondary Density": 3.5, "Secondary Length": 0.45, "Secondary Droop": 0.45,
        "Twig Density": 7.0, "Twig Length": 0.6, "Card Length": 0.6, "Weeping": 0.85,
        "Leaf Color": (0.062, 0.150, 0.024, 1.0),
    }),
    'BETULA_PUBESCENS': ("Берёза пушистая", "Downy birch: ascending branches, twigs not weeping", {
        "Height": 15.0, "Trunk Radius": 0.18, "Crown Base": 0.28, "Lean": D(3), "Trunk Wiggle": 0.4,
        "Branch Count": 46, "Branch Length": 0.85, "Crown Width": 0.55,
        "Angle Bottom": D(62), "Angle Top": D(26), "Arch": 0.12,
        "Secondary Density": 4.0, "Secondary Length": 0.42, "Secondary Droop": 0.15,
        "Twig Density": 8.0, "Twig Length": 0.45, "Card Length": 0.45, "Weeping": 0.25,
        "Leaf Color": (0.055, 0.135, 0.025, 1.0),
    }),
    'BETULA_YOUNG': ("Молодая берёза", "Young 6 m birch with a slender trunk", {
        "Height": 6.0, "Trunk Radius": 0.065, "Crown Base": 0.22, "Lean": D(3), "Trunk Wiggle": 0.25,
        "Branch Count": 34, "Branch Length": 0.85, "Crown Width": 0.5,
        "Angle Bottom": D(62), "Angle Top": D(25), "Arch": 0.2, "Branch Thickness": 0.022,
        "Secondary Density": 4.5, "Secondary Length": 0.35, "Secondary Droop": 0.2,
        "Twig Density": 9.0, "Twig Length": 0.35, "Card Length": 0.35, "Weeping": 0.45,
        "Spray Size": 0.2, "Spray Spacing": 0.14,
        "Leaf Color": (0.07, 0.165, 0.026, 1.0),
    }),
    'BETULA_AUTUMN': ("Берёза осенняя", "Silver birch in autumn colours", {
        "Height": 17.0, "Trunk Radius": 0.2, "Crown Base": 0.3, "Lean": D(5), "Trunk Wiggle": 0.3,
        "Branch Count": 50, "Branch Length": 0.85, "Crown Width": 0.5,
        "Angle Bottom": D(75), "Angle Top": D(18), "Arch": 0.5,
        "Secondary Density": 3.5, "Secondary Length": 0.45, "Secondary Droop": 0.45,
        "Twig Density": 6.0, "Twig Length": 0.6, "Card Length": 0.6, "Weeping": 0.85,
        "Leaf Color": (0.42, 0.27, 0.02, 1.0), "Color Variation": 0.4,
    }),
    'POPULUS_ITALICA': ("Тополь пирамидальный", "Lombardy poplar: narrow column of steep branches", {
        "Height": 25.0, "Trunk Radius": 0.35, "Crown Base": 0.05, "Lean": D(1), "Trunk Wiggle": 0.15,
        "Branch Count": 90, "Branch Length": 0.95, "Crown Width": 0.22,
        "Angle Bottom": D(30), "Angle Top": D(10), "Arch": -0.1, "Tip Upturn": 0.2, "Branch Thickness": 0.025,
        "Secondary Density": 2.2, "Secondary Length": 0.4, "Secondary Angle": D(30), "Secondary Droop": 0.0,
        "Twig Density": 5.0, "Twig Length": 0.5, "Card Length": 0.5, "Card Size": 1.25, "Weeping": 0.1,
        "Spray Size": 0.38, "Spray Spacing": 0.24, "Bare Inner Part": 0.05,
        "Leaf Color": (0.042, 0.111, 0.026, 1.0),
    }),
    'POPULUS_NIGRA': ("Тополь чёрный", "Black poplar: massive trunk splitting into a broad crown", {
        "Height": 24.0, "Trunk Radius": 0.5, "Crown Base": 0.25, "Lean": D(6), "Trunk Wiggle": 0.5,
        "Leader Height": 0.55, "Branch Count": 40, "Branch Length": 0.9, "Crown Width": 0.75,
        "Angle Bottom": D(58), "Angle Top": D(22), "Arch": 0.25, "Tip Upturn": 0.1, "Branch Thickness": 0.035,
        "Secondary Density": 2.5, "Secondary Length": 0.45, "Secondary Droop": 0.2,
        "Twig Density": 7.0, "Twig Length": 0.6, "Card Length": 0.6, "Card Size": 1.25, "Weeping": 0.3,
        "Leaf Color": (0.042, 0.111, 0.026, 1.0),
    }),
    'SALIX_BABYLONICA': ("Ива плакучая", "Weeping willow: curtains of long hanging shoots", {
        "Height": 13.0, "Trunk Radius": 0.35, "Crown Base": 0.25, "Lean": D(6), "Trunk Wiggle": 0.4,
        "Leader Height": 0.55, "Branch Count": 34, "Branch Length": 0.95, "Crown Width": 0.95,
        "Angle Bottom": D(48), "Angle Top": D(18), "Arch": 0.35, "Branch Thickness": 0.04,
        "Secondary Density": 2.5, "Secondary Length": 0.4, "Secondary Droop": 0.5,
        "Twig Density": 4.5, "Twig Length": 2.4, "Card Length": 0.8, "Card Size": 1.25, "Weeping": 1.0, "Twig Wood": True,
        "Spray Size": 0.31, "Spray Spacing": 0.26, "Bare Inner Part": 0.3,
        "Leaf Color": (0.098, 0.163, 0.065, 1.0),
    }),
    'SALIX_ALBA': ("Ива белая (ветла)", "White willow: short trunk, broad crown, silvery leaves", {
        "Height": 16.0, "Trunk Radius": 0.45, "Crown Base": 0.15, "Lean": D(7), "Trunk Wiggle": 0.5,
        "Leader Height": 0.45, "Branch Count": 34, "Branch Length": 0.9, "Crown Width": 0.85,
        "Angle Bottom": D(50), "Angle Top": D(25), "Arch": 0.2, "Branch Thickness": 0.035,
        "Secondary Density": 3.0, "Secondary Length": 0.4, "Secondary Droop": 0.15,
        "Twig Density": 7.0, "Twig Length": 0.7, "Card Length": 0.7, "Card Size": 1.25, "Weeping": 0.6,
        "Leaf Color": (0.15, 0.2, 0.13, 1.0),
    }),
    'ACER_PLATANOIDES': ("Клён остролистный", "Norway maple: dense round crown, opposite branching", {
        "Height": 18.0, "Trunk Radius": 0.32, "Crown Base": 0.22, "Lean": D(3), "Trunk Wiggle": 0.3,
        "Leader Height": 0.6, "Branch Count": 30, "Opposite": True, "Branch Length": 0.95, "Crown Width": 0.9,
        "Angle Bottom": D(62), "Angle Top": D(32), "Arch": 0.15, "Tip Upturn": 0.15, "Branch Thickness": 0.035,
        "Secondary Density": 3.0, "Secondary Length": 0.5, "Secondary Angle": D(55), "Secondary Droop": 0.15,
        "Twig Density": 6.0, "Twig Length": 0.5, "Card Length": 0.5, "Card Size": 1.25, "Weeping": 0.15,
        "Spray Size": 0.44, "Spray Spacing": 0.19,
        "Leaf Color": (0.058, 0.163, 0.026, 1.0),
    }),
    'ACER_AUTUMN': ("Клён осенний", "Norway maple in autumn: orange-red leaves", {
        "Height": 18.0, "Trunk Radius": 0.32, "Crown Base": 0.22, "Lean": D(3), "Trunk Wiggle": 0.3,
        "Leader Height": 0.6, "Branch Count": 30, "Opposite": True, "Branch Length": 0.95, "Crown Width": 0.9,
        "Angle Bottom": D(62), "Angle Top": D(32), "Arch": 0.15, "Tip Upturn": 0.15, "Branch Thickness": 0.035,
        "Secondary Density": 3.0, "Secondary Length": 0.5, "Secondary Angle": D(55), "Secondary Droop": 0.15,
        "Twig Density": 6.0, "Twig Length": 0.5, "Card Length": 0.5, "Card Size": 1.25, "Weeping": 0.15,
        "Spray Size": 0.44, "Spray Spacing": 0.19,
        "Leaf Color": (0.50, 0.13, 0.015, 1.0), "Color Variation": 0.45,
    }),
    'FRAXINUS_EXCELSIOR': ("Ясень обыкновенный", "Common ash: open crown, upturned branch tips, pinnate leaves", {
        "Height": 22.0, "Trunk Radius": 0.35, "Crown Base": 0.3, "Lean": D(3), "Trunk Wiggle": 0.3,
        "Leader Height": 0.7, "Branch Count": 26, "Opposite": True, "Branch Length": 0.8, "Crown Width": 0.65,
        "Angle Bottom": D(55), "Angle Top": D(25), "Arch": 0.1, "Tip Upturn": 0.3, "Branch Thickness": 0.03,
        "Secondary Density": 2.0, "Secondary Length": 0.4, "Secondary Angle": D(45), "Secondary Droop": 0.0,
        "Twig Density": 4.5, "Twig Length": 0.75, "Card Length": 0.75, "Card Size": 1.25, "Weeping": 0.0,
        "Spray Size": 0.56, "Spray Spacing": 0.26, "Bare Inner Part": 0.35,
        "Leaf Color": (0.052, 0.143, 0.033, 1.0),
    }),
    'TILIA_CORDATA': ("Липа мелколистная", "Small-leaved linden: dense ovoid crown, upturned twigs", {
        "Height": 20.0, "Trunk Radius": 0.35, "Crown Base": 0.18, "Lean": D(2), "Trunk Wiggle": 0.25,
        "Leader Height": 0.85, "Branch Count": 55, "Branch Length": 0.9, "Crown Width": 0.7,
        "Angle Bottom": D(75), "Angle Top": D(30), "Arch": 0.4, "Tip Upturn": 0.35, "Branch Thickness": 0.03,
        "Secondary Density": 3.2, "Secondary Length": 0.45, "Secondary Droop": 0.25,
        "Twig Density": 6.0, "Twig Length": 0.5, "Card Length": 0.5, "Card Size": 1.25, "Weeping": 0.35,
        "Spray Size": 0.38, "Spray Spacing": 0.15,
        "Leaf Color": (0.065, 0.169, 0.031, 1.0),
    }),
}
# per-species surface: gloss (coat) / sheen (velvet) and autumn crown tints
_SURFACE = {
    'BETULA_PENDULA': {"Leaf Gloss": 0.1}, 'BETULA_PUBESCENS': {"Leaf Sheen": 0.2}, 'BETULA_YOUNG': {"Leaf Gloss": 0.1},
    'BETULA_AUTUMN': {"Edge Color": (0.55, 0.38, 0.03, 1.0), "Edge Color Amount": 0.35, "Inner Shade": 0.45},
    'POPULUS_ITALICA': {"Leaf Gloss": 0.45}, 'POPULUS_NIGRA': {"Leaf Gloss": 0.45},
    'SALIX_BABYLONICA': {"Leaf Sheen": 0.15}, 'SALIX_ALBA': {"Leaf Sheen": 0.4},
    'ACER_PLATANOIDES': {"Leaf Gloss": 0.2},
    'ACER_AUTUMN': {"Leaf Gloss": 0.2, "Edge Color": (0.65, 0.3, 0.02, 1.0), "Edge Color Amount": 0.4,
                    "Hue Variation": 0.06},
    'FRAXINUS_EXCELSIOR': {"Leaf Gloss": 0.15}, 'TILIA_CORDATA': {"Leaf Gloss": 0.3},
}
for _k, _v in _SURFACE.items():
    BROADLEAF_PRESETS[_k][2].update(_v)

# ------------------------------------------------------------------- shrubs
_SHRUB_BASE = {
    "Crown Base": 0.03, "Lean": D(2), "Trunk Wiggle": 0.5, "Leader Height": 0.9, "Branch Jitter": 0.3,
    "Branch Resolution": 6, "Trunk Resolution": 6, "Branch Profile": 4, "Bare Inner Part": 0.08, "Card Size": 1.2,
}


def _shrub(**kw):
    v = dict(_SHRUB_BASE)
    v.update(kw)
    return v


SHRUB_PRESETS = {
    'COTONEASTER_LUCIDUS': ("Кизильник блестящий", "Cotoneaster: dense twiggy shrub with small glossy leaves", _shrub(**{
        "Height": 2.0, "Trunk Radius": 0.012, "Stems": 10, "Stem Spread": D(20),
        "Branch Count": 80, "Branch Length": 0.9, "Crown Width": 1.0,
        "Angle Bottom": D(55), "Angle Top": D(25), "Arch": 0.35, "Tip Upturn": 0.1, "Branch Thickness": 0.03,
        "Secondary Density": 6.0, "Secondary Length": 0.45, "Secondary Droop": 0.25,
        "Twig Density": 10.0, "Twig Length": 0.3, "Card Length": 0.3, "Weeping": 0.35,
        "Spray Size": 0.16, "Spray Spacing": 0.1,
        "Leaf Color": (0.025, 0.070, 0.016, 1.0), "Leaf Gloss": 0.7})),
    'PHYSOCARPUS_OPULIFOLIUS': ("Пузыреплодник калинолистный", "Ninebark: arching stems, 3-lobed leaves", _shrub(**{
        "Height": 2.5, "Trunk Radius": 0.015, "Stems": 14, "Stem Spread": D(30),
        "Branch Count": 90, "Branch Length": 0.9, "Crown Width": 1.15,
        "Angle Bottom": D(60), "Angle Top": D(25), "Arch": 0.6, "Branch Thickness": 0.03,
        "Secondary Density": 5.0, "Secondary Length": 0.45, "Secondary Droop": 0.4,
        "Twig Density": 9.0, "Twig Length": 0.4, "Card Length": 0.4, "Weeping": 0.45,
        "Spray Size": 0.2, "Spray Spacing": 0.12,
        "Leaf Color": (0.050, 0.120, 0.025, 1.0), "Leaf Gloss": 0.1})),
    'PHYSOCARPUS_DIABOLO': ("Пузыреплодник 'Diabolo'", "Purple-leaved ninebark", _shrub(**{
        "Height": 2.5, "Trunk Radius": 0.015, "Stems": 14, "Stem Spread": D(30),
        "Branch Count": 90, "Branch Length": 0.9, "Crown Width": 1.15,
        "Angle Bottom": D(60), "Angle Top": D(25), "Arch": 0.6, "Branch Thickness": 0.03,
        "Secondary Density": 5.0, "Secondary Length": 0.45, "Secondary Droop": 0.4,
        "Twig Density": 9.0, "Twig Length": 0.4, "Card Length": 0.4, "Weeping": 0.45,
        "Spray Size": 0.2, "Spray Spacing": 0.12,
        "Leaf Color": (0.11, 0.025, 0.035, 1.0), "Edge Color": (0.22, 0.06, 0.04, 1.0), "Edge Color Amount": 0.25,
        "Hue Variation": 0.02, "Leaf Gloss": 0.15})),
    'PHYSOCARPUS_LUTEUS': ("Пузыреплодник 'Luteus'", "Golden-leaved ninebark", _shrub(**{
        "Height": 2.5, "Trunk Radius": 0.015, "Stems": 14, "Stem Spread": D(30),
        "Branch Count": 90, "Branch Length": 0.9, "Crown Width": 1.15,
        "Angle Bottom": D(60), "Angle Top": D(25), "Arch": 0.6, "Branch Thickness": 0.03,
        "Secondary Density": 5.0, "Secondary Length": 0.45, "Secondary Droop": 0.4,
        "Twig Density": 9.0, "Twig Length": 0.4, "Card Length": 0.4, "Weeping": 0.45,
        "Spray Size": 0.2, "Spray Spacing": 0.12,
        "Leaf Color": (0.20, 0.21, 0.03, 1.0), "Edge Color": (0.38, 0.32, 0.03, 1.0), "Edge Color Amount": 0.35,
        "Inner Shade": 0.45, "Leaf Gloss": 0.1})),
    'CORYLUS_AVELLANA': ("Лещина (орешник)", "Hazel: tall multi-stem shrub, broad velvety leaves", _shrub(**{
        "Height": 5.0, "Trunk Radius": 0.04, "Crown Base": 0.12, "Stems": 9, "Stem Spread": D(18),
        "Branch Count": 70, "Branch Length": 0.9, "Crown Width": 0.95,
        "Angle Bottom": D(55), "Angle Top": D(20), "Arch": 0.3, "Branch Thickness": 0.025,
        "Secondary Density": 3.5, "Secondary Length": 0.45, "Secondary Droop": 0.25,
        "Twig Density": 6.0, "Twig Length": 0.55, "Card Length": 0.55, "Weeping": 0.2,
        "Spray Size": 0.3, "Spray Spacing": 0.2, "Bare Inner Part": 0.15,
        "Leaf Color": (0.055, 0.130, 0.030, 1.0), "Leaf Sheen": 0.45, "Leaf Gloss": 0.0})),
    'ACER_NEGUNDO': ("Клён ясенелистный", "Box elder: leaning stems, sprawling crown, compound leaves", _shrub(**{
        "Height": 9.0, "Trunk Radius": 0.14, "Crown Base": 0.15, "Lean": D(8), "Trunk Wiggle": 0.6,
        "Stems": 4, "Stem Spread": D(28), "Leader Height": 0.6,
        "Branch Count": 44, "Opposite": True, "Branch Length": 0.9, "Crown Width": 1.05,
        "Angle Bottom": D(62), "Angle Top": D(30), "Arch": 0.4, "Tip Upturn": 0.1, "Branch Thickness": 0.035,
        "Branch Resolution": 8, "Trunk Resolution": 10, "Branch Profile": 5,
        "Secondary Density": 3.0, "Secondary Length": 0.45, "Secondary Droop": 0.3,
        "Twig Density": 6.0, "Twig Length": 0.6, "Card Length": 0.6, "Weeping": 0.3, "Card Size": 1.25,
        "Spray Size": 0.4, "Spray Spacing": 0.3, "Bare Inner Part": 0.2,
        "Leaf Color": (0.070, 0.160, 0.040, 1.0), "Leaf Gloss": 0.1})),
}
BROADLEAF_PRESETS.update(SHRUB_PRESETS)
SPECIES_OF.update({
    'COTONEASTER_LUCIDUS': 'COTONEASTER', 'PHYSOCARPUS_OPULIFOLIUS': 'PHYSOCARPUS',
    'PHYSOCARPUS_DIABOLO': 'PHYSOCARPUS', 'PHYSOCARPUS_LUTEUS': 'PHYSOCARPUS',
    'CORYLUS_AVELLANA': 'HAZEL', 'ACER_NEGUNDO': 'BOXELDER',
})

# ----------------------------------------------------------- clipped shrubs
# shapes for the Clipped Shrub Generator (applied on top of a species preset)
SHRUB_FORMS = {
    'BALL': ("Шар", "Clipped ball", {
        "Surface Roughness": 0.25,
        "Width": 1.2, "Depth": 1.2, "Height": 1.1, "Roundness": 1.0, "Top Taper": 1.0, "Bottom Cut": 0.12,
        "Unevenness": 0.02, "Fuzz Density": 3.0, "Fuzz Size": 0.3, "Card Tilt": D(30)}),
    'CUBE': ("Куб", "Box hedge with slightly rounded edges", {
        "Surface Roughness": 0.18,
        "Width": 2.0, "Depth": 0.9, "Height": 1.0, "Roundness": 0.15, "Top Taper": 1.0, "Bottom Cut": 0.04,
        "Unevenness": 0.015, "Fuzz Density": 2.5, "Fuzz Size": 0.3, "Card Tilt": D(26)}),
    'TRAPEZOID': ("Трапеция", "Hedge narrowing to the top (lets light reach the bottom)", {
        "Surface Roughness": 0.18,
        "Width": 2.0, "Depth": 1.0, "Height": 1.2, "Roundness": 0.2, "Top Taper": 0.5, "Bottom Cut": 0.04,
        "Unevenness": 0.015, "Fuzz Density": 2.5, "Fuzz Size": 0.3, "Card Tilt": D(26)}),
    'NATURAL': ("Естественный", "Unclipped, irregular rounded shrub", {
        "Surface Roughness": 0.6,
        "Width": 1.8, "Depth": 1.6, "Height": 1.5, "Roundness": 0.95, "Top Taper": 0.85, "Bottom Cut": 0.1,
        "Unevenness": 0.18, "Fuzz Density": 5.0, "Fuzz Size": 0.4, "Card Tilt": D(40)}),
}
SHRUB_FORM_ITEMS = [(k, label, desc) for k, (label, desc, _) in SHRUB_FORMS.items()]

HEDGE_PRESETS = {
    'HEDGE_COTONEASTER': ("Кизильник блестящий (стриж.)", "Clipped cotoneaster: small glossy dark leaves", {
        "Leaf Color": (0.025, 0.070, 0.016, 1.0), "Edge Color": (0.07, 0.15, 0.025, 1.0), "Edge Color Amount": 0.25,
        "Leaf Gloss": 0.7, "Card Size": 0.22, "Surface Density": 140.0, "Inner Layer": 1.2, "Stem Radius": 0.015}),
    'HEDGE_PHYSOCARPUS': ("Пузыреплодник (стриж.)", "Clipped green ninebark", {
        "Leaf Color": (0.050, 0.120, 0.025, 1.0), "Edge Color": (0.10, 0.19, 0.03, 1.0), "Edge Color Amount": 0.25,
        "Leaf Gloss": 0.1, "Card Size": 0.26, "Surface Density": 115.0, "Inner Layer": 1.2, "Stem Radius": 0.018}),
    'HEDGE_PHYSO_DIABOLO': ("Пузыреплодник 'Diabolo' (стриж.)", "Clipped purple ninebark", {
        "Leaf Color": (0.11, 0.025, 0.035, 1.0), "Edge Color": (0.22, 0.06, 0.04, 1.0), "Edge Color Amount": 0.35,
        "Leaf Gloss": 0.15, "Card Size": 0.26, "Surface Density": 115.0, "Inner Layer": 1.2, "Stem Radius": 0.018, "Hue Variation": 0.02}),
    'HEDGE_PHYSO_LUTEUS': ("Пузыреплодник 'Luteus' (стриж.)", "Clipped golden ninebark", {
        "Leaf Color": (0.20, 0.21, 0.03, 1.0), "Edge Color": (0.38, 0.32, 0.03, 1.0), "Edge Color Amount": 0.4,
        "Leaf Gloss": 0.1, "Card Size": 0.26, "Surface Density": 115.0, "Inner Layer": 1.2, "Stem Radius": 0.018}),
}
SPECIES_OF.update({'HEDGE_COTONEASTER': 'COTONEASTER_HEDGE', 'HEDGE_PHYSOCARPUS': 'PHYSOCARPUS_HEDGE',
                   'HEDGE_PHYSO_DIABOLO': 'PHYSOCARPUS_HEDGE', 'HEDGE_PHYSO_LUTEUS': 'PHYSOCARPUS_HEDGE'})
BARK_OF = {'COTONEASTER_HEDGE': 'COTONEASTER', 'PHYSOCARPUS_HEDGE': 'PHYSOCARPUS'}


def is_hedge(key):
    return key in HEDGE_PRESETS


def hedge_values(key, form):
    v = dict(HEDGE_PRESETS[key][2])
    v.update(SHRUB_FORMS[form][2])
    return v

BIRCH_PRESETS = BROADLEAF_PRESETS   # backwards-compatible name

SPECIES_OF.update({
    'BETULA_PENDULA': 'BIRCH', 'BETULA_PUBESCENS': 'BIRCH', 'BETULA_YOUNG': 'BIRCH', 'BETULA_AUTUMN': 'BIRCH',
    'POPULUS_ITALICA': 'POPLAR', 'POPULUS_NIGRA': 'POPLAR',
    'SALIX_BABYLONICA': 'WILLOW', 'SALIX_ALBA': 'WILLOW',
    'ACER_PLATANOIDES': 'MAPLE', 'ACER_AUTUMN': 'MAPLE',
    'FRAXINUS_EXCELSIOR': 'ASH', 'TILIA_CORDATA': 'LINDEN',
})

BROADLEAF_ENUM_ITEMS = [(key, label, desc) for key, (label, desc, _) in BROADLEAF_PRESETS.items()]
BIRCH_ENUM_ITEMS = BROADLEAF_ENUM_ITEMS

# the preset list with section headings (an item with an empty identifier is a heading)
ALL_ENUM_ITEMS = (
    [("", "Хвойные", "")] + ENUM_ITEMS +
    [("", "Лиственные", "")] + [i for i in BROADLEAF_ENUM_ITEMS if i[0] not in SHRUB_PRESETS] +
    [("", "Кусты", "")] + [i for i in BROADLEAF_ENUM_ITEMS if i[0] in SHRUB_PRESETS] +
    [("", "Стриженые кусты", "")] + [(k, label, desc) for k, (label, desc, _) in HEDGE_PRESETS.items()]
)
