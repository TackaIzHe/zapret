from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from main.window_page_presenters import (
    apply_profile_setup_change_for_method,
    open_preset_raw_editor_for_method,
    open_profile_setup_for_method,
)
from ui.navigation.text_sync import on_ui_language_changed
from ui.window_appearance_state import (
    on_animations_changed,
    on_background_preset_changed,
    on_background_refresh_needed,
    on_editor_smooth_scroll_changed,
    on_mica_changed,
    on_smooth_scroll_changed,
)
from ui.workflows.mode import (
    apply_launch_method_changed_ui,
    show_active_mode_control_page,
)
from ui.window_adapter import show_page


@dataclass(frozen=True, slots=True)
class WindowPageActions:
    set_status: Callable[..., Any]
    notify: Callable[..., Any]
    request_exit: Callable[..., Any]
    open_connection_test: Callable[..., Any]
    open_folder: Callable[..., Any]
    show_page: Callable[..., Any]
    show_active_mode_control_page: Callable[..., Any]
    open_profile_setup: Callable[..., Any]
    on_profile_setup_changed: Callable[..., Any]
    open_preset_raw_editor: Callable[..., Any]
    after_launch_method_changed: Callable[..., Any]
    set_garland_enabled: Callable[..., Any]
    set_snowflakes_enabled: Callable[..., Any]
    on_background_refresh_needed: Callable[..., Any]
    on_background_preset_changed: Callable[..., Any]
    on_opacity_changed: Callable[..., Any]
    on_mica_changed: Callable[..., Any]
    on_animations_changed: Callable[..., Any]
    on_smooth_scroll_changed: Callable[..., Any]
    on_editor_smooth_scroll_changed: Callable[..., Any]
    on_ui_language_changed: Callable[..., Any]


def build_window_page_actions(*, window, appearance_actions) -> WindowPageActions:
    return WindowPageActions(
        set_status=window.set_status,
        notify=window.window_notification_center.notify,
        request_exit=window.request_exit,
        open_connection_test=window.open_connection_test,
        open_folder=window.open_folder,
        show_page=lambda page_name, *, allow_internal=False: show_page(
            window,
            page_name,
            allow_internal=allow_internal,
        ),
        show_active_mode_control_page=lambda *, allow_internal=False: show_active_mode_control_page(
            window,
            allow_internal=allow_internal,
        ),
        open_profile_setup=lambda method, profile_key: open_profile_setup_for_method(
            window,
            method,
            profile_key,
            allow_internal=True,
        ),
        on_profile_setup_changed=lambda method, profile_key, change_kind: apply_profile_setup_change_for_method(
            window,
            method,
            profile_key,
            change_kind,
        ),
        open_preset_raw_editor=lambda method, preset_name, *, allow_internal=True: open_preset_raw_editor_for_method(
            window,
            method,
            preset_name,
            allow_internal=allow_internal,
        ),
        after_launch_method_changed=lambda method: apply_launch_method_changed_ui(window, method),
        set_garland_enabled=appearance_actions.set_garland_enabled,
        set_snowflakes_enabled=appearance_actions.set_snowflakes_enabled,
        on_background_refresh_needed=lambda: on_background_refresh_needed(window),
        on_background_preset_changed=lambda preset: on_background_preset_changed(window, preset),
        on_opacity_changed=appearance_actions.set_window_opacity,
        on_mica_changed=lambda enabled: on_mica_changed(window, enabled),
        on_animations_changed=lambda enabled: on_animations_changed(window, enabled),
        on_smooth_scroll_changed=lambda enabled: on_smooth_scroll_changed(window, enabled),
        on_editor_smooth_scroll_changed=lambda enabled: on_editor_smooth_scroll_changed(window, enabled),
        on_ui_language_changed=lambda language: on_ui_language_changed(window, language),
    )


__all__ = ["WindowPageActions", "build_window_page_actions"]
