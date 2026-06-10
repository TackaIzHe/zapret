from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from updater.ui.changelog_card import ChangelogCard


class UpdaterChangelogAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_update_card_has_screen_reader_state_and_button_text(self) -> None:
        card = ChangelogCard(language="ru")

        card.show_update("9.9.9", "Исправлена работа обновлений")

        self.assertEqual(card.accessibleName(), "Доступно обновление: версия 9.9.9")
        self.assertEqual(card.property("screenReaderStateText"), "Доступно обновление: версия 9.9.9")
        self.assertIn("список изменений", card.accessibleDescription().lower())
        self.assertEqual(card.close_btn.accessibleName(), "Закрыть уведомление об обновлении")
        self.assertIn("скрывает", card.close_btn.accessibleDescription().lower())
        self.assertEqual(card.later_btn.accessibleName(), "Отложить обновление")
        self.assertIn("позже", card.later_btn.accessibleDescription().lower())
        self.assertEqual(card.install_btn.accessibleName(), "Установить обновление 9.9.9")
        self.assertEqual(card.install_btn.property("screenReaderStateText"), "Установить обновление 9.9.9")
        self.assertIn("установку", card.install_btn.accessibleDescription().lower())


if __name__ == "__main__":
    unittest.main()
