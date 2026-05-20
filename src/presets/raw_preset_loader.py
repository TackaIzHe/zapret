from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class RawPresetLoadWorker(QThread):
    loaded = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, controller, path: Path | None, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._controller = controller
        self._path = path

    def run(self) -> None:
        try:
            result = self._controller.load_text(self._path)
        except Exception as exc:
            log(f"RawPresetLoadWorker: не удалось прочитать preset: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.loaded.emit(self._request_id, result)
