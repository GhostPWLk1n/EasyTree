# SPDX-License-Identifier: GPL-3.0-or-later
"""Load the add-on straight from the clone (no zip, no install) and return the API module.

    import _boot; ec = _boot.load_addon()
"""
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_addon():
    """Import the repo as package `easy_conifer` (the add-on uses relative imports), register it."""
    import bpy
    if "easy_conifer_api" in bpy.app.driver_namespace:
        return bpy.app.driver_namespace["easy_conifer_api"]
    tmp = tempfile.mkdtemp(prefix="ec_pkg_")
    os.symlink(REPO, os.path.join(tmp, "easy_conifer"), target_is_directory=True)
    sys.path.insert(0, tmp)
    import easy_conifer
    easy_conifer.register()
    return bpy.app.driver_namespace["easy_conifer_api"]


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
