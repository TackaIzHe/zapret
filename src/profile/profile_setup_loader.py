from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class ProfileSetupLoadWorker(QThread):
    loaded = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, controller, profile_key: str, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._controller = controller
        self._profile_key = str(profile_key or "").strip()

    def run(self) -> None:
        try:
            payload = self._controller.load(self._profile_key)
        except Exception as exc:
            log(f"ProfileSetupLoadWorker: не удалось загрузить profile setup: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.loaded.emit(self._request_id, payload)
