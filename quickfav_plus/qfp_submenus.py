# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .qfp_context import make_context_filter

KNOWN_SUBMENUS = [
    {"label": "Transform", "menu_id": "VIEW3D_MT_transform"},
    {"label": "Mirror", "menu_id": "VIEW3D_MT_mirror"},
    {"label": "Snap", "menu_id": "VIEW3D_MT_snap"},
    {"label": "Object", "menu_id": "VIEW3D_MT_object"},
    {"label": "Mesh", "menu_id": "VIEW3D_MT_edit_mesh"},
    {"label": "Mesh Vertices", "menu_id": "VIEW3D_MT_edit_mesh_vertices"},
    {"label": "Mesh Edges", "menu_id": "VIEW3D_MT_edit_mesh_edges"},
    {"label": "Mesh Faces", "menu_id": "VIEW3D_MT_edit_mesh_faces"},
    {"label": "Add", "menu_id": "VIEW3D_MT_add"},
    {"label": "Select Object", "menu_id": "VIEW3D_MT_select_object"},
    {"label": "Select Edit Mesh", "menu_id": "VIEW3D_MT_select_edit_mesh"},
]


def get_known_submenu_labels():
    return [entry["label"] for entry in KNOWN_SUBMENUS]


def get_known_submenu_by_label(label):
    for entry in KNOWN_SUBMENUS:
        if entry["label"] == label:
            return entry
    return None


def make_submenu_item(entry, context, restrict=True):
    return {
        "type": "SUBMENU",
        "label": entry["label"],
        "menu_id": entry["menu_id"],
        "icon": "",
        "context_filter": make_context_filter(context, restrict=restrict),
    }


def make_custom_submenu_item(label, menu_id, context, restrict_to_current_context=True):
    return {
        "type": "SUBMENU",
        "label": label or menu_id,
        "menu_id": menu_id,
        "icon": "",
        "context_filter": make_context_filter(context, restrict=restrict_to_current_context),
    }


def _menu_bl_label(menu_id):
    cls = getattr(bpy.types, menu_id, None)
    if cls is None:
        return ""
    return getattr(cls, "bl_label", "") or ""


def find_menu_ids(query="", limit=220):
    q = (query or "").lower().strip()
    results = []

    for name in dir(bpy.types):
        if "_MT_" not in name:
            continue

        label = _menu_bl_label(name)
        searchable = f"{name} {label}".lower()

        if q and q not in searchable:
            continue

        results.append((name, label))

    return sorted(results, key=lambda pair: pair[0].lower())[:limit]
