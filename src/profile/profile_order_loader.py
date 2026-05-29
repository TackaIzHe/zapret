from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class ProfileOrderListLoadWorker(QThread):
    loaded = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, load_profiles, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._load_profiles = load_profiles

    def run(self) -> None:
        try:
            payload = self._load_profiles()
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
        move_before,
        move_after,
        move_to_end,
        *,
        action: str,
        source_profile_key: str,
        destination_profile_key: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._move_before = move_before
        self._move_after = move_after
        self._move_to_end = move_to_end
        self._action = str(action or "").strip()
        self._source_profile_key = str(source_profile_key or "").strip()
        self._destination_profile_key = str(destination_profile_key or "").strip()

    def run(self) -> None:
        try:
            if self._action == "before":
                result = self._move_before(
                    self._source_profile_key,
                    self._destination_profile_key,
                )
            elif self._action == "after":
                result = self._move_after(
                    self._source_profile_key,
                    self._destination_profile_key,
                )
            elif self._action == "end":
                result = self._move_to_end(
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
