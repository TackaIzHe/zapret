from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from profile.ui.profile_list_model import ProfileListModel
from profile.ui.profile_list_view import ProfileListView


class ProfileListViewAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_current_row_updates_screen_reader_state_text(self) -> None:
        model = ProfileListModel()
        model._rows = [
            {
                "kind": "profile",
                "display_name": "YouTube",
                "enabled": True,
                "in_preset": True,
                "strategy_name": "TLS fake",
            },
            {
                "kind": "group",
                "group_name": "Видео",
                "count": 2,
                "collapsed": False,
            },
        ]
        view = ProfileListView()
        self.addCleanup(view.deleteLater)
        view.set_screen_reader_list_name("Список профилей")
        view.setModel(model)

        view.setCurrentIndex(model.index(0, 0))

        self.assertEqual(
            view.property("screenReaderStateText"),
            "Список профилей: YouTube, включён, есть в preset, стратегия: TLS fake. "
            "Нажмите Enter, чтобы открыть profile.",
        )

        view.setCurrentIndex(model.index(1, 0))

        self.assertEqual(
            view.property("screenReaderStateText"),
            "Список профилей: Группа Видео, 2 профиля, развернута. "
            "Нажмите Enter, чтобы свернуть или развернуть группу.",
        )

    def test_empty_current_row_keeps_list_name_for_screen_reader(self) -> None:
        view = ProfileListView()
        self.addCleanup(view.deleteLater)
        view.set_screen_reader_list_name("Порядок profile")

        self.assertEqual(view.property("screenReaderStateText"), "Порядок profile")


if __name__ == "__main__":
    unittest.main()
