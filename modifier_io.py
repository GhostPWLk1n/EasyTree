# SPDX-License-Identifier: GPL-3.0-or-later
# Easy Conifer — read/write Geometry Nodes modifier inputs across Blender versions.
# Copyright (C) 2026 Pavel Fomin
"""Blender 5.2 moved modifier input values from ID properties (mod["Socket_3"])
to mod.properties.inputs.Socket_3.value. These helpers support both."""


def _wrapper(mod, ident):
    props = getattr(mod, "properties", None)
    inputs = getattr(props, "inputs", None) if props is not None else None
    if inputs is not None:
        return getattr(inputs, ident, None)
    return None


def get_input(mod, ident):
    w = _wrapper(mod, ident)
    if w is not None:
        return w.value
    return mod[ident]


def set_input(mod, ident, value):
    w = _wrapper(mod, ident)
    if w is not None:
        cur = w.value
    else:
        cur = mod[ident]
    # coerce to the socket's own type
    if isinstance(cur, bool):
        value = bool(value)
    elif isinstance(cur, int) and not isinstance(value, bool):
        value = int(round(value))
    elif isinstance(cur, float):
        value = float(value)
    if w is not None:
        w.value = value
    else:
        mod[ident] = value
    try:
        mod.id_data.update_tag()
    except Exception:
        pass
