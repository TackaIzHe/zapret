from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon, PushButton, SettingCardGroup

from ui.fluent_widgets import QuickActionsBar, insert_widget_into_setting_card_group


class QuickActionsBarLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_setting_card_group_height_keeps_quick_action_buttons_visible(self) -> None:
        group = SettingCardGroup("Действия")
        actions = QuickActionsBar()
        actions.add_buttons(
            [
                PushButton("Открыть файл", icon=FluentIcon.LINK),
                PushButton("Сбросить файл", icon=FluentIcon.RETURN),
                PushButton("Очистить всё", icon=FluentIcon.DELETE),
            ]
        )

        insert_widget_into_setting_card_group(group, 1, actions)

        needed_height = group.vBoxLayout.minimumSize().height()
        self.assertGreaterEqual(group.minimumHeight(), needed_height)
        self.assertGreaterEqual(group.maximumHeight(), needed_height)
        self.assertGreaterEqual(actions.sizeHint().height(), actions.actions_layout.minimumSize().height())


if __name__ == "__main__":
    unittest.main()
