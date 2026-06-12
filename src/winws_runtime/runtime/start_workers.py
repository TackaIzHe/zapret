from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

from winws_runtime.health.process_health_check import diagnose_startup_error
from winws_runtime.runtime.preset_launch_service import (
    STARTUP_AUTOSTART_STABLE_WINDOW_SECONDS,
    PresetLaunchService,
    ensure_required_files_fast,
)


@dataclass(frozen=True)
class PreparedDpiStartRequest:
    launch_method: str
    selected_mode: object
    mode_name: str
    method_name: str


class PresetLaunchStartWorker(QObject):
    """Qt-worker запуска: выполняет PresetLaunchService вне UI-потока."""

    finished = pyqtSignal(bool, str)  # success, error_message
    progress = pyqtSignal(str)        # status_message

    def __init__(
        self,
        selected_mode,
        launch_method,
        *,
        runtime_feature,
        runtime_api,
        startup_autostart: bool = False,
    ):
        super().__init__()
        self.selected_mode = selected_mode
        self.launch_method = launch_method
        self._runtime_feature = runtime_feature
        self.launch_runtime_api = runtime_api
        self._last_error_message: str = ""
        self._startup_autostart = bool(startup_autostart)

    def _build_launch_service(self) -> PresetLaunchService:
        return PresetLaunchService(
            selected_mode=self.selected_mode,
            launch_method=self.launch_method,
            runtime_feature=self._runtime_feature,
            runtime_api=self.launch_runtime_api,
            startup_autostart=self._startup_autostart,
            progress_callback=self.progress.emit,
        )

    def run(self):
        try:
            result = self._build_launch_service().run()
            self.selected_mode = result.selected_mode
            self._last_error_message = str(result.error_message or "").strip()
            self.finished.emit(bool(result.success), "" if result.success else self._last_error_message)
        except Exception as e:
            exe_path = getattr(self.launch_runtime_api, "expected_exe_path", "")
            diagnosis = diagnose_startup_error(e, exe_path)
            self._last_error_message = diagnosis.split("\n")[0]
            self.finished.emit(False, self._last_error_message)
