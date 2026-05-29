from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class UpdaterServerRetryWithoutDpiWorker(QThread):
    loaded = pyqtSignal(int, bool, bool, str)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, *, runtime_feature, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._runtime_feature = runtime_feature

    def run(self) -> None:
        try:
            if not self._runtime_feature.is_any_running():
                self.loaded.emit(self._request_id, False, False, "")
                return
        except Exception as exc:
            log(f"Не удалось проверить состояние DPI перед повторной проверкой серверов: {exc}", "DEBUG")
            self.loaded.emit(self._request_id, False, False, str(exc))
            return

        try:
            log("⚠️ Серверы недоступны при запущенном DPI — делаем один повтор без DPI", "🔄 UPDATE")
            shutdown_result = self._runtime_feature.shutdown_sync(
                reason="server_status_probe_retry",
                include_cleanup=True,
            )
            if bool(getattr(shutdown_result, "still_running", False)):
                log("Повтор проверки серверов без DPI пропущен: DPI не остановился", "🔄 UPDATE")
                self.loaded.emit(self._request_id, False, False, "DPI не остановился")
                return
        except Exception as exc:
            log(f"Не удалось временно остановить DPI для проверки серверов: {exc}", "❌ ERROR")
            self.loaded.emit(self._request_id, False, False, str(exc))
            return

        self.loaded.emit(self._request_id, True, True, "")


class UpdaterDpiRestartWorker(QThread):
    loaded = pyqtSignal(int, bool)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, *, runtime_feature, context: str = "", parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._runtime_feature = runtime_feature
        self._context = str(context or "скачивания обновления")

    def run(self) -> None:
        try:
            if not self._runtime_feature.is_available():
                self.loaded.emit(self._request_id, False)
                return
            log(f"🔄 Перезапуск DPI после {self._context}", "🔁 UPDATE")
            restarted = bool(self._runtime_feature.restart())
        except Exception as exc:
            log(f"Не удалось перезапустить DPI: {exc}", "❌ ERROR")
            self.failed.emit(self._request_id, str(exc))
            return
        self.loaded.emit(self._request_id, restarted)


__all__ = ["UpdaterServerRetryWithoutDpiWorker", "UpdaterDpiRestartWorker"]
