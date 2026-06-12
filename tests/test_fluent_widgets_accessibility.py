from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication


class FluentWidgetsAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_settings_card_title_has_screen_reader_state(self) -> None:
        from ui.fluent_widgets import SettingsCard

        card = SettingsCard("DNS Серверы")
        self.addCleanup(card.deleteLater)

        self.assertEqual(card.property("screenReaderStateText"), "Раздел настроек: DNS Серверы")
        self.assertEqual(card.accessibleName(), "Раздел настроек: DNS Серверы")
        self.assertEqual(card._title_label.property("screenReaderStateText"), "Раздел настроек: DNS Серверы")

    def test_settings_card_set_title_updates_screen_reader_state(self) -> None:
        from ui.fluent_widgets import SettingsCard

        card = SettingsCard()
        self.addCleanup(card.deleteLater)

        card.set_title("Диагностика")

        self.assertEqual(card.property("screenReaderStateText"), "Раздел настроек: Диагностика")
        self.assertEqual(card.accessibleName(), "Раздел настроек: Диагностика")
        self.assertEqual(card._title_label.property("screenReaderStateText"), "Раздел настроек: Диагностика")

        card.set_title("Инструменты")

        self.assertEqual(card.property("screenReaderStateText"), "Раздел настроек: Инструменты")
        self.assertEqual(card._title_label.property("screenReaderStateText"), "Раздел настроек: Инструменты")


if __name__ == "__main__":
    unittest.main()
