from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class AutostartActionWorker(QThread):
    completed = pyqtSignal(int, str, object, object)
    failed = pyqtSignal(int, str, str, object)
    status = pyqtSignal(int, str, str)

    def __init__(
        self,
        request_id: int,
        *,
        action: str,
        enable_gui_autostart,
        disable_gui_autostart,
        save_gui_autostart_enabled,
        enabled: bool | None = None,
        strategy_name: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._action = str(action or "").strip()
        self._enable_gui_autostart = enable_gui_autostart
        self._disable_gui_autostart = disable_gui_autostart
        self._save_gui_autostart_enabled = save_gui_autostart_enabled
        self._enabled = None if enabled is None else bool(enabled)
        self._strategy_name = strategy_name

    def run(self) -> None:
        context = {
            "enabled": self._enabled,
            "strategy_name": self._strategy_name,
        }

        def emit_status(message: str) -> None:
            self.status.emit(self._request_id, self._action, str(message or ""))

        try:
            if self._action == "enable":
                result = self._enable_gui_autostart(status_cb=emit_status)
                if getattr(result, "success", False):
                    self._save_gui_autostart_enabled(True)
            elif self._action == "disable":
                result = self._disable_gui_autostart()
                if getattr(result, "success", False):
                    self._save_gui_autostart_enabled(False)
            elif self._action == "save_state":
                result = self._save_gui_autostart_enabled(bool(self._enabled))
            else:
                raise ValueError(f"Неизвестное действие автозапуска: {self._action}")
        except Exception as exc:
            log(f"AutostartActionWorker: не удалось выполнить {self._action}: {exc}", "WARNING")
            self.failed.emit(self._request_id, self._action, str(exc), context)
            return
        self.completed.emit(self._request_id, self._action, result, context)


class AutostartModeLoadWorker(QThread):
    loaded = pyqtSignal(int, str)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, *, get_current_launch_method, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._get_current_launch_method = get_current_launch_method

    def run(self) -> None:
        try:
            method = str(self._get_current_launch_method() or "").strip()
        except Exception as exc:
            log(f"AutostartModeLoadWorker: не удалось загрузить режим запуска: {exc}", "WARNING")
            self.failed.emit(self._request_id, str(exc))
            return
        self.loaded.emit(self._request_id, method)
