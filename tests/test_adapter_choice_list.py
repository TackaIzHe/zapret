from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from dns.ui.adapters import build_adapter_cards, refresh_adapter_cards


class AdapterChoiceListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_adapter_list_uses_delegate_rows_and_keeps_checkbox_contract(self) -> None:
        from dns.ui.adapter_list import AdapterChoiceListWidget
        from dns.ui.cards import AdapterCard

        changed: list[int] = []
        view = AdapterChoiceListWidget()

        cards = build_adapter_cards(
            adapters=[("Ethernet", "Intel")],
            dns_info={"Ethernet": {"ipv4": ["8.8.8.8"], "ipv6": []}},
            adapter_card_cls=AdapterCard,
            adapters_layout=view,
            normalize_alias_fn=lambda value: value,
            on_state_changed=changed.append,
        )

        self.assertEqual(len(cards), 1)
        self.assertEqual(len(view.findChildren(AdapterCard)), 0)
        self.assertEqual(cards[0].adapter_name, "Ethernet")
        self.assertTrue(cards[0].checkbox.isChecked())
        self.assertEqual(
            cards[0].property("screenReaderStateText"),
            "Сетевой адаптер Ethernet, выбран, DNS v4 8.8.8.8",
        )
        self.assertGreaterEqual(view.sizeHintForRow(0), 38)
        self.assertLessEqual(view.sizeHintForRow(0), 40)

        view.activate_item(cards[0].item)

        self.assertFalse(cards[0].checkbox.isChecked())
        self.assertEqual(changed, [0])
        self.assertEqual(
            cards[0].property("screenReaderStateText"),
            "Сетевой адаптер Ethernet, не выбран, DNS v4 8.8.8.8",
        )

    def test_adapter_list_updates_dns_text_and_toggles_from_keyboard(self) -> None:
        from dns.ui.adapter_list import AdapterChoiceListWidget
        from dns.ui.cards import AdapterCard

        view = AdapterChoiceListWidget()
        cards = build_adapter_cards(
            adapters=[("Ethernet", "Intel")],
            dns_info={"Ethernet": {"ipv4": [], "ipv6": []}},
            adapter_card_cls=AdapterCard,
            adapters_layout=view,
            normalize_alias_fn=lambda value: value,
            on_state_changed=lambda _state: None,
        )

        refresh_adapter_cards(
            adapter_cards=cards,
            dns_info={"Ethernet": {"ipv4": ["1.1.1.1"], "ipv6": []}},
            build_refresh_plan_fn=lambda names, info: _RefreshPlan(names, info),
        )

        self.assertEqual(cards[0].dns_label.text(), "v4 1.1.1.1")

        view.setCurrentItem(cards[0].item)
        event = QKeyEvent(QEvent.Type.KeyPress, int(Qt.Key.Key_Space), Qt.KeyboardModifier.NoModifier)
        view.keyPressEvent(event)

        self.assertTrue(event.isAccepted())
        self.assertFalse(cards[0].checkbox.isChecked())


class _RefreshPlan:
    def __init__(self, names, info):
        self.entries = [
            _RefreshEntry(
                adapter_name=name,
                adapter_data=info[name],
                ipv4=info[name].get("ipv4", []),
                ipv6=info[name].get("ipv6", []),
            )
            for name in names
        ]


class _RefreshEntry:
    def __init__(self, *, adapter_name, adapter_data, ipv4, ipv6):
        self.adapter_name = adapter_name
        self.adapter_data = adapter_data
        self.ipv4 = ipv4
        self.ipv6 = ipv6


if __name__ == "__main__":
    unittest.main()
