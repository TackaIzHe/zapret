from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class ProfileOrderListLoadWorker(QThread):
    loaded = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, profile_service, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._service = profile_service

    def run(self) -> None:
        try:
            payload = self._service.list_preset_order_profiles()
        except Exception as exc:
            log(f"ProfileOrderListLoadWorker: не удалось прочитать порядок profile-ов: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.loaded.emit(self._request_id, payload)


class ProfilePresetOrderMoveWorker(QThread):
    moved = pyqtSignal(int, str, str, str, object)
    failed = pyqtSignal(int, str)

    def __init__(
        self,
        request_id: int,
        profile_service,
        *,
        action: str,
        source_profile_key: str,
        destination_profile_key: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._service = profile_service
        self._action = str(action or "").strip()
        self._source_profile_key = str(source_profile_key or "").strip()
        self._destination_profile_key = str(destination_profile_key or "").strip()

    def run(self) -> None:
        try:
            if self._action == "before":
                result = self._service.move_preset_profile_before(
                    self._source_profile_key,
                    self._destination_profile_key,
                )
            elif self._action == "after":
                result = self._service.move_preset_profile_after(
                    self._source_profile_key,
                    self._destination_profile_key,
                )
            elif self._action == "end":
                result = self._service.move_preset_profile_to_end(
                    self._source_profile_key,
                )
            else:
                raise ValueError(f"Неизвестное перемещение profile: {self._action}")
        except Exception as exc:
            log(f"ProfilePresetOrderMoveWorker: не удалось переместить profile: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.moved.emit(
            self._request_id,
            self._action,
            self._source_profile_key,
            self._destination_profile_key,
            result,
        )


__all__ = ["ProfileOrderListLoadWorker", "ProfilePresetOrderMoveWorker"]
