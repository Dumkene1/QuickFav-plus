# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


class QFP_PG_search_result(bpy.types.PropertyGroup):
    item_id: bpy.props.StringProperty(default="")
    label: bpy.props.StringProperty(default="")
    detail: bpy.props.StringProperty(default="")
    source_index: bpy.props.IntProperty(default=-1)


class QFP_PG_settings(bpy.types.PropertyGroup):
    custom_menu_label: bpy.props.StringProperty(name="Display Name", default="")
    custom_menu_id: bpy.props.StringProperty(name="Menu ID", default="")
    custom_operator_label: bpy.props.StringProperty(name="Display Name", default="")
    custom_operator_id: bpy.props.StringProperty(name="Operator ID", default="")

    restrict_custom_menu_to_current_context: bpy.props.BoolProperty(name="Restrict to Current Context", default=True)
    restrict_custom_operator_to_current_context: bpy.props.BoolProperty(name="Restrict to Current Context", default=True)

    menu_search_query: bpy.props.StringProperty(name="Menu Search", default="")
    operator_search_query: bpy.props.StringProperty(name="Operator Search", default="")

    shortcut_key: bpy.props.StringProperty(
        name="Key",
        description="Blender keymap key name, for example Q, SPACE, F8, ONE, TWO, THREE",
        default="",
    )
    shortcut_ctrl: bpy.props.BoolProperty(name="Ctrl", default=False)
    shortcut_alt: bpy.props.BoolProperty(name="Alt", default=False)
    shortcut_shift: bpy.props.BoolProperty(name="Shift", default=False)


    show_shortcut_section: bpy.props.BoolProperty(
        name="Shortcut",
        default=True,
    )

    show_menu_finder_section: bpy.props.BoolProperty(
        name="Menu ID Finder",
        default=False,
    )

    show_operator_finder_section: bpy.props.BoolProperty(
        name="Operator ID Finder",
        default=False,
    )

    show_saved_items_section: bpy.props.BoolProperty(
        name="Saved Items",
        default=True,
    )


classes = (QFP_PG_search_result, QFP_PG_settings)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.qfp_settings = bpy.props.PointerProperty(type=QFP_PG_settings)

    bpy.types.WindowManager.qfp_menu_results = bpy.props.CollectionProperty(type=QFP_PG_search_result)
    bpy.types.WindowManager.qfp_menu_results_index = bpy.props.IntProperty(default=0)

    bpy.types.WindowManager.qfp_operator_results = bpy.props.CollectionProperty(type=QFP_PG_search_result)
    bpy.types.WindowManager.qfp_operator_results_index = bpy.props.IntProperty(default=0)

    bpy.types.WindowManager.qfp_saved_items_view = bpy.props.CollectionProperty(type=QFP_PG_search_result)
    bpy.types.WindowManager.qfp_saved_items_index = bpy.props.IntProperty(default=0)

    bpy.types.WindowManager.qfp_conflicts_view = bpy.props.CollectionProperty(type=QFP_PG_search_result)
    bpy.types.WindowManager.qfp_conflicts_index = bpy.props.IntProperty(default=0)


def unregister():
    for attr in (
        "qfp_settings",
        "qfp_menu_results", "qfp_menu_results_index",
        "qfp_operator_results", "qfp_operator_results_index",
        "qfp_saved_items_view", "qfp_saved_items_index",
        "qfp_conflicts_view", "qfp_conflicts_index",
    ):
        if hasattr(bpy.types.WindowManager, attr):
            delattr(bpy.types.WindowManager, attr)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
