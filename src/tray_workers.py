from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from log.log import log


class TrayGithubApiRemovalToggleWorker(QThread):
    completed = pyqtSignal(bool, str)
    failed = pyqtSignal(str)

    def __init__(self, *, parent=None):
        super().__init__(parent)

    def run(self) -> None:
        import tray_commands

        messages: list[str] = []
        try:
            ok = bool(
                tray_commands.toggle_github_api_removal(
                    status_callback=lambda message: messages.append(str(message or "")),
                )
            )
        except Exception as exc:
            message = f"Ошибка при переключении удаления GitHub API: {exc}"
            log(message, "WARNING")
            self.failed.emit(message)
            return

        message = next((item for item in reversed(messages) if item), "")
        if not message:
            message = (
                "Удаление api.github.com из hosts переключено"
                if ok
                else "Ошибка при сохранении настройки удаления GitHub API"
            )
        self.completed.emit(ok, message)


__all__ = ["TrayGithubApiRemovalToggleWorker"]
