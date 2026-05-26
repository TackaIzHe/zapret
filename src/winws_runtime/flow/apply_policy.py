from __future__ import annotations

from pathlib import Path
from log.log import log
from settings.mode import is_preset_launch_method, normalize_launch_method
from profile.launch_validation import preset_has_enabled_profiles_for_launch


def _is_launch_running(runtime_feature) -> bool:
    try:
        launch_runtime = runtime_feature.objects.launch_runtime
        if launch_runtime is not None:
            return bool(launch_runtime.is_running())
    except Exception as e:
        log(f"Ошибка проверки состояния DPI: {e}", "DEBUG")
    return False


def _get_selected_presets_path(presets_feature, launch_method: str) -> Path | None:
    method = normalize_launch_method(launch_method, default="")
    if not is_preset_launch_method(method):
        return None
    try:
        snapshot = presets_feature.get_launch_snapshot(method, require_filters=False)
        return Path(snapshot.preset_path)
    except Exception:
        return None


def request_preset_runtime_content_apply(
    *,
    runtime_feature,
    launch_method: str,
    reason: str,
    profile_key: str | None = None,
) -> bool:
    """Apply runtime reaction for edits to the currently selected preset mode."""
    method = normalize_launch_method(launch_method, default="")
    if not is_preset_launch_method(method):
        log(f"Preset runtime apply skipped: unsupported method {method}", "DEBUG")
        return False

    launch_runtime = runtime_feature.objects.launch_runtime
    if launch_runtime is None:
        log("Preset runtime apply skipped: launch_runtime not found", "DEBUG")
        return False

    if not _is_launch_running(runtime_feature):
        log(f"Preset runtime apply skipped: DPI not running ({method})", "DEBUG")
        return False

    preset_path = _get_selected_presets_path(runtime_feature.dependencies.presets_feature, method)
    if preset_path is None or not preset_path.exists():
        log(f"Preset runtime apply: active preset missing for {method}, stopping DPI", "WARNING")
        launch_runtime.stop_dpi_async()
        return True

    try:
        content = preset_path.read_text(encoding="utf-8")
    except Exception as e:
        log(f"Preset runtime apply: failed to read preset for {method}: {e}", "ERROR")
        return False

    if not preset_has_enabled_profiles_for_launch(method, content):
        log(f"Preset runtime apply: preset has no enabled profiles for {method}, stopping DPI", "INFO")
        launch_runtime.stop_dpi_async()
        return True

    profile_info = f" [{profile_key}]" if profile_key else ""
    log(
        f"Preset runtime apply{profile_info} ({method}, reason={reason}) -> preset mode switch pipeline",
        "INFO",
    )
    launch_runtime.switch_presets_async(method)
    return True
