from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon, PushSettingCard

from presets.ui.control.shared_builders import build_push_setting_card_common


class ControlPushSettingCardIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_fluent_icon_is_converted_for_push_setting_card_button(self) -> None:
        card = build_push_setting_card_common(
            push_setting_card_cls=PushSettingCard,
            button_text="Открыть",
            icon=QIcon(),
            title_text="Проверка",
            content_text="",
            on_click=lambda: None,
            button_icon_name=FluentIcon.LINK,
        )

        self.assertFalse(card.button.icon().isNull())


if __name__ == "__main__":
    unittest.main()
