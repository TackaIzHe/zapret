from __future__ import annotations

from log.log import log

from ui.page_actions import request_blockcheck_diagnostics_focus
from ui.window_adapter import route_window_search_result, show_page
from utils.subproc import run_hidden


class WindowActionsMixin:
    def bind_status_message_sink(self, sink) -> None:
        self._status_message_sink = sink if callable(sink) else None

    def set_status(self, text: str) -> None:
        """Пишет пользовательский статус в лог.

        Текст также уходит в узкий status-message sink, если он подключён
        при сборке приложения. Само окно не получает доступ к общему store.
        """
        normalized_text = str(text or "")
        level = "INFO"
        lower_text = normalized_text.lower()
        if "работает" in lower_text or "запущен" in lower_text or "успешно" in lower_text:
            level = "INFO"
        elif "останов" in lower_text or "ошибка" in lower_text or "выключен" in lower_text:
            level = "WARNING"
        elif "внимание" in lower_text or "предупреждение" in lower_text:
            level = "WARNING"
        log(normalized_text, level)

        sink = getattr(self, "_status_message_sink", None)
        if callable(sink):
            try:
                sink(normalized_text)
            except Exception:
                pass

    def open_folder(self) -> None:
        """Opens the DPI folder."""
        try:
            run_hidden("explorer.exe .", shell=True)
        except Exception as e:
            self.set_status(f"Ошибка при открытии папки: {str(e)}")

    def open_connection_test(self) -> None:
        """Переключает на вкладку диагностики соединений."""
        try:
            if show_page(self, PageName.BLOCKCHECK):
                route_window_search_result(self, PageName.BLOCKCHECK, "diagnostics")
                request_blockcheck_diagnostics_focus(self)
                log("Открыта вкладка диагностики в BlockCheck", "INFO")
        except Exception as e:
            log(f"Ошибка при открытии вкладки тестирования: {e}", "❌ ERROR")
            self.set_status(f"Ошибка: {e}")
