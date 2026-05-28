from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class BlockcheckInitialStateWorker(QThread):
    completed = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(self, request_id: int, *, parent=None):
        super().__init__(parent)
        self._request_id = int(request_id)

    def run(self) -> None:
        try:
            from blockcheck.page_runtime import load_page_initial_state

            result = load_page_initial_state()
        except Exception as exc:
            log(f"BlockcheckInitialStateWorker: не удалось загрузить начальное состояние: {exc}", "WARNING")
            self.failed.emit(self._request_id, str(exc))
            return
        self.completed.emit(self._request_id, result)


class BlockcheckSupportPrepareWorker(QThread):
    completed = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)

    def __init__(
        self,
        request_id: int,
        *,
        run_log_file: str | None,
        mode_label: str,
        extra_domains: list[str],
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = int(request_id)
        self._run_log_file = run_log_file
        self._mode_label = str(mode_label or "BlockCheck")
        self._extra_domains = list(extra_domains or [])

    def run(self) -> None:
        try:
            from blockcheck.page_runtime import prepare_support

            result = prepare_support(
                run_log_file=self._run_log_file,
                mode_label=self._mode_label,
                extra_domains=self._extra_domains,
            )
        except Exception as exc:
            log(f"BlockcheckSupportPrepareWorker: не удалось подготовить обращение: {exc}", "WARNING")
            self.failed.emit(self._request_id, str(exc))
            return
        self.completed.emit(self._request_id, result)
