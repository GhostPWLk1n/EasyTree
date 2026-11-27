# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — sidebar panel (lives in the "Easy Tree" tab next to Easy Tree).
# Copyright (C) 2026 Pavel Fomin
import bpy

from . import nodes_builder
from .operators import conifer_modifier, is_broadleaf_group, is_hedge_group
from . import presets

QUICK = (
    ("Shape", ("Height", "Trunk Radius", "Crown Base")),
    ("Branches", ("Whorl Spacing", "Branch Length", "Crown Shape", "Droop", "Tip Upturn", "Twig Hang")),
    ("Needle Cards", ("Card Size", "Spray Size", "Spray Spacing", "Flatness", "Needle Color")),
    ("Extras", ("Twig Wood", "Cones", "Wind")),
)

QUICK_HEDGE = (
    ("Shape", ("Width", "Depth", "Height", "Roundness", "Top Taper", "Bottom Cut", "Unevenness")),
    ("Foliage", ("Card Size", "Surface Density", "Inner Layer", "Foliage Depth", "Surface Roughness", "Fuzz Density", "Fuzz Size")),
    ("Leaf Colour", ("Leaf Color", "Inner Shade", "Top Light", "Edge Color", "Edge Color Amount", "Hue Variation",
                     "Leaf Gloss")),
    ("Inside", ("Stems per Metre", "Inner Branch Density")),
)

QUICK_BROADLEAF = (
    ("Shape", ("Height", "Trunk Radius", "Crown Base", "Leader Height", "Lean")),
    ("Branches", ("Branch Count", "Crown Width", "Branch Length", "Arch", "Tip Upturn", "Opposite")),
    ("Shrub", ("Stems", "Stem Spread")),
    ("Leaf Cards", ("Twig Length", "Weeping", "Card Length", "Spray Size")),
    ("Leaf Colour", ("Leaf Color", "Inner Shade", "Top Light", "Edge Color", "Edge Color Amount", "Hue Variation",
                     "Leaf Gloss", "Leaf Sheen")),
    ("Extras", ("Leaves", "Twig Wood", "Wind")),
)


def draw_input(layout, mod, ident, text):
    props = getattr(mod, "properties", None)
    inputs = getattr(props, "inputs", None) if props is not None else None
    if inputs is not None:  # Blender 5.2+
        w = getattr(inputs, ident, None)
        if w is not None:
            layout.prop(w, "value", text=text)
    else:
        layout.prop(mod, '["%s"]' % ident, text=text)


class EASYCONIFER_PT_panel(bpy.types.Panel):
    bl_label = "Easy Conifer & Broadleaf"
    bl_idname = "EASYCONIFER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Easy Tree"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)
        col.prop(scene, "easy_conifer_preset", text="")
        if presets.is_hedge(scene.easy_conifer_preset):
            col.prop(scene, "easy_conifer_shrub_form", text="Form")
        col.operator("object.easy_conifer_add", text="Add Tree", icon='ADD')
        layout.prop(scene, "easy_conifer_use_easy_tree_bark")

        bake = layout.box()
        bake.label(text="Twig Textures", icon='TEXTURE')
        row = bake.row(align=True)
        row.prop(scene, "easy_conifer_bake_species", text="")
        row.prop(scene, "easy_conifer_bake_resolution", text="")
        row = bake.row(align=True)
        row.prop(scene, "easy_conifer_bake_seed")
        row.prop(scene, "easy_conifer_bake_density", text="Density")
        row = bake.row(align=True)
        row.operator("object.easy_conifer_bake", icon='RENDER_STILL')
        row.operator("object.easy_conifer_reset_textures", text="", icon='LOOP_BACK')

        mod = conifer_modifier(context.active_object)
        if mod is None:
            return
        box = layout.box()
        row = box.row(align=True)
        row.operator("object.easy_conifer_apply_preset", text="Apply Preset")
        row.operator("object.easy_conifer_new_seed", text="New Seed", icon='FILE_REFRESH')
        ids = nodes_builder.input_identifiers(mod.node_group)
        if is_hedge_group(mod.node_group):
            row = box.row(align=True)
            row.prop(scene, "easy_conifer_shrub_form", text="")
            row.operator("object.easy_conifer_apply_form", text="Apply Form")
        quick = QUICK_HEDGE if is_hedge_group(mod.node_group) else (
            QUICK_BROADLEAF if is_broadleaf_group(mod.node_group) else QUICK)
        for title, names in quick:
            sub = box.column(align=True)
            sub.label(text=title)
            for name in names:
                if name in ids:
                    draw_input(sub, mod, ids[name], name)
        box.label(text="All settings: Modifier Properties", icon='MODIFIER')

        row = layout.row(align=True)
        row.label(text="Foliage in viewport:")
        row.operator("object.easy_conifer_needles_visibility", text="", icon='HIDE_OFF').show = True
        row.operator("object.easy_conifer_needles_visibility", text="", icon='HIDE_ON').show = False
        layout.operator("object.easy_conifer_rebuild", icon='NODETREE')


classes = (EASYCONIFER_PT_panel,)
