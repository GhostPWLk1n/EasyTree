# SPDX-License-Identifier: GPL-3.0-or-later
#
# Easy Conifer — procedural spruce and fir generator for Blender (Geometry Nodes).
# Companion to Easy Tree by Jacob Johnston (GPL-3.0-or-later).
# Copyright (C) 2026 Pavel Fomin
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See the LICENSE file for details.

import bpy

from . import operators, panel, presets


def register():
    bpy.types.Scene.easy_conifer_preset = bpy.props.EnumProperty(
        name="Tree Preset",
        description="Species preset for new trees",
        items=presets.ALL_ENUM_ITEMS,
        default='PICEA_ABIES',
    )
    bpy.types.Scene.easy_conifer_shrub_form = bpy.props.EnumProperty(
        name="Shrub Form", description="Form of new clipped shrubs", items=presets.SHRUB_FORM_ITEMS, default='BALL')
    bpy.types.Scene.easy_conifer_use_easy_tree_bark = bpy.props.BoolProperty(
        name="Use Easy Tree Bark",
        description="Use the bark material from Easy Tree if that add-on is installed",
        default=True,
    )
    bpy.types.Scene.easy_conifer_bake_species = bpy.props.EnumProperty(
        name="Species", items=[('SPRUCE', "Ель", "Spruce twigs"), ('FIR', "Пихта", "Fir twigs"), ('BIRCH', "Берёза", ""), ('POPLAR', "Тополь", ""),
                               ('WILLOW', "Ива", ""), ('MAPLE', "Клён", ""), ('ASH', "Ясень", ""), ('LINDEN', "Липа", ""),
                               ('COTONEASTER', "Кизильник", ""), ('PHYSOCARPUS', "Пузыреплодник", ""),
                               ('HAZEL', "Лещина", ""), ('BOXELDER', "Клён ясенелистный", ""),
                               ('COTONEASTER_HEDGE', "Кизильник (стриж.)", ""), ('PHYSOCARPUS_HEDGE', "Пузыреплодник (стриж.)", ""),
                               ('ALL', "Все", "All species")], default='ALL')
    bpy.types.Scene.easy_conifer_bake_resolution = bpy.props.EnumProperty(
        name="Resolution", items=[('1024', "1024", ""), ('2048', "2048", ""), ('4096', "4096", "")],
        default='2048', description="Atlas size (2x2 twigs)")
    bpy.types.Scene.easy_conifer_bake_seed = bpy.props.IntProperty(name="Seed", default=0, min=0)
    bpy.types.Scene.easy_conifer_bake_density = bpy.props.FloatProperty(
        name="Needle Density", default=1.0, min=0.3, max=3.0, description="Needle density multiplier")
    for cls in operators.classes + panel.classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operators.classes + panel.classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.easy_conifer_use_easy_tree_bark
    del bpy.types.Scene.easy_conifer_shrub_form
    for p in ("species", "resolution", "seed", "density"):
        delattr(bpy.types.Scene, "easy_conifer_bake_" + p)
    del bpy.types.Scene.easy_conifer_preset
