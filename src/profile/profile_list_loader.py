from __future__ import annotations

import time

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class ProfileListLoadResult:
    def __init__(self, *, payload, view_state=None) -> None:
        self.payload = payload
        self.view_state = view_state


class ProfileListLoadWorker(QThread):
    loaded = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, load_profiles, build_view_state=None, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._load_profiles = load_profiles
        self._build_view_state = build_view_state

    def run(self) -> None:
        started_at = time.perf_counter()
        try:
            payload = self._load_profiles()
        except Exception as exc:
            log(f"ProfileListLoadWorker: не удалось загрузить profile payload: {exc}", "ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        view_state = None
        if callable(self._build_view_state):
            try:
                view_state = self._build_view_state(tuple(getattr(payload, "items", ()) or ()))
            except Exception as exc:
                log(f"ProfileListLoadWorker: не удалось подготовить view state profile: {exc}", "ERROR")
                self.failed.emit(self._request_id, str(exc))
                return
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        log(f"profile_feature.worker.list_profiles.total: {elapsed_ms:.1f}ms", "DEBUG")
        self.loaded.emit(self._request_id, ProfileListLoadResult(payload=payload, view_state=view_state))
