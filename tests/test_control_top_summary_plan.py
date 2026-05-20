from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class ControlTopSummaryPlanTests(unittest.TestCase):
    _app = None

    def test_profiles_value_is_translated(self) -> None:
        from presets.ui.control.top_summary_plan import build_profiles_value

        self.assertEqual(build_profiles_value(2, language="ru"), "2 включено")
        self.assertEqual(build_profiles_value(2, language="en"), "2 enabled")

    def test_profiles_value_handles_missing_count(self) -> None:
        from presets.ui.control.top_summary_plan import build_profiles_value

        self.assertEqual(build_profiles_value(None, language="ru"), "Не удалось проверить")
        self.assertEqual(build_profiles_value(None, language="en"), "Could not check")

    def test_premium_summary_keeps_free_and_premium_labels_as_is(self) -> None:
        from presets.ui.control.top_summary_plan import build_premium_summary

        self.assertEqual(build_premium_summary(False, None, language="ru"), ("Free", "Базовые функции"))
        self.assertEqual(build_premium_summary(True, 12, language="ru"), ("Premium", "Осталось 12 дней"))
        self.assertEqual(build_premium_summary(True, 12, language="en"), ("Premium", "12 days left"))

    def test_top_summary_items_have_accent_icons(self) -> None:
        with patch.dict("os.environ", {"QT_QPA_PLATFORM": "offscreen"}):
            from PyQt6.QtWidgets import QApplication
            from presets.ui.control.top_summary_widget import ControlTopSummaryWidget

            self.__class__._app = QApplication.instance() or QApplication([])
            widget = ControlTopSummaryWidget(language="ru", mode_value="Zapret 2")

            for item in (
                widget.preset_item,
                widget.profiles_item,
                widget.mode_item,
                widget.premium_item,
            ):
                self.assertIsNotNone(getattr(item, "_icon_label", None))
                self.assertFalse(item._icon_label.pixmap().isNull())


if __name__ == "__main__":
    unittest.main()
