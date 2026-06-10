from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ui.queued_worker_state import QueuedWorkerState


@dataclass(slots=True)
class TelegramProxyPageWorkerState:
    """Состояние одного фонового действия страницы.

    Runtime запускает worker-а, то есть фоновую задачу. Этот объект хранит
    только две вещи вокруг запуска: есть ли отложенный запрос и запланирован
    ли запуск на следующий проход Qt-событий.
    """

    runtime: object
    pending: bool = False
    start_scheduled: bool = False

    def is_busy(self) -> bool:
        if self.start_scheduled:
            return True
        is_running = getattr(self.runtime, "is_running", None)
        if callable(is_running):
            return bool(is_running())
        return False

    def start_or_mark_pending(self, start: Callable[[], None]) -> bool:
        if self.is_busy():
            self.pending = True
            return False
        self.pending = False
        start()
        return True

    def schedule_next(self, single_shot: Callable[[int, Callable[[], None]], None], start: Callable[[], None]) -> None:
        if self.start_scheduled:
            self.pending = True
            return
        self.start_scheduled = True
        single_shot(0, lambda: self.run_scheduled(start))

    def schedule_start(self, single_shot: Callable[[int, Callable[[], None]], None], start: Callable[[], None]) -> None:
        self.pending = True
        self.schedule_next(single_shot, start)

    def run_scheduled(self, start: Callable[[], None], *, cleanup_in_progress: bool = False) -> None:
        self.start_scheduled = False
        pending = bool(self.pending)
        self.pending = False
        if cleanup_in_progress or not pending:
            return
        start()

    def schedule_after_finish(
        self,
        worker,
        *,
        is_current_worker_finish: Callable[[object, object], bool],
        schedule_next: Callable[[], None],
        cleanup_in_progress: bool = False,
    ) -> None:
        if not is_current_worker_finish(self.runtime, worker):
            return
        if self.pending and not cleanup_in_progress:
            schedule_next()

    def reset(self) -> None:
        self.pending = False
        self.start_scheduled = False


TelegramProxyPageQueuedWorkerState = QueuedWorkerState
