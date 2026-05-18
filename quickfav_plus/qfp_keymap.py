# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import qfp_storage


NUMBER_KEY_ALIASES = {
    "0": "ZERO",
    "1": "ONE",
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINE",
}


COMMON_KEY_ALIASES = {
    " ": "SPACE",
    "SPACEBAR": "SPACE",
    "ESC": "ESC",
    "ESCAPE": "ESC",
    "RETURN": "RET",
    "ENTER": "RET",
    "DELETE": "DEL",
    "BACKSPACE": "BACK_SPACE",
    "BACKSPACEKEY": "BACK_SPACE",
    "LEFTARROW": "LEFT_ARROW",
    "RIGHTARROW": "RIGHT_ARROW",
    "UPARROW": "UP_ARROW",
    "DOWNARROW": "DOWN_ARROW",
}


def normalize_key_name(key):
    key = (key or "").strip().upper()

    if key in NUMBER_KEY_ALIASES:
        return NUMBER_KEY_ALIASES[key]

    if key in COMMON_KEY_ALIASES:
        return COMMON_KEY_ALIASES[key]

    return key


def key_is_valid(key):
    if not key:
        return False

    try:
        # Test by adding/removing a temporary keymap item.
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc is None:
            return False

        km = kc.keymaps.new(name="Window", space_type="EMPTY")
        kmi = km.keymap_items.new("qfp.open_menu", type=key, value="PRESS")
        km.keymap_items.remove(kmi)
        kc.keymaps.remove(km)
        return True
    except Exception:
        return False


_addon_keymaps = []


def unregister_keymap():
    for km, kmi in _addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass

    _addon_keymaps.clear()


def register_keymap(key="", ctrl=False, alt=False, shift=False):
    unregister_keymap()

    key = normalize_key_name(key)

    if not key:
        return False

    if not key_is_valid(key):
        return False

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc is None:
        return False

    km = kc.keymaps.new(name="Window", space_type="EMPTY")
    kmi = km.keymap_items.new(
        "qfp.open_menu",
        type=key,
        value="PRESS",
        ctrl=ctrl,
        alt=alt,
        shift=shift,
    )

    _addon_keymaps.append((km, kmi))
    return True



def register_saved_keymap():
    shortcut = qfp_storage.get_shortcut()
    key = normalize_key_name(shortcut.get("key", ""))

    if not key:
        unregister_keymap()
        return

    register_keymap(
        key=key,
        ctrl=shortcut.get("ctrl", False),
        alt=shortcut.get("alt", False),
        shift=shortcut.get("shift", False),
    )

def save_and_apply_shortcut(key, ctrl=False, alt=False, shift=False):
    key = normalize_key_name(key)
    qfp_storage.save_shortcut(key, ctrl=ctrl, alt=alt, shift=shift)
    register_keymap(key=key, ctrl=ctrl, alt=alt, shift=shift)



def restore_default_shortcut():
    clear_shortcut()

def clear_shortcut():
    unregister_keymap()
    qfp_storage.save_shortcut("", ctrl=False, alt=False, shift=False)


def find_conflicts(key, ctrl=False, alt=False, shift=False):
    key = normalize_key_name(key)
    conflicts = []
    wm = bpy.context.window_manager

    for kc in (wm.keyconfigs.user, wm.keyconfigs.addon, wm.keyconfigs.default):
        if kc is None:
            continue

        for km in kc.keymaps:
            for kmi in km.keymap_items:
                if kmi.idname == "qfp.open_menu":
                    continue

                if (
                    kmi.type == key
                    and kmi.value == "PRESS"
                    and bool(kmi.ctrl) == bool(ctrl)
                    and bool(kmi.alt) == bool(alt)
                    and bool(kmi.shift) == bool(shift)
                ):
                    conflicts.append({
                        "keymap": km.name,
                        "operator": kmi.idname,
                        "name": getattr(kmi, "name", "") or kmi.idname,
                    })

    return conflicts


def register():
    pass


def unregister():
    unregister_keymap()
