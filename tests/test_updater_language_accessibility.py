from __future__ import annotations

import unittest

from config.build_info import APP_VERSION, CHANNEL
from updater.ui.language import apply_servers_page_language


class _TextTarget:
    def __init__(self, text: str = ""):
        self.text = text
        self._accessible_name = ""
        self.properties = {}

    def setText(self, text):  # noqa: N802
        self.text = text

    def setAccessibleName(self, value):  # noqa: N802
        self._accessible_name = value

    def accessibleName(self):  # noqa: N802
        return self._accessible_name

    def setProperty(self, name, value):  # noqa: N802
        self.properties[name] = value

    def property(self, name):
        return self.properties.get(name)


class _Card:
    titleLabel = None

    def __init__(self):
        self.title = ""
        self.content = ""

    def set_title(self, text):
        self.title = text

    def setContent(self, text):  # noqa: N802
        self.content = text


class _Stateful:
    def __init__(self):
        self.language = ""
        self.texts = ()

    def set_ui_language(self, language):
        self.language = language

    def set_texts(self, *texts):
        self.texts = texts


class _Breadcrumb:
    def __init__(self):
        self.items = []

    def blockSignals(self, _blocked):  # noqa: N802
        pass

    def clear(self):
        self.items.clear()

    def addItem(self, key, text):  # noqa: N802
        self.items.append((key, text))


class _Table:
    def setHorizontalHeaderLabels(self, labels):  # noqa: N802
        self.labels = labels


class UpdaterLanguageAccessibilityTests(unittest.TestCase):
    def test_language_refresh_updates_version_screen_reader_state(self) -> None:
        version_info_label = _TextTarget("old")

        apply_servers_page_language(
            tr_fn=lambda _key, default, **_kwargs: default,
            ui_language="ru",
            update_card=_Stateful(),
            changelog_card=_Stateful(),
            breadcrumb=_Breadcrumb(),
            page_title_label=_TextTarget(),
            servers_title_label=_TextTarget(),
            legend_active_label=_TextTarget(),
            servers_table=_Table(),
            settings_card=_Card(),
            toggle_label=None,
            auto_check_card=_Stateful(),
            version_info_label=version_info_label,
            telegram_card=_Card(),
            telegram_info_label=None,
            telegram_button=_TextTarget(),
            refresh_server_rows=lambda: None,
        )

        expected = f"Версия ZapretGUI: v{APP_VERSION} · {CHANNEL}"

        self.assertEqual(version_info_label.accessibleName(), expected)
        self.assertEqual(
            version_info_label.property("screenReaderStateText"),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
