from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication


class DpiSettingsAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_launch_method_labels_are_named_for_screen_reader(self) -> None:
        from settings.dpi.page import DpiSettingsPage

        page = DpiSettingsPage(
            dpi_settings_feature=SimpleNamespace(),
            orchestra_feature=SimpleNamespace(),
            runtime_actions=SimpleNamespace(handle_launch_method_changed=Mock()),
            set_status=Mock(),
            after_launch_method_changed=Mock(),
        )
        self.addCleanup(page.deleteLater)

        self.assertEqual(
            page._method_desc_label.property("screenReaderStateText"),
            "Описание выбора метода запуска: Выберите способ запуска обхода блокировок",
        )
        self.assertEqual(
            page.zapret2_header.property("screenReaderStateText"),
            "Раздел метода запуска: Zapret 2 (winws2.exe)",
        )
        self.assertEqual(
            page._zapret1_header.property("screenReaderStateText"),
            "Раздел метода запуска: Zapret 1 (winws.exe)",
        )

        page._ensure_orchestra_settings_built()

        self.assertEqual(
            page._orchestra_label.property("screenReaderStateText"),
            "Раздел метода запуска: Настройки оркестратора",
        )


if __name__ == "__main__":
    unittest.main()
