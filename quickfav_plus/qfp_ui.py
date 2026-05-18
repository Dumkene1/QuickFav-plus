# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


def tag_redraw_all():
    wm = bpy.context.window_manager
    for window in wm.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            area.tag_redraw()


def readable(value):
    if not value:
        return "Any"
    return str(value).replace("_", " ").title()


def item_context_label(item):
    context_filter = item.get("context_filter", item.get("context", {}))

    if context_filter.get("show_everywhere"):
        return "All Contexts"

    parts = []

    for key in ("area_type", "space_type", "object_type", "object_mode"):
        value = context_filter.get(key)
        if value and value not in {"ANY", "UNKNOWN", "NONE"}:
            parts.append(readable(value))

    return " / ".join(parts) if parts else "Any Context"


def item_display_label(item):
    label = item.get("label") or item.get("operator") or item.get("menu_id") or "Unnamed"
    item_type = item.get("type", "UNKNOWN")
    return f"{item_context_label(item)} — {label} [{item_type}]"


def shortcut_label(key, ctrl=False, alt=False, shift=False):
    parts = []
    if ctrl:
        parts.append("Ctrl")
    if alt:
        parts.append("Alt")
    if shift:
        parts.append("Shift")
    parts.append(key or "None")
    return " + ".join(parts)
