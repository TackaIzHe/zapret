from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, IndeterminateProgressBar, LineEdit, PushButton

from dns.ui.page_build import build_network_page_shell
from ui.fluent_widgets import SettingsCard


class DnsPageBuildContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_network_shell_transient_containers_are_parented_immediately(self) -> None:
        content_parent = QWidget()

        shell = build_network_page_shell(
            parent=content_parent,
            content_parent=content_parent,
            tr_fn=lambda _key, default: default,
            add_section_title_fn=lambda **_kwargs: None,
            body_label_cls=BodyLabel,
            settings_card_cls=SettingsCard,
            qvbox_layout_cls=QVBoxLayout,
            qhbox_layout_cls=QHBoxLayout,
            qframe_cls=QFrame,
            line_edit_cls=LineEdit,
            action_button_cls=PushButton,
            indeterminate_progress_bar_cls=IndeterminateProgressBar,
            setting_card_group_cls=SettingsCard,
            quick_actions_bar_cls=lambda: QWidget(),
            insert_widget_into_setting_card_group_fn=lambda *_args, **_kwargs: None,
            build_custom_dns_ui_fn=lambda **_kwargs: SimpleNamespace(
                card=SettingsCard(parent=content_parent),
                indicator=QFrame(content_parent),
                title_label=BodyLabel(""),
                primary_input=LineEdit(content_parent),
                secondary_input=LineEdit(content_parent),
                apply_button=PushButton("OK", content_parent),
            ),
            build_tools_card_ui_fn=lambda **_kwargs: SimpleNamespace(
                section_label=None,
                card=SettingsCard(parent=content_parent),
                actions_bar=QWidget(content_parent),
                test_button=PushButton("test", content_parent),
                flush_button=PushButton("flush", content_parent),
            ),
            on_apply_custom_dns=lambda: None,
            on_test_connection=lambda: None,
            on_flush_dns_cache=lambda: None,
            set_tooltip_fn=lambda *_args, **_kwargs: None,
            dns_provider_card_cls=SimpleNamespace(indicator_off=lambda: ""),
        )

        self.assertIs(shell.dns_cards_container.parent(), content_parent)
        self.assertIs(shell.adapters_container.parent(), content_parent)

    def test_network_page_places_custom_dns_inside_dns_choices_list(self) -> None:
        from dns.ui.page import NetworkPage

        dns_feature = SimpleNamespace(
            normalize_adapter_alias=lambda value: str(value),
            consume_warmed_page_data=lambda: None,
            create_page_load_worker=lambda request_id, parent=None: None,
        )

        page = NetworkPage(deps=SimpleNamespace(dns_feature=dns_feature))

        self.assertIs(page.custom_card.parent(), page.dns_cards_container)
        self.assertLess(
            page.dns_cards_layout.indexOf(page.custom_card),
            page.dns_cards_layout.count(),
        )


if __name__ == "__main__":
    unittest.main()
