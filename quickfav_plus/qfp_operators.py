# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import qfp_storage, qfp_submenus, qfp_ui, qfp_keymap
from .qfp_capture import (
    capture_button_item,
    resolve_context_path,
    resolve_operator,
    find_operator_ids,
    make_operator_item,
)


def draw_quickfav_popup(menu_self, context):
    layout = menu_self.layout
    items = qfp_storage.list_items()
    visible_count = 0
    current_group = None

    from .qfp_capture import is_item_available

    for index, item in enumerate(items):
        if not is_item_available(context, item):
            continue

        context_filter = item.get("context_filter", {})
        group = "All Contexts" if context_filter.get("show_everywhere") else (
            f'{context_filter.get("object_mode", "Any")} / {context_filter.get("area_type", "Any")}'
        )

        if group != current_group:
            if visible_count > 0:
                layout.separator()
            layout.label(text=group)
            current_group = group

        label = item.get("label") or item.get("operator") or item.get("menu_id") or "Unnamed"

        if item.get("type") == "SUBMENU":
            menu_id = item.get("menu_id", "")
            if hasattr(bpy.types, menu_id):
                layout.menu(menu_id, text=label)
                visible_count += 1
            continue

        op = layout.operator("qfp.run_item", text=label)
        op.item_index = index
        visible_count += 1

    if not items:
        layout.label(text="No QuickFav Plus items yet", icon="INFO")
    elif visible_count == 0:
        layout.label(text="No items available in this context", icon="INFO")


def refresh_saved_items_view(context):
    wm = context.window_manager
    wm.qfp_saved_items_view.clear()

    for original_index, item in enumerate(qfp_storage.list_items()):
        row = wm.qfp_saved_items_view.add()
        row.item_id = item.get("operator") or item.get("menu_id") or item.get("label", "")
        row.label = qfp_ui.item_display_label(item)
        row.detail = item.get("type", "UNKNOWN")
        row.source_index = original_index

    if wm.qfp_saved_items_index >= len(wm.qfp_saved_items_view):
        wm.qfp_saved_items_index = max(0, len(wm.qfp_saved_items_view) - 1)


def refresh_conflicts_view(context):
    wm = context.window_manager
    settings = wm.qfp_settings
    wm.qfp_conflicts_view.clear()

    if not settings.shortcut_key:
        return

    conflicts = qfp_keymap.find_conflicts(
        settings.shortcut_key,
        ctrl=settings.shortcut_ctrl,
        alt=settings.shortcut_alt,
        shift=settings.shortcut_shift,
    )

    for conflict in conflicts:
        row = wm.qfp_conflicts_view.add()
        row.item_id = conflict["operator"]
        row.label = f'{conflict["keymap"]}: {conflict["operator"]}'
        row.detail = conflict.get("name", "")
        row.source_index = -1


class QFP_OT_open_menu(bpy.types.Operator):
    bl_idname = "qfp.open_menu"
    bl_label = "Open QuickFav Plus Menu"

    def execute(self, context):
        # Safer than bpy.ops.wm.call_menu for non-Object modes.
        context.window_manager.popup_menu(draw_quickfav_popup, title="QuickFav Plus")
        return {"FINISHED"}


class QFP_OT_apply_shortcut(bpy.types.Operator):
    bl_idname = "qfp.apply_shortcut"
    bl_label = "Apply Shortcut"

    def execute(self, context):
        settings = context.window_manager.qfp_settings
        normalized_key = qfp_keymap.normalize_key_name(settings.shortcut_key)

        if not qfp_keymap.key_is_valid(normalized_key):
            self.report({"ERROR"}, f"Invalid Blender key name: {settings.shortcut_key}")
            return {"CANCELLED"}

        settings.shortcut_key = normalized_key

        qfp_keymap.save_and_apply_shortcut(
            normalized_key,
            ctrl=settings.shortcut_ctrl,
            alt=settings.shortcut_alt,
            shift=settings.shortcut_shift,
        )
        settings = context.window_manager.qfp_settings
        settings.shortcut_key = qfp_keymap.normalize_key_name(settings.shortcut_key)
        refresh_conflicts_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_check_shortcut_conflicts(bpy.types.Operator):
    bl_idname = "qfp.check_shortcut_conflicts"
    bl_label = "Check Conflicts"

    def execute(self, context):
        refresh_conflicts_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_restore_default_shortcut(bpy.types.Operator):
    bl_idname = "qfp.restore_default_shortcut"
    bl_label = "Restore Default Shortcut"

    def execute(self, context):
        settings = context.window_manager.qfp_settings
        settings.shortcut_key = ""
        settings.shortcut_ctrl = False
        settings.shortcut_alt = False
        settings.shortcut_shift = False

        qfp_keymap.restore_default_shortcut()
        refresh_conflicts_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_clear_shortcut(bpy.types.Operator):
    bl_idname = "qfp.clear_shortcut"
    bl_label = "Clear Shortcut"

    def execute(self, context):
        qfp_keymap.clear_shortcut()
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_add_button_to_favorites(bpy.types.Operator):
    bl_idname = "qfp.add_button_to_favorites"
    bl_label = "Add to QuickFav Plus"

    def execute(self, context):
        item = capture_button_item(context)

        if not item:
            self.report({"WARNING"}, "QuickFav Plus could not capture this UI item.")
            return {"CANCELLED"}

        if item.get("type") == "PROPERTY_UNSUPPORTED":
            self.report({"WARNING"}, "This property type is not supported yet.")
            return {"CANCELLED"}

        qfp_storage.add_item(item)
        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_remove_button_from_favorites(bpy.types.Operator):
    bl_idname = "qfp.remove_button_from_favorites"
    bl_label = "Remove from QuickFav Plus"

    def execute(self, context):
        item = capture_button_item(context)

        if not item:
            return {"CANCELLED"}

        qfp_storage.remove_item(item)
        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_run_item(bpy.types.Operator):
    bl_idname = "qfp.run_item"
    bl_label = "Run QuickFav Plus Item"

    item_index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        items = qfp_storage.list_items()

        if self.item_index < 0 or self.item_index >= len(items):
            return {"CANCELLED"}

        item = items[self.item_index]

        if item.get("type") == "SUBMENU":
            menu_id = item.get("menu_id", "")

            if not hasattr(bpy.types, menu_id):
                self.report({"ERROR"}, f"Menu not found: {menu_id}")
                return {"CANCELLED"}

            # Native menu call only happens after the user selects it.
            bpy.ops.wm.call_menu(name=menu_id)
            return {"FINISHED"}

        if item.get("type") == "PROPERTY_TOGGLE":
            target = resolve_context_path(context, item.get("context_path", ""))
            prop_id = item.get("property_identifier", "")

            if target is None or not hasattr(target, prop_id):
                self.report({"ERROR"}, "Property target not found in this context.")
                return {"CANCELLED"}

            try:
                current_value = bool(getattr(target, prop_id))
                setattr(target, prop_id, not current_value)
                return {"FINISHED"}
            except Exception as exc:
                self.report({"ERROR"}, f"Could not toggle property: {exc}")
                return {"CANCELLED"}

        if item.get("type") == "OPERATOR":
            op = resolve_operator(item.get("operator", ""))

            if op is None:
                return {"CANCELLED"}

            if hasattr(op, "poll") and not op.poll():
                self.report({"WARNING"}, "Not available in this exact context.")
                return {"CANCELLED"}

            props = item.get("properties", {}) or {}
            op(**props) if props else op()
            return {"FINISHED"}

        return {"CANCELLED"}


class QFP_OT_refresh_saved_items(bpy.types.Operator):
    bl_idname = "qfp.refresh_saved_items"
    bl_label = "Refresh Saved Items"

    def execute(self, context):
        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_remove_selected_saved_item(bpy.types.Operator):
    bl_idname = "qfp.remove_selected_saved_item"
    bl_label = "Remove"

    def execute(self, context):
        wm = context.window_manager

        if not wm.qfp_saved_items_view:
            return {"CANCELLED"}

        view_row = wm.qfp_saved_items_view[wm.qfp_saved_items_index]
        removed = qfp_storage.remove_item_by_index(view_row.source_index)

        if removed is None:
            self.report({"ERROR"}, "Could not remove selected item.")
            return {"CANCELLED"}

        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_move_selected_saved_item(bpy.types.Operator):
    bl_idname = "qfp.move_selected_saved_item"
    bl_label = "Move Selected"

    direction: bpy.props.IntProperty(default=0)

    def execute(self, context):
        wm = context.window_manager

        if not wm.qfp_saved_items_view:
            return {"CANCELLED"}

        view_row = wm.qfp_saved_items_view[wm.qfp_saved_items_index]
        moved = qfp_storage.move_item(view_row.source_index, self.direction)

        if not moved:
            return {"CANCELLED"}

        new_source_index = view_row.source_index + self.direction
        refresh_saved_items_view(context)

        for index, row in enumerate(wm.qfp_saved_items_view):
            if row.source_index == new_source_index:
                wm.qfp_saved_items_index = index
                break

        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_add_known_submenu(bpy.types.Operator):
    bl_idname = "qfp.add_known_submenu"
    bl_label = "Add Known Submenu"

    submenu_label: bpy.props.StringProperty(default="")

    def execute(self, context):
        entry = qfp_submenus.get_known_submenu_by_label(self.submenu_label)

        if not entry:
            return {"CANCELLED"}

        settings = context.window_manager.qfp_settings
        item = qfp_submenus.make_submenu_item(
            entry,
            context,
            restrict=settings.restrict_custom_menu_to_current_context,
        )

        qfp_storage.add_item(item)
        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_add_custom_menu_id(bpy.types.Operator):
    bl_idname = "qfp.add_custom_menu_id"
    bl_label = "Add Custom Menu ID"

    def execute(self, context):
        settings = context.window_manager.qfp_settings
        menu_id = settings.custom_menu_id.strip()
        label = settings.custom_menu_label.strip() or menu_id

        if not menu_id or not hasattr(bpy.types, menu_id):
            self.report({"ERROR"}, f"Menu ID not found: {menu_id}")
            return {"CANCELLED"}

        item = qfp_submenus.make_custom_submenu_item(
            label,
            menu_id,
            context,
            settings.restrict_custom_menu_to_current_context,
        )

        qfp_storage.add_item(item)
        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_refresh_menu_search(bpy.types.Operator):
    bl_idname = "qfp.refresh_menu_search"
    bl_label = "Find Menu IDs"

    def execute(self, context):
        wm = context.window_manager
        settings = wm.qfp_settings
        wm.qfp_menu_results.clear()

        for menu_id, label in qfp_submenus.find_menu_ids(settings.menu_search_query, limit=220):
            row = wm.qfp_menu_results.add()
            row.item_id = menu_id
            row.label = menu_id
            row.detail = label

        return {"FINISHED"}


class QFP_OT_use_selected_menu_id(bpy.types.Operator):
    bl_idname = "qfp.use_selected_menu_id"
    bl_label = "Use Selected Menu ID"

    def execute(self, context):
        wm = context.window_manager

        if not wm.qfp_menu_results:
            return {"CANCELLED"}

        row = wm.qfp_menu_results[wm.qfp_menu_results_index]
        settings = wm.qfp_settings
        settings.custom_menu_id = row.item_id
        settings.custom_menu_label = row.detail or row.item_id.replace("_MT_", " ").replace("_", " ").title()
        return {"FINISHED"}


class QFP_OT_add_selected_menu_id(bpy.types.Operator):
    bl_idname = "qfp.add_selected_menu_id"
    bl_label = "Add Selected Menu ID"

    def execute(self, context):
        bpy.ops.qfp.use_selected_menu_id()
        result = bpy.ops.qfp.add_custom_menu_id()
        context.window_manager.qfp_menu_results.clear()
        context.window_manager.qfp_menu_results_index = 0
        qfp_ui.tag_redraw_all()
        return result


class QFP_OT_refresh_operator_search(bpy.types.Operator):
    bl_idname = "qfp.refresh_operator_search"
    bl_label = "Find Operator IDs"

    def execute(self, context):
        wm = context.window_manager
        settings = wm.qfp_settings
        wm.qfp_operator_results.clear()

        for operator_id, label in find_operator_ids(settings.operator_search_query, limit=260):
            row = wm.qfp_operator_results.add()
            row.item_id = operator_id
            row.label = operator_id
            row.detail = label

        return {"FINISHED"}


class QFP_OT_use_selected_operator_id(bpy.types.Operator):
    bl_idname = "qfp.use_selected_operator_id"
    bl_label = "Use Selected Operator ID"

    def execute(self, context):
        wm = context.window_manager

        if not wm.qfp_operator_results:
            return {"CANCELLED"}

        row = wm.qfp_operator_results[wm.qfp_operator_results_index]
        settings = wm.qfp_settings
        settings.custom_operator_id = row.item_id
        settings.custom_operator_label = row.detail or row.item_id
        return {"FINISHED"}


class QFP_OT_add_custom_operator_id(bpy.types.Operator):
    bl_idname = "qfp.add_custom_operator_id"
    bl_label = "Add Custom Operator ID"

    def execute(self, context):
        settings = context.window_manager.qfp_settings
        operator_id = settings.custom_operator_id.strip()
        label = settings.custom_operator_label.strip()

        if not operator_id or resolve_operator(operator_id) is None:
            self.report({"ERROR"}, f"Operator ID not found: {operator_id}")
            return {"CANCELLED"}

        item = make_operator_item(
            operator_id,
            context,
            label,
            settings.restrict_custom_operator_to_current_context,
        )

        qfp_storage.add_item(item)
        refresh_saved_items_view(context)
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_add_selected_operator_id(bpy.types.Operator):
    bl_idname = "qfp.add_selected_operator_id"
    bl_label = "Add Selected Operator ID"

    def execute(self, context):
        bpy.ops.qfp.use_selected_operator_id()
        result = bpy.ops.qfp.add_custom_operator_id()
        context.window_manager.qfp_operator_results.clear()
        context.window_manager.qfp_operator_results_index = 0
        qfp_ui.tag_redraw_all()
        return result


class QFP_OT_export_data(bpy.types.Operator, ExportHelper):
    bl_idname = "qfp.export_data"
    bl_label = "Export QuickFav Plus List"
    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        qfp_storage.export_to_path(self.filepath)
        self.report({"INFO"}, "QuickFav Plus list exported.")
        return {"FINISHED"}


class QFP_OT_import_data(bpy.types.Operator, ImportHelper):
    bl_idname = "qfp.import_data"
    bl_label = "Import QuickFav Plus List"
    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        try:
            qfp_storage.import_from_path(self.filepath)
        except Exception as exc:
            self.report({"ERROR"}, f"Import failed: {exc}")
            return {"CANCELLED"}

        refresh_saved_items_view(context)
        qfp_keymap.register_saved_keymap()
        qfp_ui.tag_redraw_all()
        self.report({"INFO"}, "QuickFav Plus list imported.")
        return {"FINISHED"}



class QFP_OT_clear_menu_search_results(bpy.types.Operator):
    bl_idname = "qfp.clear_menu_search_results"
    bl_label = "Clear Menu Search"

    def execute(self, context):
        wm = context.window_manager
        wm.qfp_menu_results.clear()
        wm.qfp_menu_results_index = 0
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


class QFP_OT_clear_operator_search_results(bpy.types.Operator):
    bl_idname = "qfp.clear_operator_search_results"
    bl_label = "Clear Operator Search"

    def execute(self, context):
        wm = context.window_manager
        wm.qfp_operator_results.clear()
        wm.qfp_operator_results_index = 0
        qfp_ui.tag_redraw_all()
        return {"FINISHED"}


classes = (
    QFP_OT_open_menu,
    QFP_OT_apply_shortcut,
    QFP_OT_check_shortcut_conflicts,
    QFP_OT_restore_default_shortcut,
    QFP_OT_clear_shortcut,
    QFP_OT_add_button_to_favorites,
    QFP_OT_remove_button_from_favorites,
    QFP_OT_run_item,
    QFP_OT_refresh_saved_items,
    QFP_OT_remove_selected_saved_item,
    QFP_OT_move_selected_saved_item,
    QFP_OT_add_known_submenu,
    QFP_OT_add_custom_menu_id,
    QFP_OT_refresh_menu_search,
    QFP_OT_clear_menu_search_results,
    QFP_OT_use_selected_menu_id,
    QFP_OT_add_selected_menu_id,
    QFP_OT_refresh_operator_search,
    QFP_OT_clear_operator_search_results,
    QFP_OT_use_selected_operator_id,
    QFP_OT_add_custom_operator_id,
    QFP_OT_add_selected_operator_id,
    QFP_OT_export_data,
    QFP_OT_import_data,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    try:
        shortcut = qfp_storage.get_shortcut()
        settings = bpy.context.window_manager.qfp_settings
        if shortcut.get("key"):
            settings.shortcut_key = shortcut.get("key", "")
        settings.shortcut_ctrl = shortcut.get("ctrl", False)
        settings.shortcut_alt = shortcut.get("alt", False)
        settings.shortcut_shift = shortcut.get("shift", False)

        refresh_saved_items_view(bpy.context)
    except Exception:
        pass


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
