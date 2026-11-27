# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — operators. Copyright (C) 2026 Pavel Fomin
import random
import bpy

import os

from . import nodes_builder, broadleaf_builder, hedge_builder, presets, materials, twig_baker
from .modifier_io import get_input, set_input

MOD_NAME = "Conifer Generator"


def is_broadleaf_group(group):
    return group is not None and (group.name.startswith(broadleaf_builder.GROUP_NAME) or
                                  any(group.name.startswith(n) for n in broadleaf_builder.LEGACY_GROUP_NAMES))


is_birch_group = is_broadleaf_group  # backwards-compatible name


def is_hedge_group(group):
    return group is not None and group.name.startswith(hedge_builder.GROUP_NAME)


def group_kind(group):
    if is_hedge_group(group):
        return 'HEDGE'
    if is_broadleaf_group(group):
        return 'BROADLEAF'
    if group is not None and group.name.startswith(nodes_builder.GROUP_NAME):
        return 'CONIFER'
    return None


def preset_kind(key):
    if presets.is_hedge(key):
        return 'HEDGE'
    return 'BROADLEAF' if presets.is_broadleaf(key) else 'CONIFER'


def conifer_modifier(obj):
    """The Easy Conifer generator modifier (conifer, broadleaf or clipped shrub) of an object, or None."""
    if obj is None:
        return None
    for mod in obj.modifiers:
        g = mod.node_group if mod.type == 'NODES' else None
        if g and group_kind(g):
            return mod
    return None


def _defaults(mod):
    return {'HEDGE': hedge_builder.interface_defaults, 'BROADLEAF': broadleaf_builder.interface_defaults,
            'CONIFER': nodes_builder.interface_defaults}[group_kind(mod.node_group)]()


def _set_materials(context, mod, key):
    ids = _ids(mod)
    if presets.is_hedge(key):
        sp = presets.SPECIES_OF[key]
        set_input(mod, ids["Bark Material"], materials.get_species_bark_material(presets.BARK_OF[sp]))
        set_input(mod, ids["Leaf Material"], materials.get_needle_material(sp))
    elif presets.is_broadleaf(key):
        sp = presets.SPECIES_OF.get(key, 'BIRCH')
        set_input(mod, ids["Bark Material"], materials.get_species_bark_material(sp))
        set_input(mod, ids["Leaf Material"], materials.get_needle_material(sp))
    else:
        set_input(mod, ids["Bark Material"],
                  materials.get_bark_material(context.scene.easy_conifer_use_easy_tree_bark))
        set_input(mod, ids["Needle Material"],
                  materials.get_needle_material(presets.SPECIES_OF.get(key, 'SPRUCE')))
        set_input(mod, ids["Cone Material"], materials.get_cone_material())


def _ids(mod):
    return nodes_builder.input_identifiers(mod.node_group)


def _ensure_transparent_bounces(context, op, minimum=32):
    """Overlapping alpha cards need more transparent bounces than Cycles' default 8,
    otherwise deep parts of the crown render as black blocks."""
    cyc = getattr(context.scene, "cycles", None)
    if cyc is not None and cyc.transparent_max_bounces < minimum:
        cyc.transparent_max_bounces = minimum
        op.report({'INFO'}, "Cycles: Transparent Max Bounces raised to %d for needle cards" % minimum)


class EASYCONIFER_OT_bake(bpy.types.Operator):
    bl_idname = "object.easy_conifer_bake"
    bl_label = "Bake Twig Textures"
    bl_description = ("Build high-poly twigs with real needles and bake them into the card texture atlas "
                      "(albedo+alpha, normal, mask). Takes about a minute per species at 2048")
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        species = list(twig_baker.SPECIES) if scene.easy_conifer_bake_species == 'ALL' else [scene.easy_conifer_bake_species]
        try:
            out_dir = bpy.utils.extension_path_user(__package__, path="textures", create=True)
        except Exception:
            out_dir = os.path.join(bpy.utils.user_resource('DATAFILES'), "easy_conifer", "textures")
        wm = context.window_manager
        for sp in species:
            wm.progress_begin(0, 4)
            try:
                twig_baker.bake_atlas(sp, out_dir, resolution=int(scene.easy_conifer_bake_resolution),
                                      seed=scene.easy_conifer_bake_seed,
                                      density_scale=scene.easy_conifer_bake_density,
                                      report=lambda msg: None)
            finally:
                wm.progress_end()
            mat = bpy.data.materials.get(materials.needle_material_name(sp))
            if mat:
                materials.assign_atlas(mat, sp)
        self.report({'INFO'}, "Twig textures baked to %s" % out_dir)
        return {'FINISHED'}


class EASYCONIFER_OT_reset_textures(bpy.types.Operator):
    bl_idname = "object.easy_conifer_reset_textures"
    bl_label = "Use Shipped Textures"
    bl_description = "Delete re-baked twig textures and go back to the ones shipped with the add-on"
    bl_options = {'REGISTER'}

    def execute(self, context):
        try:
            d = bpy.utils.extension_path_user(__package__, path="textures", create=False)
        except Exception:
            d = None
        if d and os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".png"):
                    os.remove(os.path.join(d, f))
        for sp in twig_baker.SPECIES:
            mat = bpy.data.materials.get(materials.needle_material_name(sp))
            if mat:
                materials.assign_atlas(mat, sp)
        return {'FINISHED'}


class EASYCONIFER_OT_add(bpy.types.Operator):
    bl_idname = "object.easy_conifer_add"
    bl_label = "Add Tree"
    bl_description = "Add a procedural tree (conifer or broadleaf) with the selected preset at the 3D cursor"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(name="Preset", items=presets.ALL_ENUM_ITEMS)
    seed: bpy.props.IntProperty(name="Seed", default=-1, min=-1,
                                description="-1 picks a random seed")

    def invoke(self, context, event):
        self.preset = context.scene.easy_conifer_preset
        return self.execute(context)

    def execute(self, context):
        kind = preset_kind(self.preset)
        tree = {'HEDGE': hedge_builder.ensure_hedge_group, 'BROADLEAF': broadleaf_builder.ensure_broadleaf_group,
                'CONIFER': nodes_builder.ensure_group}[kind]()
        table = {'HEDGE': presets.HEDGE_PRESETS, 'BROADLEAF': presets.BROADLEAF_PRESETS, 'CONIFER': presets.PRESETS}[kind]
        label = table[self.preset][0]
        form = context.scene.easy_conifer_shrub_form
        if kind == 'HEDGE':
            label = "%s — %s" % (label, presets.SHRUB_FORMS[form][0])
        obj = bpy.data.objects.new(label, bpy.data.meshes.new({'HEDGE': "Shrub", 'BROADLEAF': "Tree"}.get(kind, "Conifer")))
        obj.location = context.scene.cursor.location
        context.collection.objects.link(obj)
        mod = obj.modifiers.new(tree.name, 'NODES')
        mod.node_group = tree
        ids = _ids(mod)

        presets.apply(mod, ids, self.preset, _defaults(mod))
        if kind == 'HEDGE':
            _apply_form(mod, ids, form)
        seed = self.seed if self.seed >= 0 else random.randint(0, 99999)
        set_input(mod, ids["Seed"], seed)
        _set_materials(context, mod, self.preset)
        _ensure_transparent_bounces(context, self)
        obj["easy_conifer_preset"] = self.preset

        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        self.report({'INFO'}, "Added %s (seed %d)" % (obj.name, seed))
        return {'FINISHED'}


class EASYCONIFER_OT_apply_preset(bpy.types.Operator):
    bl_idname = "object.easy_conifer_apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Reset the selected conifers to the chosen preset (seed and materials are kept)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(conifer_modifier(o) for o in context.selected_objects)

    def execute(self, context):
        key = context.scene.easy_conifer_preset
        n = skipped = 0
        for obj in context.selected_objects:
            mod = conifer_modifier(obj)
            if not mod:
                continue
            if preset_kind(key) != group_kind(mod.node_group):
                skipped += 1  # a preset can't turn a conifer into a birch, a tree into a clipped shrub, etc.
                continue
            ids = _ids(mod)
            seed = get_input(mod, ids["Seed"])
            form_vals = None
            if preset_kind(key) == 'HEDGE':   # keep the current shape, change the species
                form_vals = {nm: get_input(mod, ids[nm]) for nm in presets.SHRUB_FORMS['BALL'][2] if nm in ids}
            presets.apply(mod, ids, key, _defaults(mod))
            if form_vals:
                for nm, v in form_vals.items():
                    set_input(mod, ids[nm], v)
            set_input(mod, ids["Seed"], seed)
            _set_materials(context, mod, key)
            obj["easy_conifer_preset"] = key
            obj.update_tag()
            n += 1
        msg = "Preset applied to %d object(s)" % n
        if skipped:
            msg += "; %d skipped (other tree type — add a new tree instead)" % skipped
        self.report({'INFO'}, msg)
        return {'FINISHED'}


def _apply_form(mod, ids, form):
    for name, val in presets.SHRUB_FORMS[form][2].items():
        if name in ids:
            set_input(mod, ids[name], val)


class EASYCONIFER_OT_apply_form(bpy.types.Operator):
    bl_idname = "object.easy_conifer_apply_form"
    bl_label = "Apply Form"
    bl_description = "Give the selected clipped shrubs the chosen form (ball, box, trapezoid, natural)"
    bl_options = {'REGISTER', 'UNDO'}

    keep_size: bpy.props.BoolProperty(name="Keep Size", default=False,
                                      description="Keep the current width, depth and height")

    @classmethod
    def poll(cls, context):
        return any(is_hedge_group(getattr(conifer_modifier(o), "node_group", None)) for o in context.selected_objects)

    def execute(self, context):
        form = context.scene.easy_conifer_shrub_form
        n = 0
        for obj in context.selected_objects:
            mod = conifer_modifier(obj)
            if not mod or not is_hedge_group(mod.node_group):
                continue
            ids = _ids(mod)
            size = {k: get_input(mod, ids[k]) for k in ("Width", "Depth", "Height")}
            _apply_form(mod, ids, form)
            if self.keep_size:
                for k, v in size.items():
                    set_input(mod, ids[k], v)
            obj.update_tag()
            n += 1
        self.report({'INFO'}, "Form '%s' applied to %d shrub(s)" % (presets.SHRUB_FORMS[form][0], n))
        return {'FINISHED'}


class EASYCONIFER_OT_new_seed(bpy.types.Operator):
    bl_idname = "object.easy_conifer_new_seed"
    bl_label = "New Seed"
    bl_description = "Give the selected conifers a new random seed"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(conifer_modifier(o) for o in context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            mod = conifer_modifier(obj)
            if mod:
                set_input(mod, _ids(mod)["Seed"], random.randint(0, 99999))
                obj.update_tag()
        return {'FINISHED'}


class EASYCONIFER_OT_needles_visibility(bpy.types.Operator):
    bl_idname = "object.easy_conifer_needles_visibility"
    bl_label = "Needles in Viewport"
    bl_description = "Show or hide needles / leaves of all trees in the viewport (render is not affected)"
    bl_options = {'REGISTER', 'UNDO'}

    show: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        for obj in bpy.data.objects:
            mod = conifer_modifier(obj)
            if mod:
                set_input(mod, _ids(mod)["Visible in Viewport"], self.show)
                obj.update_tag()
        return {'FINISHED'}


class EASYCONIFER_OT_rebuild(bpy.types.Operator):
    bl_idname = "object.easy_conifer_rebuild"
    bl_label = "Rebuild Node Group"
    bl_description = ("Recreate the Conifer and Broadleaf Generator node groups from the add-on "
                      "(use after updating the add-on; manual edits to the group are lost)")
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        users = []
        for obj in bpy.data.objects:
            mod = conifer_modifier(obj)
            if mod:
                ids = _ids(mod)
                vals = {name: get_input(mod, ident) for name, ident in ids.items()}
                legacy_birch = "Crown Shape" in ids and is_broadleaf_group(mod.node_group)
                if legacy_birch:
                    # 0.4 birch: "Branch Length" was a fraction of height; now it is the crown reach
                    vals.update({"Branch Length": 0.85, "Crown Width": 0.5})
                users.append((obj, mod, vals, group_kind(mod.node_group)))
        trees = {'CONIFER': nodes_builder.build_main_group(), 'BROADLEAF': broadleaf_builder.build_broadleaf_group(),
                 'HEDGE': hedge_builder.build_hedge_group()}
        for obj, mod, vals, kind in users:
            tree = trees[kind]
            new_ids = nodes_builder.input_identifiers(tree)
            mod.node_group = tree
            for name, val in vals.items():
                if name in new_ids:
                    try:
                        set_input(mod, new_ids[name], val)
                    except Exception:
                        pass
            obj.update_tag()
        for name in (nodes_builder.GROUP_NAME, nodes_builder.CLUSTER_GROUP_NAME, broadleaf_builder.GROUP_NAME,
                     hedge_builder.GROUP_NAME) + \
                broadleaf_builder.LEGACY_GROUP_NAMES:
            old = bpy.data.node_groups.get(name + " (old)")
            if old and old.users == 0:
                bpy.data.node_groups.remove(old)
        self.report({'INFO'}, "Rebuilt; %d tree(s) updated" % len(users))
        return {'FINISHED'}


classes = (
    EASYCONIFER_OT_add,
    EASYCONIFER_OT_apply_preset,
    EASYCONIFER_OT_apply_form,
    EASYCONIFER_OT_new_seed,
    EASYCONIFER_OT_needles_visibility,
    EASYCONIFER_OT_rebuild,
    EASYCONIFER_OT_bake,
    EASYCONIFER_OT_reset_textures,
)
