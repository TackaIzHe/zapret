from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPixmap
from qfluentwidgets import BodyLabel, CaptionLabel, CheckBox, ComboBox, RadioButton, SegmentedWidget, Slider

from ui.fluent_widgets import SettingsCard
from ui.pages.appearance_page_lower_build import build_holiday_sections, build_opacity_section
from ui.pages.appearance_page_top_build import (
    build_background_section,
    build_display_mode_section,
    build_language_section,
    update_sidebar_icon_style_accessibility,
)


class AppearanceAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_display_mode_selector_reads_current_mode(self) -> None:
        widgets = build_display_mode_section(
            page=None,
            tr_language="ru",
            add_section_title=lambda **_kwargs: BodyLabel("Режим отображения"),
            content_parent=QWidget(),
            settings_card_cls=SettingsCard,
            caption_label_cls=CaptionLabel,
            segmented_widget_cls=SegmentedWidget,
            on_display_mode_changed=lambda _mode: None,
        )
        self.addCleanup(widgets.card.deleteLater)

        self.assertEqual(widgets.segmented.accessibleName(), "Режим отображения интерфейса, выбрано: Тёмный")
        self.assertIn("светлый, тёмный или автоматический", widgets.segmented.accessibleDescription())

        widgets.segmented.setCurrentItem("light")

        self.assertEqual(widgets.segmented.accessibleName(), "Режим отображения интерфейса, выбрано: Светлый")
        self.assertEqual(
            widgets.segmented.property("screenReaderStateText"),
            "Режим отображения интерфейса, выбрано: Светлый",
        )

    def test_language_selector_reads_current_language(self) -> None:
        widgets = build_language_section(
            tr_language="ru",
            add_section_title=lambda **_kwargs: None,
            settings_card_cls=SettingsCard,
            caption_label_cls=CaptionLabel,
            body_label_cls=BodyLabel,
            combo_cls=ComboBox,
            on_ui_language_changed=lambda _index: None,
        )
        self.addCleanup(widgets.card.deleteLater)

        self.assertIn("Язык интерфейса", widgets.combo.accessibleName())
        self.assertIn("выбрано:", widgets.combo.accessibleName())
        self.assertIn("Выберите язык", widgets.combo.accessibleDescription())

    def test_background_controls_read_state_and_premium_limit(self) -> None:
        widgets = build_background_section(
            tr_language="ru",
            add_section_title=lambda **_kwargs: None,
            settings_card_cls=SettingsCard,
            caption_label_cls=CaptionLabel,
            body_label_cls=BodyLabel,
            radio_button_cls=RadioButton,
            combo_cls=ComboBox,
            on_bg_preset_toggled=lambda *_args: None,
            on_rkn_background_changed=lambda _index: None,
        )
        self.addCleanup(widgets.card.deleteLater)

        self.assertEqual(widgets.radio_standard.accessibleName(), "Фон окна: Стандартный, выбрано")
        self.assertEqual(widgets.radio_amoled.accessibleName(), "Фон окна: AMOLED — чёрный, недоступно без Premium")
        self.assertEqual(widgets.radio_rkn_chan.accessibleName(), "Фон окна: РКН Тян, недоступно без Premium")
        self.assertEqual(widgets.rkn_background_combo.accessibleName(), "Фон РКН Тян, вариантов пока нет")

    def test_sidebar_icon_style_selector_reads_current_style(self) -> None:
        segmented = SegmentedWidget()
        self.addCleanup(segmented.deleteLater)
        segmented.addItem("standard", "Стандартные", lambda: None)
        segmented.addItem("windows11_fluent", "Windows 11 Fluent", lambda: None)
        segmented.setCurrentItem("standard")

        update_sidebar_icon_style_accessibility(segmented, style="standard")

        self.assertEqual(segmented.accessibleName(), "Стиль иконок бокового меню, выбрано: Стандартные")
        self.assertIn("Выберите стиль иконок", segmented.accessibleDescription())

        segmented.setCurrentItem("windows11_fluent")
        update_sidebar_icon_style_accessibility(segmented, style="windows11_fluent")

        self.assertEqual(segmented.accessibleName(), "Стиль иконок бокового меню, выбрано: Windows 11 Fluent")
        self.assertEqual(
            segmented.property("screenReaderStateText"),
            "Стиль иконок бокового меню, выбрано: Windows 11 Fluent",
        )

    def test_opacity_slider_reads_current_percent(self) -> None:
        class _Page:
            content = QWidget()

            def __init__(self) -> None:
                self.widgets = []

            def add_widget(self, widget) -> None:
                self.widgets.append(widget)

            def add_spacing(self, _value: int) -> None:
                pass

        page = _Page()
        widgets = build_opacity_section(
            page=page,
            tr_language="ru",
            settings_card_cls=SettingsCard,
            caption_label_cls=CaptionLabel,
            body_label_cls=BodyLabel,
            slider_cls=Slider,
            initial_opacity=72,
            get_icon_pixmap=lambda *_args: QPixmap(20, 20),
            on_opacity_changed=lambda _value: None,
        )

        self.assertEqual(widgets.opacity_slider.accessibleName(), "Прозрачность окна, значение: 72%")
        self.assertIn("Настройка прозрачности", widgets.opacity_slider.accessibleDescription())

        widgets.opacity_slider.setValue(85)

        self.assertEqual(widgets.opacity_slider.accessibleName(), "Прозрачность окна, значение: 85%")
        self.assertEqual(
            widgets.opacity_slider.property("screenReaderStateText"),
            "Прозрачность окна, значение: 85%",
        )

    def test_holiday_switches_read_premium_limit_and_state(self) -> None:
        class _Page:
            content = QWidget()

            def __init__(self) -> None:
                self.widgets = []

            def add_section_title(self, **_kwargs) -> None:
                pass

            def add_widget(self, widget) -> None:
                self.widgets.append(widget)

            def add_spacing(self, _value: int) -> None:
                pass

        page = _Page()
        widgets = build_holiday_sections(
            page=page,
            tr_language="ru",
            settings_card_cls=SettingsCard,
            caption_label_cls=CaptionLabel,
            body_label_cls=BodyLabel,
            checkbox_cls=CheckBox,
            get_icon_pixmap=lambda *_args: QPixmap(20, 20),
            on_garland_changed=lambda _state: None,
            on_snowflakes_changed=lambda _state: None,
        )

        self.assertEqual(widgets.garland_checkbox.accessibleName(), "Новогодняя гирлянда, недоступно без Premium")
        self.assertIn("Premium", widgets.garland_checkbox.accessibleDescription())
        self.assertEqual(widgets.snowflakes_checkbox.accessibleName(), "Снежинки, недоступно без Premium")

        widgets.garland_checkbox.setEnabled(True)
        widgets.garland_checkbox.setChecked(True)
        widgets.snowflakes_checkbox.setEnabled(True)
        widgets.snowflakes_checkbox.setChecked(True)
        widgets.snowflakes_checkbox.setChecked(False)

        self.assertEqual(widgets.garland_checkbox.accessibleName(), "Новогодняя гирлянда, включено")
        self.assertEqual(
            widgets.garland_checkbox.property("screenReaderStateText"),
            "Новогодняя гирлянда, включено",
        )
        self.assertEqual(widgets.snowflakes_checkbox.accessibleName(), "Снежинки, выключено")

    def test_saved_holiday_state_refreshes_screen_reader_state(self) -> None:
        from ui.pages.appearance_page import AppearancePage

        garland = CheckBox()
        snowflakes = CheckBox()
        self.addCleanup(garland.deleteLater)
        self.addCleanup(snowflakes.deleteLater)
        garland.setEnabled(True)
        snowflakes.setEnabled(True)

        page = AppearancePage.__new__(AppearancePage)
        page._garland_checkbox = garland
        page._snowflakes_checkbox = snowflakes
        page._set_checked_silently = lambda widget, value: widget.setChecked(bool(value))

        AppearancePage.set_garland_state(page, True)
        AppearancePage.set_snowflakes_state(page, False)

        self.assertEqual(garland.accessibleName(), "Новогодняя гирлянда, включено")
        self.assertEqual(snowflakes.accessibleName(), "Снежинки, выключено")

    def test_saved_sidebar_icon_style_refreshes_screen_reader_state(self) -> None:
        from ui.pages.appearance_page import AppearancePage

        segmented = SegmentedWidget()
        self.addCleanup(segmented.deleteLater)
        segmented.addItem("standard", "Стандартные", lambda: None)
        segmented.addItem("windows11_fluent", "Windows 11 Fluent", lambda: None)
        segmented.setCurrentItem("standard")
        page = AppearancePage.__new__(AppearancePage)
        page._sidebar_icon_style_seg = segmented
        page._begin_ui_sync = lambda: None
        page._end_ui_sync = lambda: None
        page._set_current_item_silently = lambda widget, item: widget.setCurrentItem(item)

        AppearancePage._apply_sidebar_icon_style_value(page, "windows11_fluent")

        self.assertEqual(segmented.accessibleName(), "Стиль иконок бокового меню, выбрано: Windows 11 Fluent")


if __name__ == "__main__":
    unittest.main()
