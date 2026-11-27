# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — materials. Copyright (C) 2026 Pavel Fomin
import os
import bpy

BARK_NAME = "Conifer Bark"
CONE_NAME = "Conifer Cone"


def _easy_tree_assets():
    """Path to Easy Tree's assets.blend if that add-on is installed, else None."""
    for mod_name in ("bl_ext.blender_org.easy_tree", "bl_ext.user_default.easy_tree", "easy_tree"):
        mod = __import__("sys").modules.get(mod_name)
        if mod and getattr(mod, "__file__", None):
            path = os.path.join(os.path.dirname(mod.__file__), "assets", "assets.blend")
            if os.path.exists(path):
                return path
    for base in bpy.utils.script_paths(subdir="extensions") + [bpy.utils.user_resource('EXTENSIONS')]:
        if not base or not os.path.isdir(base):
            continue
        for repo in os.listdir(base):
            path = os.path.join(base, repo, "easy_tree", "assets", "assets.blend")
            if os.path.exists(path):
                return path
    return None


def _easy_tree_bark():
    """Append Easy Tree's 'Bark' material (with its textures) if available."""
    if "Bark" in bpy.data.materials:
        return bpy.data.materials["Bark"]
    path = _easy_tree_assets()
    if not path:
        return None
    try:
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            if "Bark" in src.materials:
                dst.materials = ["Bark"]
    except Exception:
        return None
    return bpy.data.materials.get("Bark")


def _new_material(name):
    mat = bpy.data.materials.new(name)
    if hasattr(mat, "use_nodes") and not mat.use_nodes:
        mat.use_nodes = True
    return mat, mat.node_tree.nodes, mat.node_tree.links


def _procedural_bark():
    mat = bpy.data.materials.get(BARK_NAME)
    if mat:
        return mat
    mat, nodes, links = _new_material(BARK_NAME)
    bsdf = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 6.0, 1.0)
    links.new(tc.outputs["UV"], mapping.inputs["Vector"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Distortion"].default_value = 0.6
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.022, 0.016, 1.0)
    ramp.color_ramp.elements[1].color = (0.16, 0.11, 0.08, 1.0)
    links.new(noise.outputs["Factor" if "Factor" in noise.outputs else "Fac"], ramp.inputs[0])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    links.new(noise.outputs["Factor" if "Factor" in noise.outputs else "Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def get_bark_material(prefer_easy_tree=True):
    if prefer_easy_tree:
        mat = _easy_tree_bark()
        if mat:
            return mat
    return _procedural_bark()


def texture_dirs():
    """Folders searched for baked atlases: user re-bakes first, then shipped ones."""
    dirs = []
    try:
        dirs.append(bpy.utils.extension_path_user(__package__, path="textures", create=False))
    except Exception:
        pass
    dirs.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures"))
    return dirs


def atlas_paths(species):
    for d in texture_dirs():
        paths = {k: os.path.join(d, "%s_%s.png" % (species.lower(), k)) for k in ("albedo", "normal", "mask")}
        if all(os.path.exists(p) for p in paths.values()):
            return paths
    return None


def _load_image(path, non_color, pack=True):
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    img.alpha_mode = 'CHANNEL_PACKED' if non_color else 'STRAIGHT'
    if pack:
        img.pack()  # keep the .blend self-contained
    return img


def assign_atlas(mat, species):
    """(Re)load the atlas images of `species` into the material's texture nodes."""
    paths = atlas_paths(species)
    if not paths:
        return False
    nodes = mat.node_tree.nodes
    for key, nc in (("albedo", False), ("normal", True), ("mask", True)):
        node = nodes.get("EC_" + key)
        if node is None:
            continue
        old = node.image
        node.image = _load_image(paths[key], nc)
        if old and old.users == 0:
            bpy.data.images.remove(old)
        node.image.name = "EC_%s_%s" % (species.lower(), key)
    return True


FOLIAGE_MAT_VERSION = 3


def needle_material_name(species):
    if species == 'BIRCH':
        return "Birch Leaves"
    if species in LEAF_NAMES:
        return LEAF_NAMES[species]
    return "Conifer Needles %s" % species.title()


def get_needle_material(species='SPRUCE'):
    """Card material on the baked atlas: albedo+alpha, tangent normal map,
    mask (R AO, G needle mask, B thickness, A random id per leaf). Needles are re-tinted by the
    per-card attribute `needle_color` relative to the colour they were baked with."""
    from .twig_baker import REF_COLOR
    name = needle_material_name(species)
    mat = bpy.data.materials.get(name)
    if mat and mat.get("ec_version", 1) >= FOLIAGE_MAT_VERSION:
        return mat
    if mat:  # an older version: keep it for existing objects, build a fresh one
        mat.name = name + " (old)"
    mat, nodes, links = _new_material(name)
    mat["ec_version"] = FOLIAGE_MAT_VERSION
    nodes.clear()

    def n(idname, loc, **kw):
        node = nodes.new(idname)
        node.location = loc
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    uv = n("ShaderNodeUVMap", (-900, 0), uv_map="UVMap")
    tex = {}
    for i, key in enumerate(("albedo", "normal", "mask")):
        t = n("ShaderNodeTexImage", (-650, 250 - i * 300), name="EC_" + key, label=key.title(),
              interpolation='Linear')
        links.new(uv.outputs["UV"], t.inputs["Vector"])
        tex[key] = t
    sep = n("ShaderNodeSeparateColor", (-350, -400))
    links.new(tex["mask"].outputs["Color"], sep.inputs[0])
    ao, needle_mask, thick = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    leaf_id = tex["mask"].outputs["Alpha"]

    def math(op, a, b, loc, c=None):
        m = n("ShaderNodeMath", loc, operation=op)
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                links.new(v, m.inputs[i])
        return m.outputs[0]

    # per-leaf variation, 0 on wood: id in [-0.5, 0.5] * leaf mask
    var = math('MULTIPLY', math('SUBTRACT', leaf_id, 0.5, (-350, -650)), needle_mask, (-150, -650))

    # re-tint needles: albedo * needle_color / reference colour
    attr = n("ShaderNodeAttribute", (-650, 600), attribute_type='GEOMETRY', attribute_name="needle_color")
    ref = REF_COLOR[species]
    div = n("ShaderNodeVectorMath", (-350, 550), operation='DIVIDE')
    links.new(attr.outputs["Vector"], div.inputs[0])
    div.inputs[1].default_value = ref
    tinted = n("ShaderNodeMix", (-150, 450), data_type='RGBA', blend_type='MULTIPLY')
    tinted.inputs[0].default_value = 1.0
    links.new(tex["albedo"].outputs["Color"], tinted.inputs[6])
    links.new(div.outputs[0], tinted.inputs[7])
    base = n("ShaderNodeMix", (50, 350), data_type='RGBA')
    links.new(needle_mask, base.inputs[0])
    links.new(tex["albedo"].outputs["Color"], base.inputs[6])
    links.new(tinted.outputs[2], base.inputs[7])
    ao_f = n("ShaderNodeMapRange", (-150, -500))
    links.new(ao, ao_f.inputs["Value"])
    ao_f.inputs["To Min"].default_value = 0.62
    shaded = n("ShaderNodeMix", (250, 300), data_type='RGBA', blend_type='MULTIPLY')
    shaded.inputs[0].default_value = 1.0
    links.new(base.outputs[2], shaded.inputs[6])
    links.new(ao_f.outputs[0], shaded.inputs[7])
    # every leaf a little lighter or darker than its neighbour
    bfac = math('ADD', math('MULTIPLY', var, 0.4, (50, -700)), 1.0, (200, -700))
    lit = n("ShaderNodeMix", (400, 350), data_type='RGBA', blend_type='MULTIPLY')
    lit.inputs[0].default_value = 1.0
    links.new(shaded.outputs[2], lit.inputs[6])
    links.new(bfac, lit.inputs[7])
    shaded = lit

    nmap = n("ShaderNodeNormalMap", (-150, -100), space='TANGENT', uv_map="UVMap")
    links.new(tex["normal"].outputs["Color"], nmap.inputs["Color"])
    nmap.inputs["Strength"].default_value = 1.3

    bsdf = n("ShaderNodeBsdfPrincipled", (500, 200))
    links.new(shaded.outputs[2], bsdf.inputs["Base Color"])
    links.new(nmap.outputs[0], bsdf.inputs["Normal"])
    if "Coat Normal" in bsdf.inputs:   # the coat must follow the leaves, not the flat card
        links.new(nmap.outputs[0], bsdf.inputs["Coat Normal"])
    # roughness: wood 0.85, leaves glossy with a per-leaf spread
    leaf_r = {'POPLAR': 0.32, 'LINDEN': 0.42, 'COTONEASTER_HEDGE': 0.3, 'COTONEASTER': 0.3}.get(species, 0.48)
    if species in ('SPRUCE', 'FIR'):
        leaf_r = 0.55
    rmix = n("ShaderNodeMapRange", (200, -50))
    links.new(needle_mask, rmix.inputs["Value"])
    rmix.inputs["To Min"].default_value = 0.85
    rmix.inputs["To Max"].default_value = leaf_r
    rough = math('MULTIPLY_ADD', var, 0.35, (350, -50), rmix.outputs[0])   # var * 0.35 + roughness
    links.new(rough, bsdf.inputs["Roughness"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.35
    # coating and velvet, driven per tree by the generator (attributes leaf_coat, leaf_sheen)
    coat = n("ShaderNodeAttribute", (250, -150), attribute_type='GEOMETRY', attribute_name="leaf_coat")
    sheen = n("ShaderNodeAttribute", (250, -300), attribute_type='GEOMETRY', attribute_name="leaf_sheen")
    # coat only on leaves, stronger on some of them
    coat_w = math('MULTIPLY', coat.outputs["Fac"],
                  math('MULTIPLY', needle_mask, math('MULTIPLY_ADD', leaf_id, 0.9, (100, -200), 0.55), (250, -200)),
                  (400, -200))
    if "Coat Weight" in bsdf.inputs:
        links.new(coat_w, bsdf.inputs["Coat Weight"])
    if "Sheen Weight" in bsdf.inputs:
        links.new(sheen.outputs["Fac"], bsdf.inputs["Sheen Weight"])
    for sock, val in (("Coat Roughness", 0.12), ("Coat IOR", 1.45), ("Sheen Roughness", 0.35)):
        if sock in bsdf.inputs:
            bsdf.inputs[sock].default_value = val
    if "Sheen Tint" in bsdf.inputs:
        bsdf.inputs["Sheen Tint"].default_value = (0.75, 0.8, 0.7, 1.0)
    transl = n("ShaderNodeBsdfTranslucent", (500, -250))
    links.new(shaded.outputs[2], transl.inputs["Color"])
    links.new(nmap.outputs[0], transl.inputs["Normal"])
    tmix_f = n("ShaderNodeMath", (300, -400), operation='MULTIPLY')
    links.new(thick, tmix_f.inputs[0])
    tmix_f.inputs[1].default_value = 0.45 if species not in ('SPRUCE', 'FIR') else 0.3
    mix = n("ShaderNodeMixShader", (800, 100))
    links.new(tmix_f.outputs[0], mix.inputs[0])
    links.new(bsdf.outputs[0], mix.inputs[1])
    links.new(transl.outputs[0], mix.inputs[2])
    transp = n("ShaderNodeBsdfTransparent", (800, -150))
    cut = n("ShaderNodeMixShader", (1000, 0))
    # fade cards seen edge-on: no smeared, stretched leaves on the silhouette
    geo = n("ShaderNodeNewGeometry", (300, -600))
    facing = n("ShaderNodeVectorMath", (450, -600), operation='DOT_PRODUCT')
    links.new(geo.outputs["True Normal"], facing.inputs[0]); links.new(geo.outputs["Incoming"], facing.inputs[1])
    fade = n("ShaderNodeMapRange", (600, -600), interpolation_type='SMOOTHSTEP')
    links.new(math('ABSOLUTE', facing.outputs["Value"], None, (550, -650)), fade.inputs["Value"])
    fade.inputs["From Min"].default_value = 0.14
    fade.inputs["From Max"].default_value = 0.4
    links.new(math('MULTIPLY', tex["albedo"].outputs["Alpha"], fade.outputs[0], (750, -600)), cut.inputs[0])
    links.new(transp.outputs[0], cut.inputs[1])
    links.new(mix.outputs[0], cut.inputs[2])
    out = n("ShaderNodeOutputMaterial", (1200, 0))
    links.new(cut.outputs[0], out.inputs["Surface"])

    for attr_name, val in (("surface_render_method", 'DITHERED'), ("use_backface_culling", False)):
        if hasattr(mat, attr_name):
            try:
                setattr(mat, attr_name, val)
            except Exception:
                pass
    mat.diffuse_color = tuple(min(c * 2.5, 1.0) for c in ref) + (1.0,)
    assign_atlas(mat, species)
    return mat


def get_cone_material():
    mat = bpy.data.materials.get(CONE_NAME)
    if mat:
        return mat
    mat, nodes, links = _new_material(CONE_NAME)
    bsdf = nodes.get("Principled BSDF")
    tc = nodes.new("ShaderNodeTexCoord")
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = 'RINGS'
    wave.inputs["Scale"].default_value = 9.0
    wave.inputs["Distortion"].default_value = 2.0
    links.new(tc.outputs["Object"], wave.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.05, 0.025, 0.012, 1.0)
    ramp.color_ramp.elements[1].color = (0.32, 0.17, 0.08, 1.0)
    links.new(wave.outputs["Color"], ramp.inputs[0])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    links.new(wave.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mat.diffuse_color = (0.3, 0.16, 0.07, 1.0)
    return mat


BIRCH_BARK_NAME = "Birch Bark"


def get_birch_bark_material():
    """White birch bark: horizontal black lenticels, dark spots and patches, dark
    fissured base (object Z). Trunk and scaffold branches are white, second-order
    branches dark red-brown (attribute bark_level: 0 trunk, 1 scaffold, 2 secondary)."""
    mat = bpy.data.materials.get(BIRCH_BARK_NAME)
    if mat:
        return mat
    mat, nodes, links = _new_material(BIRCH_BARK_NAME)
    nodes.clear()

    def n(idname, loc, **kw):
        node = nodes.new(idname)
        node.location = loc
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    def math(op, a, b=None, loc=(0, 0), clamp=False):
        node = n("ShaderNodeMath", loc, operation=op, use_clamp=clamp)
        for idx, val in enumerate((a, b)):
            if val is None:
                continue
            if isinstance(val, bpy.types.NodeSocket):
                links.new(val, node.inputs[idx])
            else:
                node.inputs[idx].default_value = val
        return node.outputs[0]

    def step(v, lo, hi, loc):
        r = n("ShaderNodeMapRange", loc, interpolation_type='SMOOTHSTEP')
        links.new(v, r.inputs["Value"])
        r.inputs["From Min"].default_value = lo
        r.inputs["From Max"].default_value = hi
        return r.outputs["Result"]

    def noise(vec, scale, detail, loc, rough=0.5):
        t = n("ShaderNodeTexNoise", loc)
        links.new(vec, t.inputs["Vector"])
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough
        return t.outputs["Fac" if "Fac" in t.outputs else "Factor"]

    def mix_col(f, a, b, loc):
        mx = n("ShaderNodeMix", loc, data_type='RGBA')
        for idx, val in ((0, f), (6, a), (7, b)):
            if isinstance(val, bpy.types.NodeSocket):
                links.new(val, mx.inputs[idx])
            else:
                mx.inputs[idx].default_value = val
        return mx.outputs[2]

    uvn = n("ShaderNodeUVMap", (-1400, 200), uv_map="UVMap")
    sep = n("ShaderNodeSeparateXYZ", (-1200, 200))
    links.new(uvn.outputs["UV"], sep.inputs[0])
    tc = n("ShaderNodeTexCoord", (-1400, -300))
    osep = n("ShaderNodeSeparateXYZ", (-1200, -300))
    links.new(tc.outputs["Object"], osep.inputs[0])
    ux, vy, oz = sep.outputs[0], sep.outputs[1], osep.outputs[2]

    def vec(a, sa, b_, sb, loc):
        c = n("ShaderNodeCombineXYZ", loc)
        links.new(math('MULTIPLY', a, sa, (loc[0] - 150, loc[1] + 60)), c.inputs[0])
        links.new(math('MULTIPLY', b_, sb, (loc[0] - 150, loc[1] - 60)), c.inputs[1])
        return c.outputs[0]

    # lenticels: short in height, long around the trunk
    lent = step(noise(vec(ux, 5.0, vy, 70.0, (-950, 400)), 1.0, 2.0, (-750, 400)), 0.6, 0.68, (-550, 400))
    # larger black patches (branch scars, cracks)
    patch = step(noise(vec(ux, 2.0, vy, 5.0, (-950, 150)), 1.0, 4.0, (-750, 150), 0.65), 0.66, 0.72, (-550, 150))
    # medium dark spots — the "ripple" of birch bark between lenticels and patches
    spots = step(noise(vec(ux, 3.5, vy, 12.0, (-950, 650)), 1.0, 3.0, (-750, 650), 0.6), 0.575, 0.62, (-550, 650))
    dark_marks = math('MAXIMUM', math('MAXIMUM', lent, patch, (-450, 300)), spots, (-350, 300))
    # white bark with a slightly warm, uneven tone
    tone = noise(vec(ux, 3.0, vy, 2.0, (-950, -50)), 1.0, 3.0, (-750, -50))
    white = mix_col(tone, (0.62, 0.60, 0.55, 1), (0.80, 0.78, 0.72, 1), (-350, 0))
    bark_white = mix_col(dark_marks, white, (0.025, 0.022, 0.02, 1), (-150, 100))
    # trunk and scaffold branches white; second-order and finer branches dark red-brown
    lvl = n("ShaderNodeAttribute", (-950, -650), attribute_type='GEOMETRY', attribute_name="bark_level")
    whiteness = step(lvl.outputs["Fac"], 1.6, 1.4, (-550, -650))
    col = mix_col(whiteness, (0.05, 0.03, 0.022, 1), bark_white, (50, 0))
    # dark fissured base: a ragged edge 0.4..2 m high, vertical cracks with
    # white plates between them in the transition zone
    edge = math('ADD', math('MULTIPLY', noise(vec(ux, 4.0, vy, 0.6, (-950, -400)), 1.0, 3.0, (-750, -400)),
                            1.8, (-550, -400)), -0.1, (-400, -400))
    cracks = noise(vec(ux, 14.0, vy, 1.2, (-950, -900)), 1.0, 6.0, (-750, -900), 0.75)
    crack_m = step(cracks, 0.42, 0.6, (-550, -900))
    depth = math('SUBTRACT', edge, oz, (-250, -400))           # >0 below the edge
    base_m = step(math('ADD', depth, math('MULTIPLY', crack_m, 0.6, (-400, -650)), (-150, -500)), 0.2, 0.45, (-50, -400))
    fiss = noise(vec(ux, 30.0, vy, 3.0, (-950, -1150)), 1.0, 6.0, (-750, -1150), 0.7)
    base_col = mix_col(fiss, (0.015, 0.013, 0.012, 1), (0.09, 0.085, 0.08, 1), (-350, -1000))
    col = mix_col(base_m, col, base_col, (250, -100))

    bsdf = n("ShaderNodeBsdfPrincipled", (600, 0))
    links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.62
    height = math('ADD', math('MULTIPLY', dark_marks, -0.4, (300, -500)),
                  math('MULTIPLY', math('MULTIPLY', fiss, base_m, (100, -700)), 1.0, (300, -700)), (450, -550))
    bump = n("ShaderNodeBump", (600, -400))
    bump.inputs["Strength"].default_value = 0.35
    links.new(height, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    out = n("ShaderNodeOutputMaterial", (900, 0))
    links.new(bsdf.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = (0.75, 0.73, 0.68, 1.0)
    return mat


# --------------------------------------------------------- broadleaf barks
BARKS = {
    # plate colour, fissure colour, cells across / along (UV), fissure width, young bark colour, young radius
    'POPLAR': dict(name="Poplar Bark", plate=(0.16, 0.15, 0.13), fissure=(0.025, 0.022, 0.02), fu=7.0, fv=0.7,
                   width=0.14, young=(0.20, 0.22, 0.17), young_r=0.07, depth=0.8),
    'WILLOW': dict(name="Willow Bark", plate=(0.13, 0.11, 0.085), fissure=(0.02, 0.017, 0.014), fu=10.0, fv=1.0,
                   width=0.17, young=(0.30, 0.21, 0.07), young_r=0.045, depth=1.0),
    'MAPLE': dict(name="Maple Bark", plate=(0.085, 0.08, 0.072), fissure=(0.03, 0.027, 0.024), fu=12.0, fv=3.5,
                  width=0.07, young=(0.13, 0.12, 0.095), young_r=0.06, depth=0.4),
    'ASH': dict(name="Ash Bark", plate=(0.15, 0.15, 0.13), fissure=(0.04, 0.038, 0.034), fu=7.0, fv=2.6,
                width=0.12, young=(0.17, 0.18, 0.14), young_r=0.07, depth=0.6),
    'LINDEN': dict(name="Linden Bark", plate=(0.10, 0.09, 0.08), fissure=(0.03, 0.026, 0.022), fu=9.0, fv=1.1,
                   width=0.09, young=(0.13, 0.065, 0.045), young_r=0.05, depth=0.5),
    # shrubs: thin stems, mostly young bark
    'COTONEASTER': dict(name="Cotoneaster Bark", plate=(0.07, 0.055, 0.045), fissure=(0.03, 0.022, 0.018), fu=8.0,
                        fv=2.0, width=0.05, young=(0.09, 0.055, 0.04), young_r=0.012, depth=0.3),
    'PHYSOCARPUS': dict(name="Physocarpus Bark", plate=(0.20, 0.13, 0.08), fissure=(0.06, 0.035, 0.022), fu=6.0,
                        fv=0.5, width=0.2, young=(0.17, 0.10, 0.06), young_r=0.012, depth=0.9),   # peeling strips
    'HAZEL': dict(name="Hazel Bark", plate=(0.17, 0.12, 0.085), fissure=(0.09, 0.06, 0.04), fu=14.0, fv=4.0,
                  width=0.02, young=(0.16, 0.11, 0.075), young_r=0.025, depth=0.15),               # smooth, lenticels
    'BOXELDER': dict(name="Box Elder Bark", plate=(0.13, 0.12, 0.10), fissure=(0.035, 0.03, 0.025), fu=9.0,
                     fv=1.6, width=0.09, young=(0.11, 0.15, 0.085), young_r=0.04, depth=0.5),      # green young shoots
}


def get_species_bark_material(species):
    """Bark for broadleaf species; BIRCH has its own white bark."""
    if species == 'BIRCH':
        return get_birch_bark_material()
    p = BARKS[species]
    mat = bpy.data.materials.get(p['name'])
    if mat:
        return mat
    mat, nodes, links = _new_material(p['name'])
    nodes.clear()

    def n(idname, loc, **kw):
        node = nodes.new(idname)
        node.location = loc
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    def math(op, a, b=None, loc=(0, 0)):
        node = n("ShaderNodeMath", loc, operation=op)
        for idx, val in enumerate((a, b)):
            if val is None:
                continue
            if isinstance(val, bpy.types.NodeSocket):
                links.new(val, node.inputs[idx])
            else:
                node.inputs[idx].default_value = val
        return node.outputs[0]

    def step(v, lo, hi, loc):
        r = n("ShaderNodeMapRange", loc, interpolation_type='SMOOTHSTEP')
        links.new(v, r.inputs["Value"])
        r.inputs["From Min"].default_value = lo
        r.inputs["From Max"].default_value = hi
        return r.outputs["Result"]

    def mix_col(f, a, b, loc):
        mx = n("ShaderNodeMix", loc, data_type='RGBA')
        for idx, val in ((0, f), (6, a), (7, b)):
            if isinstance(val, bpy.types.NodeSocket):
                links.new(val, mx.inputs[idx])
            else:
                mx.inputs[idx].default_value = val
        return mx.outputs[2]

    uvn = n("ShaderNodeUVMap", (-1400, 0), uv_map="UVMap")
    sep = n("ShaderNodeSeparateXYZ", (-1250, 0))
    links.new(uvn.outputs["UV"], sep.inputs[0])
    vec = n("ShaderNodeCombineXYZ", (-1050, 0))
    links.new(math('MULTIPLY', sep.outputs[0], p['fu'], (-1150, 80)), vec.inputs[0])
    links.new(math('MULTIPLY', sep.outputs[1], p['fv'], (-1150, -80)), vec.inputs[1])
    warp = n("ShaderNodeTexNoise", (-1050, -250))
    links.new(vec.outputs[0], warp.inputs["Vector"])
    warp.inputs["Scale"].default_value = 1.5
    warp.inputs["Detail"].default_value = 3.0
    wv = n("ShaderNodeVectorMath", (-850, -100), operation='MULTIPLY_ADD')
    links.new(warp.outputs["Color"], wv.inputs[0])
    wv.inputs[1].default_value = (0.35, 0.35, 0.0)
    links.new(vec.outputs[0], wv.inputs[2])
    vor = n("ShaderNodeTexVoronoi", (-650, 0), feature='DISTANCE_TO_EDGE')
    links.new(wv.outputs[0], vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 1.0
    plate = step(vor.outputs["Distance"], 0.0, p['width'], (-450, 0))       # 0 in fissures, 1 on plates
    tone = n("ShaderNodeTexNoise", (-650, 300))
    links.new(wv.outputs[0], tone.inputs["Vector"])
    tone.inputs["Scale"].default_value = 3.0
    tone.inputs["Detail"].default_value = 4.0
    tf = tone.outputs["Fac" if "Fac" in tone.outputs else "Factor"]
    plate_col = mix_col(tf, tuple(c * 0.75 for c in p['plate']) + (1,), tuple(c * 1.25 for c in p['plate']) + (1,), (-450, 300))
    old = mix_col(plate, p['fissure'] + (1,), plate_col, (-250, 150))
    # young, smooth bark on thin branches; second-order branches always young
    rad = n("ShaderNodeAttribute", (-650, -450), attribute_type='GEOMETRY', attribute_name="bark_r")
    lvl = n("ShaderNodeAttribute", (-650, -650), attribute_type='GEOMETRY', attribute_name="bark_level")
    young_r = step(rad.outputs["Fac"], p['young_r'] * 1.5, p['young_r'] * 0.6, (-450, -450))
    young_l = step(lvl.outputs["Fac"], 1.4, 1.6, (-450, -650))
    young = math('MAXIMUM', young_r, young_l, (-250, -500))
    young_col = mix_col(tf, tuple(c * 0.85 for c in p['young']) + (1,), tuple(c * 1.1 for c in p['young']) + (1,), (-250, -250))
    col = mix_col(young, old, young_col, (0, 0))
    bsdf = n("ShaderNodeBsdfPrincipled", (300, 0))
    links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    bump = n("ShaderNodeBump", (100, -350))
    links.new(plate, bump.inputs["Height"])
    links.new(math('MULTIPLY', math('SUBTRACT', 1.0, young, (-100, -450)), p['depth'], (0, -450)), bump.inputs["Strength"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    out = n("ShaderNodeOutputMaterial", (550, 0))
    links.new(bsdf.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = p['plate'] + (1.0,)
    return mat


LEAF_NAMES = {'POPLAR': "Poplar Leaves", 'WILLOW': "Willow Leaves", 'MAPLE': "Maple Leaves",
              'ASH': "Ash Leaves", 'LINDEN': "Linden Leaves",
              'COTONEASTER': "Cotoneaster Leaves", 'PHYSOCARPUS': "Physocarpus Leaves",
              'HAZEL': "Hazel Leaves", 'BOXELDER': "Box Elder Leaves",
              'COTONEASTER_HEDGE': "Cotoneaster Clipped Leaves", 'PHYSOCARPUS_HEDGE': "Physocarpus Clipped Leaves"}
