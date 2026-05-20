from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class ListsEditorTextLoadWorker(QThread):
    loaded = pyqtSignal(int, str, object)
    failed = pyqtSignal(int, str, str)

    def __init__(self, request_id: int, controller, kind: str, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._controller = controller
        self._kind = str(kind or "").strip()

    def run(self) -> None:
        try:
            state = self._controller.load_text(self._kind)
        except Exception as exc:
            log(f"ListsEditorTextLoadWorker: не удалось загрузить list {self._kind}: {exc}", "ERROR")
            self.failed.emit(self._request_id, self._kind, str(exc))
            return
        self.loaded.emit(self._request_id, self._kind, state)
