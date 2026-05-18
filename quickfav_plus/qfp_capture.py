# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .qfp_context import make_context_filter, context_matches


def _same_rna_pointer(a, b):
    if a is None or b is None:
        return False
    try:
        return a.as_pointer() == b.as_pointer()
    except Exception:
        return a == b


def _context_pointer_paths(context):
    candidates = []

    def add(path, value):
        if value is not None:
            candidates.append((path, value))

    for path in ("scene", "object", "active_object", "tool_settings", "space_data"):
        try:
            add(path, getattr(context, path))
        except Exception:
            pass

    try:
        add("space_data.overlay", context.space_data.overlay)
    except Exception:
        pass

    try:
        add("space_data.shading", context.space_data.shading)
    except Exception:
        pass

    return candidates


def _find_pointer_context_path(context, pointer):
    for path, candidate in _context_pointer_paths(context):
        if _same_rna_pointer(pointer, candidate):
            return path
    return ""


def resolve_context_path(context, path):
    current = context
    for part in (path or "").split("."):
        if not part:
            continue
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _button_prop_is_boolean(button_prop):
    try:
        return getattr(button_prop, "type", "") == "BOOLEAN"
    except Exception:
        return False


def _operator_identifier_to_id(identifier):
    if not identifier or "_OT_" not in identifier:
        return ""
    namespace, op_name = identifier.split("_OT_", 1)
    return f"{namespace.lower()}.{op_name}"


def _safe_json_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        out = []
        for entry in value:
            safe = _safe_json_value(entry)
            if safe is None and entry is not None:
                return None
            out.append(safe)
        return out
    return None


def _capture_operator_properties(button_operator):
    props = {}
    try:
        rna_props = button_operator.bl_rna.properties
    except Exception:
        return props

    for prop in rna_props:
        identifier = getattr(prop, "identifier", "")
        if not identifier or identifier == "rna_type":
            continue
        try:
            value = getattr(button_operator, identifier)
        except Exception:
            continue
        safe = _safe_json_value(value)
        if safe is not None or value is None:
            props[identifier] = safe
    return props


def capture_button_item(context):
    button_operator = getattr(context, "button_operator", None)

    if button_operator is not None:
        try:
            identifier = button_operator.bl_rna.identifier
        except Exception:
            identifier = ""

        operator_id = _operator_identifier_to_id(identifier)
        if not operator_id:
            return None

        label = getattr(button_operator.bl_rna, "name", "") or operator_id
        props = _capture_operator_properties(button_operator)

        return {
            "type": "OPERATOR",
            "label": label,
            "operator": operator_id,
            "properties": props,
            "icon": "",
            "context_filter": make_context_filter(context, restrict=True),
        }

    button_pointer = getattr(context, "button_pointer", None)
    button_prop = getattr(context, "button_prop", None)

    if button_pointer is not None and button_prop is not None:
        prop_id = getattr(button_prop, "identifier", "")
        prop_name = getattr(button_prop, "name", "") or prop_id

        if prop_id and _button_prop_is_boolean(button_prop):
            context_path = _find_pointer_context_path(context, button_pointer)
            if context_path:
                return {
                    "type": "PROPERTY_TOGGLE",
                    "label": prop_name,
                    "operator": "",
                    "properties": {},
                    "icon": "",
                    "context_path": context_path,
                    "property_identifier": prop_id,
                    "context_filter": make_context_filter(context, restrict=True),
                }

        return {
            "type": "PROPERTY_UNSUPPORTED",
            "label": prop_name,
            "operator": "",
            "properties": {},
            "icon": "",
            "property_identifier": prop_id,
            "context_filter": make_context_filter(context, restrict=True),
        }

    return None


def resolve_operator(operator_id):
    if not operator_id or "." not in operator_id:
        return None
    namespace, op_name = operator_id.split(".", 1)
    namespace_ops = getattr(bpy.ops, namespace, None)
    if namespace_ops is None:
        return None
    return getattr(namespace_ops, op_name, None)


def operator_label_from_id(operator_id):
    op = resolve_operator(operator_id)
    if op is None:
        return operator_id
    try:
        return getattr(op.get_rna_type(), "name", "") or operator_id
    except Exception:
        return operator_id


def find_operator_ids(query="", limit=260):
    q = (query or "").lower().strip()
    results = []

    for namespace in dir(bpy.ops):
        if namespace.startswith("_"):
            continue
        namespace_ops = getattr(bpy.ops, namespace, None)
        if namespace_ops is None:
            continue
        try:
            op_names = dir(namespace_ops)
        except Exception:
            continue

        for op_name in op_names:
            if op_name.startswith("_"):
                continue
            op_id = f"{namespace}.{op_name}"
            label = operator_label_from_id(op_id)
            searchable = f"{op_id} {label}".lower()
            if q and q not in searchable:
                continue
            results.append((op_id, label))

    return sorted(set(results), key=lambda pair: pair[0])[:limit]


def make_operator_item(operator_id, context, label="", restrict_to_current_context=True):
    return {
        "type": "OPERATOR",
        "label": label or operator_label_from_id(operator_id),
        "operator": operator_id,
        "properties": {},
        "icon": "",
        "context_filter": make_context_filter(context, restrict=restrict_to_current_context),
    }


def is_item_available(context, item):
    item_type = item.get("type", "")

    if not context_matches(context, item):
        return False

    if item_type == "SUBMENU":
        return hasattr(bpy.types, item.get("menu_id", ""))

    if item_type == "PROPERTY_TOGGLE":
        target = resolve_context_path(context, item.get("context_path", ""))
        prop_id = item.get("property_identifier", "")
        return target is not None and hasattr(target, prop_id)

    if item_type == "PROPERTY_UNSUPPORTED":
        return False

    if item_type == "OPERATOR":
        return resolve_operator(item.get("operator", "")) is not None

    return False
