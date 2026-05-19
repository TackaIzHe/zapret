from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from qfluentwidgets import RoundMenu

from ui.presets_menu.common import fluent_icon, make_menu_action


@dataclass(frozen=True)
class ProfileContextMenuActions:
    open_profile: Callable[[str], object]
    set_enabled: Callable[[str, bool], object]
    duplicate_profile: Callable[[str], object]
    delete_from_preset: Callable[[str], object]
    edit_user_profile: Callable[[str], object]
    delete_user_profile: Callable[[str], object]


def show_profile_context_menu(
    *,
    parent,
    item,
    global_pos,
    actions: ProfileContextMenuActions,
) -> None:
    profile_key = str(getattr(item, "key", "") or "").strip()
    if not profile_key:
        return

    in_preset = bool(getattr(item, "in_preset", False))
    enabled = bool(getattr(item, "enabled", False))
    user_profile_id = str(getattr(item, "user_profile_id", "") or "").strip()
    is_user_profile = bool(user_profile_id or profile_key.startswith("template:user:"))

    menu = RoundMenu(parent=parent)

    open_action = make_menu_action("Открыть", icon=fluent_icon("VIEW"), parent=menu)
    open_action.triggered.connect(lambda: actions.open_profile(profile_key))
    menu.addAction(open_action)

    if in_preset:
        toggle_action = make_menu_action(
            "Выключить" if enabled else "Включить",
            icon=fluent_icon("CANCEL") if enabled else fluent_icon("ACCEPT"),
            parent=menu,
        )
        toggle_action.triggered.connect(lambda: actions.set_enabled(profile_key, not enabled))
        menu.addAction(toggle_action)

        duplicate_action = make_menu_action("Дублировать", icon=fluent_icon("COPY"), parent=menu)
        duplicate_action.triggered.connect(lambda: actions.duplicate_profile(profile_key))
        menu.addAction(duplicate_action)

        delete_action = make_menu_action("Удалить из preset", icon=fluent_icon("DELETE"), parent=menu)
        delete_action.triggered.connect(lambda: actions.delete_from_preset(profile_key))
        menu.addAction(delete_action)
    else:
        add_action = make_menu_action("Добавить в preset", icon=fluent_icon("ADD"), parent=menu)
        add_action.triggered.connect(lambda: actions.set_enabled(profile_key, True))
        menu.addAction(add_action)

    if is_user_profile:
        menu.addSeparator()
        edit_action = make_menu_action("Изменить пользовательский profile", icon=fluent_icon("EDIT"), parent=menu)
        edit_action.triggered.connect(lambda: actions.edit_user_profile(profile_key))
        menu.addAction(edit_action)

        delete_user_action = make_menu_action("Удалить пользовательский profile", icon=fluent_icon("DELETE"), parent=menu)
        delete_user_action.triggered.connect(lambda: actions.delete_user_profile(profile_key))
        menu.addAction(delete_user_action)

    menu.exec(global_pos)
