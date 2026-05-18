from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class StatusMessageContractTests(unittest.TestCase):
    def test_ui_state_store_remembers_last_status_message(self) -> None:
        from app.state_store import MainWindowStateStore

        store = MainWindowStateStore()
        changes: list[tuple[str, frozenset[str]]] = []
        store.subscribe(
            lambda state, fields: changes.append((state.last_status_message, fields)),
            fields={"last_status_message"},
        )

        self.assertTrue(store.set_last_status_message("Проверка обновлений..."))

        self.assertEqual(store.snapshot().last_status_message, "Проверка обновлений...")
        self.assertEqual(changes, [("Проверка обновлений...", frozenset({"last_status_message"}))])

    def test_window_set_status_sends_text_to_bound_status_message_sink(self) -> None:
        from main.window_actions import WindowActionsMixin

        class Window(WindowActionsMixin):
            pass

        window = Window()
        messages: list[str] = []
        window.bind_status_message_sink(messages.append)

        with patch("main.window_actions.log"):
            window.set_status("Блокировка MAX включена")

        self.assertEqual(messages, ["Блокировка MAX включена"])


if __name__ == "__main__":
    unittest.main()
