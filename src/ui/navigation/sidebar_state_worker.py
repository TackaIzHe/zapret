from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal


class SidebarExpandedStateSaveWorker(QThread):
    saved = pyqtSignal(bool)
    failed = pyqtSignal(str)

    def __init__(self, *, expanded: bool, state_key: str, parent=None):
        super().__init__(parent)
        self._expanded = bool(expanded)
        self._state_key = str(state_key or "sidebar_expanded")

    def run(self) -> None:
        try:
            from settings.store import set_ui_state_settings

            set_ui_state_settings({self._state_key: self._expanded})
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.saved.emit(self._expanded)


def create_sidebar_expanded_save_worker(*, expanded: bool, state_key: str, parent=None) -> SidebarExpandedStateSaveWorker:
    return SidebarExpandedStateSaveWorker(expanded=expanded, state_key=state_key, parent=parent)


__all__ = ["SidebarExpandedStateSaveWorker", "create_sidebar_expanded_save_worker"]
