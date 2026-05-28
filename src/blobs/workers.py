from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class BlobsLoadWorker(QThread):
    loaded = pyqtSignal(int, dict, bool)
    failed = pyqtSignal(int, str, bool)

    def __init__(self, request_id: int, blobs_feature, *, reload: bool = False, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._blobs = blobs_feature
        self._reload = bool(reload)

    def run(self) -> None:
        try:
            if self._reload:
                blobs_info = self._blobs.reload_blobs()
            else:
                blobs_info = self._blobs.get_blobs_info()
        except Exception as exc:
            log(f"BlobsLoadWorker: не удалось загрузить blobs: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc), self._reload)
            return
        self.loaded.emit(self._request_id, dict(blobs_info or {}), self._reload)


class BlobActionWorker(QThread):
    completed = pyqtSignal(int, str, bool, object)
    failed = pyqtSignal(int, str, str, object)

    def __init__(
        self,
        request_id: int,
        blobs_feature,
        *,
        action: str,
        name: str = "",
        blob_type: str = "",
        value: str = "",
        description: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._blobs = blobs_feature
        self._action = str(action or "").strip()
        self._name = str(name or "").strip()
        self._blob_type = str(blob_type or "").strip()
        self._value = str(value or "")
        self._description = str(description or "")

    def run(self) -> None:
        context = {
            "name": self._name,
            "type": self._blob_type,
            "value": self._value,
            "description": self._description,
        }
        try:
            if self._action == "save":
                result = bool(
                    self._blobs.save_user_blob(
                        self._name,
                        self._blob_type,
                        self._value,
                        self._description,
                    )
                )
            elif self._action == "delete":
                result = bool(self._blobs.delete_user_blob(self._name))
            else:
                raise ValueError(f"Неизвестное действие blob: {self._action}")
        except Exception as exc:
            log(f"BlobActionWorker: действие {self._action} не выполнено: {exc}", "ERROR")
            self.failed.emit(self._request_id, self._action, str(exc), context)
            return
        self.completed.emit(self._request_id, self._action, result, context)


__all__ = ["BlobActionWorker", "BlobsLoadWorker"]
