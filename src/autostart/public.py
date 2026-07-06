from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Callable


@dataclass(frozen=True, slots=True)
class GuiAutostartResult:
    success: bool
    removed_count: int = 0
    restart_requested: bool = False
    message: str = ""


def get_current_launch_method() -> str:
    from settings.dpi.public import get_launch_method

    return str(get_launch_method() or "").strip()


def save_gui_autostart_enabled(enabled: bool) -> bool:
    from settings.store import set_gui_autostart_enabled

    return bool(set_gui_autostart_enabled(bool(enabled)))


def disable_gui_autostart() -> GuiAutostartResult:
    from autostart.scheduled_task_api import delete_autostart_task
    from autostart.startup_shortcut_api import delete_startup_shortcut

    removed_count = 0
    if delete_autostart_task():
        removed_count += 1
    if delete_startup_shortcut():
        removed_count += 1
    return GuiAutostartResult(success=True, removed_count=removed_count)


def enable_gui_autostart(*, status_cb: Callable[[str], None] | None = None) -> GuiAutostartResult:
    from autostart.scheduled_task_api import create_or_update_autostart_task
    from autostart.startup_shortcut_api import delete_startup_shortcut

    def _status(message: str) -> None:
        if status_cb is not None:
            status_cb(message)

    try:
        _status("Удаление старого ярлыка автозапуска...")
        delete_startup_shortcut()
        _status("Создание задачи автозапуска в Планировщике Windows...")
        ok = bool(create_or_update_autostart_task(sys.executable))
    except Exception:
        ok = False
    if ok:
        _status("Автозапуск программы включён")
        return GuiAutostartResult(success=True)
    return GuiAutostartResult(
        success=False,
        message=(
            "Не удалось включить автозапуск. Windows не дал создать задачу "
            "в Планировщике заданий."
        ),
    )


def ensure_gui_autostart_migrated() -> bool:
    """Чинит автозапуск, включённый старой версией через ярлык автозагрузки.

    Ярлык молча игнорируется Windows для программ с requireAdministrator при
    включённом UAC, поэтому при включённой настройке автозапуска задача
    планировщика создаётся заново, а устаревший ярлык удаляется. Заодно
    задача перерегистрируется, если exe переехал.
    """
    try:
        from settings.store import get_gui_autostart_enabled

        if not get_gui_autostart_enabled():
            return False

        from autostart.scheduled_task_api import (
            create_or_update_autostart_task,
            get_autostart_task_action,
        )
        from autostart.startup_shortcut_api import (
            delete_startup_shortcut,
            get_startup_shortcut_path,
        )

        exe_path = sys.executable
        action = get_autostart_task_action()
        task_ok = action is not None and action[0] == exe_path
        shortcut_exists = get_startup_shortcut_path().exists()
        if task_ok and not shortcut_exists:
            return False

        if not task_ok and not create_or_update_autostart_task(exe_path):
            return False
        delete_startup_shortcut()
        return True
    except Exception as exc:
        try:
            from log.log import log

            log(f"GUI autostart migration failed: {exc}", "WARNING")
        except Exception:
            pass
        return False


__all__ = [
    "GuiAutostartResult",
    "disable_gui_autostart",
    "enable_gui_autostart",
    "ensure_gui_autostart_migrated",
    "get_current_launch_method",
    "save_gui_autostart_enabled",
]
