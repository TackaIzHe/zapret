from __future__ import annotations

import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.state_store import AppUiState
from PyQt6.QtWidgets import QApplication


class _Label:
    def __init__(self, text: str = "") -> None:
        self._text = str(text)
        self.text_calls: list[str] = []

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:  # noqa: N802
        value = str(text)
        self.text_calls.append(value)
        self._text = value


class AutostartUiGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_strategy_summary_change_skips_mode_worker_reload(self) -> None:
        from autostart.ui.page import AutostartPage

        page = AutostartPage.__new__(AutostartPage)
        page._cleanup_in_progress = False
        page.strategy_name = "Old"
        page.current_strategy_label = _Label("Old")
        page._update_mode = Mock(
            side_effect=AssertionError("strategy summary change must not reload launch mode")
        )
        page.update_status = AutostartPage.update_status.__get__(page, AutostartPage)
        page._tr = Mock(side_effect=lambda _key, default, **_kwargs: default)
        page.status_label = _Label()
        page.status_desc = _Label()
        page.status_icon = Mock()
        page.disable_btn = Mock()
        page.gui_option = Mock()

        AutostartPage._on_ui_state_changed(
            page,
            AppUiState(autostart_enabled=False, current_strategy_summary="New"),
            frozenset({"current_strategy_summary"}),
        )

        page._update_mode.assert_not_called()
        self.assertEqual(page.current_strategy_label.text(), "New")

    def test_duplicate_status_update_skips_full_repaint_and_mode_reload(self) -> None:
        from autostart.ui.page import AutostartPage

        page = AutostartPage.__new__(AutostartPage)
        page.strategy_name = "Current"
        page._ui_language = "ru"
        page._tr = Mock(side_effect=lambda _key, default, **_kwargs: default)
        page.status_label = _Label()
        page.status_desc = _Label()
        page.current_strategy_label = _Label("Current")
        page.status_icon = Mock()
        page.disable_btn = Mock()
        page.gui_option = Mock()
        page._update_mode = Mock()

        AutostartPage.update_status(page, False, "Current")

        page.status_label.setText = Mock(side_effect=AssertionError("same status must not rewrite title"))
        page.status_desc.setText = Mock(side_effect=AssertionError("same status must not rewrite description"))
        page.current_strategy_label.setText = Mock(side_effect=AssertionError("same strategy must not rewrite label"))
        page.status_icon.setPixmap.side_effect = AssertionError("same status must not repaint icon")
        page.disable_btn.setVisible.side_effect = AssertionError("same status must not rewrite visibility")
        page.gui_option.set_disabled.side_effect = AssertionError("same status must not rewrite option state")
        page._update_mode.side_effect = AssertionError("same status must not reload launch mode")

        AutostartPage.update_status(page, False, "Current")

        page.status_label.setText.assert_not_called()
        page.status_desc.setText.assert_not_called()
        page.current_strategy_label.setText.assert_not_called()
        page.status_icon.setPixmap.assert_called_once()
        page.disable_btn.setVisible.assert_called_once()
        page.gui_option.set_disabled.assert_called_once()
        page._update_mode.assert_called_once()


if __name__ == "__main__":
    unittest.main()
