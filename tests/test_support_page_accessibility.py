from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from ui.pages.support_page import SupportPage


class SupportPageAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_support_cards_have_screen_reader_text(self) -> None:
        page = SupportPage(
            create_open_action_worker=lambda *_args, **_kwargs: None,
        )

        self.assertEqual(page._support_card.accessibleName(), "Открыть GitHub Discussions")
        self.assertIn("Основной канал поддержки", page._support_card.accessibleDescription())
        self.assertEqual(page._support_card.button.accessibleName(), "Открыть GitHub Discussions")
        self.assertIn("Основной канал поддержки", page._support_card.button.accessibleDescription())
        self.assertEqual(page._tg_card.accessibleName(), "Открыть Telegram")
        self.assertIn("сообществом", page._tg_card.accessibleDescription())
        self.assertEqual(page._tg_card.button.accessibleName(), "Открыть Telegram")
        self.assertIn("сообществом", page._tg_card.button.accessibleDescription())
        self.assertEqual(page._dc_card.accessibleName(), "Открыть Discord")
        self.assertIn("живое общение", page._dc_card.accessibleDescription())
        self.assertEqual(page._dc_card.button.accessibleName(), "Открыть Discord")
        self.assertIn("живое общение", page._dc_card.button.accessibleDescription())

    def test_language_refresh_keeps_screen_reader_text(self) -> None:
        page = SupportPage(
            create_open_action_worker=lambda *_args, **_kwargs: None,
        )

        page.set_ui_language("ru")

        self.assertEqual(page._support_card.accessibleName(), "Открыть GitHub Discussions")
        self.assertIn("Основной канал поддержки", page._support_card.accessibleDescription())
        self.assertEqual(page._support_card.button.accessibleName(), "Открыть GitHub Discussions")
        self.assertIn("Основной канал поддержки", page._support_card.button.accessibleDescription())
        self.assertEqual(page._tg_card.accessibleName(), "Открыть Telegram")
        self.assertIn("сообществом", page._tg_card.accessibleDescription())
        self.assertEqual(page._tg_card.button.accessibleName(), "Открыть Telegram")
        self.assertIn("сообществом", page._tg_card.button.accessibleDescription())
        self.assertEqual(page._dc_card.accessibleName(), "Открыть Discord")
        self.assertIn("живое общение", page._dc_card.accessibleDescription())
        self.assertEqual(page._dc_card.button.accessibleName(), "Открыть Discord")
        self.assertIn("живое общение", page._dc_card.button.accessibleDescription())


if __name__ == "__main__":
    unittest.main()
