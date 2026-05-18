# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path
import bpy


DEFAULT_DATA = {
    "version": 9,
    "items": [],
    "shortcut": {"key": "", "ctrl": False, "alt": False, "shift": False},
}


def storage_path():
    config_dir = Path(bpy.utils.user_resource("CONFIG", path="", create=True))
    return config_dir / "quickfav_plus_favorites.json"


def _fresh_default():
    return json.loads(json.dumps(DEFAULT_DATA))


def load_data():
    path = storage_path()
    if not path.exists():
        return _fresh_default()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _fresh_default()

        data.setdefault("version", 9)
        data.setdefault("items", [])
        data.setdefault("shortcut", DEFAULT_DATA["shortcut"].copy())

        if not isinstance(data["items"], list):
            data["items"] = []

        return data
    except Exception:
        return _fresh_default()


def save_data(data):
    path = storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def list_items():
    return load_data().get("items", [])


def get_shortcut():
    return load_data().get("shortcut", DEFAULT_DATA["shortcut"].copy())


def save_shortcut(key, ctrl=False, alt=True, shift=False):
    data = load_data()
    data["shortcut"] = {
        "key": key,
        "ctrl": bool(ctrl),
        "alt": bool(alt),
        "shift": bool(shift),
    }
    save_data(data)


def make_item_key(item):
    return json.dumps(
        {
            "type": item.get("type", ""),
            "operator": item.get("operator", ""),
            "properties": item.get("properties", {}),
            "menu_id": item.get("menu_id", ""),
            "property_path": item.get("property_path", ""),
            "context_path": item.get("context_path", ""),
            "property_identifier": item.get("property_identifier", ""),
            "value": item.get("value", None),
        },
        sort_keys=True,
        default=str,
    )


def contains_item(item):
    key = make_item_key(item)
    return any(make_item_key(saved) == key for saved in list_items())


def add_item(item):
    data = load_data()
    if contains_item(item):
        return False
    data["items"].append(item)
    save_data(data)
    return True


def remove_item(item):
    data = load_data()
    key = make_item_key(item)
    before = len(data["items"])
    data["items"] = [saved for saved in data["items"] if make_item_key(saved) != key]
    changed = len(data["items"]) != before
    if changed:
        save_data(data)
    return changed


def remove_item_by_index(index):
    data = load_data()
    items = data.get("items", [])
    if index < 0 or index >= len(items):
        return None
    removed = items.pop(index)
    save_data(data)
    return removed


def move_item(index, direction):
    data = load_data()
    items = data.get("items", [])
    new_index = index + direction

    if index < 0 or index >= len(items):
        return False

    if new_index < 0 or new_index >= len(items):
        return False

    items[index], items[new_index] = items[new_index], items[index]
    save_data(data)
    return True


def export_to_path(filepath):
    data = load_data()
    Path(filepath).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def import_from_path(filepath):
    path = Path(filepath)
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Imported file is not a valid QuickFav Plus data file.")

    data.setdefault("version", 9)
    data.setdefault("items", [])
    data.setdefault("shortcut", DEFAULT_DATA["shortcut"].copy())

    if not isinstance(data["items"], list):
        raise ValueError("Imported file does not contain a valid items list.")

    save_data(data)
