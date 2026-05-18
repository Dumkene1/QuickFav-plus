# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .qfp_capture import capture_button_item
from .qfp_storage import contains_item


def draw_qfp_button_context_menu(self, context):
    item = capture_button_item(context)

    if not item:
        return

    layout = self.layout
    layout.separator()

    if item.get("type") == "PROPERTY_UNSUPPORTED":
        layout.label(text="QuickFav Plus: unsupported property type", icon="INFO")
        return

    if contains_item(item):
        layout.operator("qfp.remove_button_from_favorites", text="Remove from QuickFav Plus", icon="REMOVE")
    else:
        layout.operator("qfp.add_button_to_favorites", text="Add to QuickFav Plus", icon="ADD")


def register():
    bpy.types.UI_MT_button_context_menu.append(draw_qfp_button_context_menu)


def unregister():
    try:
        bpy.types.UI_MT_button_context_menu.remove(draw_qfp_button_context_menu)
    except Exception:
        pass
