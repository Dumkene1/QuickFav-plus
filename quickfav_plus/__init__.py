# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "QuickFav Plus",
    "author": "QuickFav Plus Maintainer",
    "version": (1, 16, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > QuickFav+",
    "description": "Organized user-managed favorites menu for Blender commands.",
    "category": "Interface",
}

from . import qfp_storage
from . import qfp_ui
from . import qfp_context
from . import qfp_submenus
from . import qfp_capture
from . import qfp_properties
from . import qfp_keymap
from . import qfp_operators
from . import qfp_panel
from . import qfp_context_menu

MODULES = (
    qfp_storage,
    qfp_ui,
    qfp_context,
    qfp_submenus,
    qfp_capture,
    qfp_properties,
    qfp_keymap,
    qfp_operators,
    qfp_panel,
    qfp_context_menu,
)


def register():
    for module in MODULES:
        if hasattr(module, "register"):
            module.register()

    qfp_keymap.register_saved_keymap()


def unregister():
    qfp_keymap.unregister_keymap()

    for module in reversed(MODULES):
        if module is qfp_keymap:
            continue
        if hasattr(module, "unregister"):
            module.unregister()
