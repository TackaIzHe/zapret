from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QListWidget
from qfluentwidgets import ScrollBar

from ui.widgets.fluent_scrollbar import FluentScrollBars, install_fluent_scrollbars


class FluentScrollbarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_install_fluent_scrollbars_uses_qfluent_scrollbar(self) -> None:
        widget = QListWidget()

        bars = install_fluent_scrollbars(widget, vertical=True, horizontal=False)

        self.assertIsInstance(bars, FluentScrollBars)
        self.assertIsInstance(bars.vertical, ScrollBar)
        self.assertIsNone(bars.horizontal)
        self.assertIs(getattr(widget, "_zapret_fluent_scrollbars"), bars)
        self.assertEqual(widget.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def test_install_fluent_scrollbars_is_idempotent(self) -> None:
        widget = QListWidget()

        first = install_fluent_scrollbars(widget, vertical=True, horizontal=False)
        second = install_fluent_scrollbars(widget, vertical=True, horizontal=False)

        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
