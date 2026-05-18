# SPDX-License-Identifier: GPL-3.0-or-later

"""
Context helpers.

v1.16:
Context matching is intentionally tolerant. Blender can report slightly different
area/space/object values after mode changes, especially when shortcuts are
registered globally. QuickFav Plus should not hide valid saved items too
aggressively.
"""


def normalize_mode(mode):
    if mode == "EDIT_MESH":
        return "EDIT"
    if mode == "PAINT_GPENCIL":
        return "PAINT_GREASE_PENCIL"
    if mode == "EDIT_GPENCIL":
        return "EDIT_GREASE_PENCIL"
    if mode == "SCULPT_GPENCIL":
        return "SCULPT_GREASE_PENCIL"
    return mode or "NONE"


def safe_context_mode(context):
    try:
        mode = getattr(context, "mode", None)
        if mode:
            return normalize_mode(mode)
    except Exception:
        pass

    obj = getattr(context, "object", None)
    if obj is not None:
        try:
            return normalize_mode(getattr(obj, "mode", "NONE"))
        except Exception:
            pass

    return "NONE"


def current_context_profile(context):
    obj = getattr(context, "object", None)
    area = getattr(context, "area", None)
    space = getattr(context, "space_data", None)

    return {
        "area_type": getattr(area, "type", "UNKNOWN") if area else "UNKNOWN",
        "space_type": getattr(space, "type", "UNKNOWN") if space else "UNKNOWN",
        "object_type": getattr(obj, "type", "NONE") if obj else "NONE",
        "object_mode": safe_context_mode(context),
    }


def make_context_filter(context, restrict=True):
    if not restrict:
        return {"show_everywhere": True}

    profile = current_context_profile(context)

    return {
        "show_everywhere": False,
        "area_type": profile.get("area_type", "UNKNOWN"),
        "space_type": profile.get("space_type", "UNKNOWN"),
        "object_type": profile.get("object_type", "NONE"),
        "object_mode": profile.get("object_mode", "NONE"),
    }


def _loose_value_match(saved, current):
    """
    General loose match.

    Treat unknown/none/any as wildcard because Blender context can be incomplete
    when called from global shortcuts.
    """
    if saved in {None, "", "ANY", "UNKNOWN", "NONE"}:
        return True
    if current in {None, "", "ANY", "UNKNOWN", "NONE"}:
        return True
    return saved == current


def _loose_mode_match(saved, current):
    saved = normalize_mode(saved)
    current = normalize_mode(current)

    if saved in {None, "", "ANY", "UNKNOWN", "NONE"}:
        return True
    if current in {None, "", "ANY", "UNKNOWN", "NONE"}:
        return True

    return saved == current


def context_matches(context, item):
    context_filter = item.get("context_filter")

    # Backward compatibility with older saved data.
    if context_filter is None:
        old = item.get("context", {})
        context_filter = {
            "show_everywhere": False,
            "area_type": old.get("area_type", "ANY"),
            "space_type": old.get("space_type", "ANY"),
            "object_type": old.get("object_type", "ANY"),
            "object_mode": old.get("object_mode", "ANY"),
        }

    if context_filter.get("show_everywhere"):
        return True

    current = current_context_profile(context)

    # Area should match when both sides are known.
    if not _loose_value_match(context_filter.get("area_type"), current.get("area_type")):
        return False

    # Space type is useful, but should not be overly strict.
    if not _loose_value_match(context_filter.get("space_type"), current.get("space_type")):
        return False

    # Object type is now advisory/tolerant.
    # This prevents valid mode-specific commands disappearing after mode switches.
    saved_obj = context_filter.get("object_type")
    current_obj = current.get("object_type")
    if saved_obj not in {None, "", "ANY", "UNKNOWN", "NONE"} and current_obj not in {None, "", "ANY", "UNKNOWN", "NONE"}:
        if saved_obj != current_obj:
            return False

    if not _loose_mode_match(context_filter.get("object_mode"), current.get("object_mode")):
        return False

    return True
