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


class RawPresetSaveWorker(QThread):
    saved = pyqtSignal(int, str, object, bool)
    failed = pyqtSignal(int, str)

    def __init__(
        self,
        request_id: int,
        controller,
        *,
        file_name: str,
        source_text: str,
        publish_content_changed: bool,
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self.controller = controller
        self._file_name = str(file_name or "").strip()
        self._source_text = str(source_text or "")
        self._publish_content_changed = bool(publish_content_changed)

    def run(self) -> None:
        try:
            result = self.controller.save_text(
                file_name=self._file_name,
                source_text=self._source_text,
                publish_content_changed=self._publish_content_changed,
            )
        except Exception as exc:
            log(f"RawPresetSaveWorker: не удалось сохранить preset: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.saved.emit(
            self._request_id,
            self._file_name,
            result,
            self._publish_content_changed,
        )


class RawPresetActionWorker(QThread):
    completed = pyqtSignal(int, str, object, object)
    failed = pyqtSignal(int, str, str, object)

    def __init__(
        self,
        request_id: int,
        controller,
        *,
        action: str,
        payload: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self.controller = controller
        self._action = str(action or "").strip()
        self._payload = dict(payload or {})

    def run(self) -> None:
        action = self._action
        payload = self._payload
        controller = self.controller
        try:
            if action == "open":
                result = controller.open_source_file(payload.get("path"))
            elif action == "rename":
                updated = controller.rename(
                    file_name=str(payload.get("file_name") or ""),
                    new_name=str(payload.get("new_name") or ""),
                )
                result = (updated, controller.source_path(updated.file_name))
            elif action == "duplicate":
                updated = controller.duplicate(
                    file_name=str(payload.get("file_name") or ""),
                    new_name=str(payload.get("new_name") or ""),
                )
                result = (updated, controller.source_path(updated.file_name))
            elif action == "export":
                target_path = str(payload.get("target_path") or "")
                controller.export(
                    file_name=str(payload.get("file_name") or ""),
                    target_path=target_path,
                )
                result = target_path
            elif action == "reset":
                updated = controller.reset_to_builtin(
                    file_name=str(payload.get("file_name") or ""),
                )
                result = (updated, controller.source_path(updated.file_name))
            elif action == "delete":
                result = controller.delete(
                    file_name=str(payload.get("file_name") or ""),
                )
            else:
                raise ValueError(f"Неизвестное действие preset: {action}")
        except Exception as exc:
            log(f"RawPresetActionWorker: действие {action} не выполнено: {exc}", "ERROR")
            self.failed.emit(self._request_id, action, str(exc), payload)
            return
        self.completed.emit(self._request_id, action, result, payload)


class RawPresetActivateWorker(QThread):
    activated = pyqtSignal(int, bool)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, controller, file_name: str, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self.controller = controller
        self._file_name = str(file_name or "").strip()

    def run(self) -> None:
        try:
            activated = bool(self.controller.activate(file_name=self._file_name))
        except Exception as exc:
            log(f"RawPresetActivateWorker: не удалось активировать preset: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.activated.emit(self._request_id, activated)
