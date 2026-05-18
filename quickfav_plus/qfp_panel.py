# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import qfp_submenus, qfp_storage, qfp_ui



def sync_saved_items_view(context):
    wm = context.window_manager
    items = qfp_storage.list_items()

    # Rebuild when the view count is stale. This keeps the sidebar from showing
    # an empty cached list after Blender restart or mode/context changes.
    if len(wm.qfp_saved_items_view) == len(items):
        return

    wm.qfp_saved_items_view.clear()

    for original_index, item in enumerate(items):
        row = wm.qfp_saved_items_view.add()
        row.item_id = item.get("operator") or item.get("menu_id") or item.get("label", "")
        row.label = qfp_ui.item_display_label(item)
        row.detail = item.get("type", "UNKNOWN")
        row.source_index = original_index

    if wm.qfp_saved_items_index >= len(wm.qfp_saved_items_view):
        wm.qfp_saved_items_index = max(0, len(wm.qfp_saved_items_view) - 1)


class QFP_UL_search_results(bpy.types.UIList):
    bl_idname = "QFP_UL_search_results"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.label)
        if item.detail and item.detail != item.label:
            row.label(text=item.detail)


class QFP_UL_saved_items(bpy.types.UIList):
    bl_idname = "QFP_UL_saved_items"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.detail == "SUBMENU":
            layout.label(text=item.label, icon="DOWNARROW_HLT")
        elif item.detail == "OPERATOR":
            layout.label(text=item.label, icon="PLAY")
        elif item.detail == "PROPERTY_TOGGLE":
            layout.label(text=item.label, icon="CHECKBOX_HLT")
        else:
            layout.label(text=item.label, icon="QUESTION")


class QFP_UL_conflicts(bpy.types.UIList):
    bl_idname = "QFP_UL_conflicts"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.label, icon="ERROR")


class QFP_MT_add_known_submenu_menu(bpy.types.Menu):
    bl_label = "Add Native Submenu"
    bl_idname = "QFP_MT_add_known_submenu_menu"

    def draw(self, context):
        layout = self.layout
        for label in qfp_submenus.get_known_submenu_labels():
            op = layout.operator("qfp.add_known_submenu", text=label)
            op.submenu_label = label


def draw_foldout(layout, data, prop_name, title, icon="TRIA_RIGHT"):
    value = getattr(data, prop_name)
    row = layout.row(align=True)
    row.prop(
        data,
        prop_name,
        text=title,
        icon="TRIA_DOWN" if value else "TRIA_RIGHT",
        emboss=False,
    )
    return value


class QFP_PT_sidebar_panel(bpy.types.Panel):
    bl_label = "QuickFav Plus"
    bl_idname = "QFP_PT_sidebar_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "QuickFav+"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        settings = wm.qfp_settings
        sync_saved_items_view(context)

        layout.operator("qfp.open_menu", text="Open QuickFav Plus", icon="MENU_PANEL")

        layout.separator()

        if draw_foldout(layout, settings, "show_shortcut_section", "Shortcut", "KEYINGSET"):
            box = layout.box()
            box.label(text="No default shortcut. Type key name: Q, F8, SPACE, ONE", icon="INFO")
            row = box.row(align=True)
            row.prop(settings, "shortcut_key", text="Key")
            row.prop(settings, "shortcut_ctrl")
            row.prop(settings, "shortcut_alt")
            row.prop(settings, "shortcut_shift")

            row = box.row(align=True)
            row.operator("qfp.check_shortcut_conflicts", text="Check")
            row.operator("qfp.apply_shortcut", text="Apply")
            row.operator("qfp.restore_default_shortcut", text="No Default")

            box.operator("qfp.clear_shortcut", text="Clear Shortcut")

            if wm.qfp_conflicts_view:
                box.label(text="Possible conflicts:", icon="ERROR")
                box.template_list(
                    "QFP_UL_conflicts",
                    "conflicts",
                    wm,
                    "qfp_conflicts_view",
                    wm,
                    "qfp_conflicts_index",
                    rows=3,
                )

        layout.separator()

        if draw_foldout(layout, settings, "show_menu_finder_section", "Menu ID Finder", "VIEWZOOM"):
            box = layout.box()
            box.prop(settings, "menu_search_query", text="Search")
            row = box.row(align=True)
            row.operator("qfp.refresh_menu_search", text="Find")
            row.operator("qfp.clear_menu_search_results", text="Clear")
            row.menu("QFP_MT_add_known_submenu_menu", text="Common")

            box.template_list(
                "QFP_UL_search_results",
                "menu_results",
                wm,
                "qfp_menu_results",
                wm,
                "qfp_menu_results_index",
                rows=5,
            )

            row = box.row(align=True)
            row.operator("qfp.use_selected_menu_id", text="Use")
            row.operator("qfp.add_selected_menu_id", text="Add")

            box.prop(settings, "custom_menu_label")
            box.prop(settings, "custom_menu_id")
            box.prop(settings, "restrict_custom_menu_to_current_context")
            box.operator("qfp.add_custom_menu_id", text="Add Custom Menu ID", icon="ADD")

        layout.separator()

        if draw_foldout(layout, settings, "show_operator_finder_section", "Operator ID Finder", "VIEWZOOM"):
            box = layout.box()
            box.prop(settings, "operator_search_query", text="Search")
            row = box.row(align=True)
            row.operator("qfp.refresh_operator_search", text="Find")
            row.operator("qfp.clear_operator_search_results", text="Clear")

            box.template_list(
                "QFP_UL_search_results",
                "operator_results",
                wm,
                "qfp_operator_results",
                wm,
                "qfp_operator_results_index",
                rows=5,
            )

            row = box.row(align=True)
            row.operator("qfp.use_selected_operator_id", text="Use")
            row.operator("qfp.add_selected_operator_id", text="Add")

            box.prop(settings, "custom_operator_label")
            box.prop(settings, "custom_operator_id")
            box.prop(settings, "restrict_custom_operator_to_current_context")
            box.operator("qfp.add_custom_operator_id", text="Add Custom Operator ID", icon="ADD")

        layout.separator()

        if draw_foldout(layout, settings, "show_saved_items_section", "Saved Items", "FILE_FOLDER"):
            box = layout.box()
            row = box.row(align=True)
            row.label(text=f"Saved Items: {len(wm.qfp_saved_items_view)}")
            row.operator("qfp.refresh_saved_items", text="", icon="FILE_REFRESH")

            box.template_list(
                "QFP_UL_saved_items",
                "saved_items",
                wm,
                "qfp_saved_items_view",
                wm,
                "qfp_saved_items_index",
                rows=8,
            )

            row = box.row(align=True)
            up = row.operator("qfp.move_selected_saved_item", text="", icon="TRIA_UP")
            up.direction = -1
            down = row.operator("qfp.move_selected_saved_item", text="", icon="TRIA_DOWN")
            down.direction = 1
            row.operator("qfp.remove_selected_saved_item", text="Remove", icon="X")

            io_row = box.row(align=True)
            io_row.operator("qfp.export_data", text="Export")
            io_row.operator("qfp.import_data", text="Import")


classes = (
    QFP_UL_search_results,
    QFP_UL_saved_items,
    QFP_UL_conflicts,
    QFP_MT_add_known_submenu_menu,
    QFP_PT_sidebar_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
