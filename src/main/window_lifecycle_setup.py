from __future__ import annotations

import time as _time

from config.window_metrics import HEIGHT, MIN_HEIGHT, MIN_WIDTH, WIDTH
from main.application_lifecycle import ApplicationLifecycle
from main.application_lifecycle_port import build_application_lifecycle_window_port
from main.runtime_state import log_startup_metric as emit_startup_metric
from ui.window_close_flow import WindowCloseFlow
from ui.window_geometry_runtime import WindowGeometryRuntime


def attach_window_lifecycle(window, features) -> None:
    window.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
    window.window_geometry_runtime = WindowGeometryRuntime(
        window,
        min_width=MIN_WIDTH,
        min_height=MIN_HEIGHT,
        default_width=WIDTH,
        default_height=HEIGHT,
        close_state=window.close_state,
        create_geometry_save_worker=features.window_geometry.create_geometry_save_worker,
    )
    window.application_lifecycle = ApplicationLifecycle(
        window_port=build_application_lifecycle_window_port(window),
        close_state=window.close_state,
        runtime_feature=features.runtime,
        premium_feature=features.premium,
        telegram_proxy_feature=features.telegram_proxy,
        tray_feature=features.tray,
    )
    window.window_close_flow = WindowCloseFlow(
        parent=window,
        close_state=window.close_state,
        get_launch_state_snapshot=features.runtime.snapshot,
        close_to_tray=window.close_to_tray,
        exit_stop_dpi=window.exit_stop_dpi,
        exit_keep_dpi=window.exit_keep_dpi,
        tray_close_mode=features.program_settings.tray_close_mode,
    )


def restore_window_geometry(window) -> None:
    t_geometry = _time.perf_counter()
    window.window_geometry_runtime.restore_geometry()
    emit_startup_metric(
        "StartupWindowInitRestoreGeometry",
        f"{(_time.perf_counter() - t_geometry) * 1000:.0f}ms",
    )


__all__ = ["attach_window_lifecycle", "restore_window_geometry"]
