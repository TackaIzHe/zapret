from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget

from ui.holiday_effects import _Snowflake, GarlandOverlay, SnowflakesOverlay, suspend_window_holiday_effects_for_ui_work


class HolidayEffectsPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_snowflake_motion_rect_covers_old_and_new_positions(self) -> None:
        host = QWidget()
        overlay = SnowflakesOverlay(host)
        flake = _Snowflake(40.0, 50.0)
        flake.size = 4.0

        self.assertTrue(hasattr(overlay, "_snowflake_paint_rect"))
        self.assertTrue(hasattr(overlay, "_snowflake_motion_rect"))

        old_rect = overlay._snowflake_paint_rect(flake)
        flake.x = 44.0
        flake.y = 57.0
        new_rect = overlay._snowflake_paint_rect(flake)

        dirty_rect = overlay._snowflake_motion_rect(flake, 40.0, 50.0)

        self.assertTrue(dirty_rect.contains(old_rect))
        self.assertTrue(dirty_rect.contains(new_rect))
        self.assertLess(dirty_rect.width(), overlay.width() or 640)

    def test_snowflake_pixmap_is_reused_for_same_visual_bucket(self) -> None:
        host = QWidget()
        overlay = SnowflakesOverlay(host)
        flake = _Snowflake(40.0, 50.0)
        flake.size = 3.1
        flake.opacity = 0.31

        first = overlay._snowflake_pixmap(flake, 1.0)
        second = overlay._snowflake_pixmap(flake, 1.0)

        self.assertFalse(first.isNull())
        self.assertEqual(first.cacheKey(), second.cacheKey())
        self.assertEqual(len(overlay._flake_pixmap_cache), 1)

    def test_snowflake_density_stays_bounded_on_large_windows(self) -> None:
        host = QWidget()
        overlay = SnowflakesOverlay(host)

        self.assertLessEqual(overlay._max_flake_count(1920, 1080), 150)
        self.assertLessEqual(overlay._initial_flake_count(1920, 1080), 70)

    def test_snowflake_animation_can_pause_during_heavy_ui_work(self) -> None:
        host = QWidget()
        host.resize(640, 480)
        overlay = SnowflakesOverlay(host)
        overlay.set_enabled(True)

        self.assertTrue(overlay._animate_timer.isActive())
        self.assertTrue(overlay._spawn_timer.isActive())

        overlay.suspend_for_ui_work(1000)

        self.assertFalse(overlay._animate_timer.isActive())
        self.assertFalse(overlay._spawn_timer.isActive())

    def test_garland_animation_can_pause_during_heavy_ui_work(self) -> None:
        host = QWidget()
        host.resize(640, 480)
        overlay = GarlandOverlay(host)
        overlay.set_enabled(True)

        self.assertTrue(overlay._timer.isActive())

        overlay.suspend_for_ui_work(1000)

        self.assertFalse(overlay._timer.isActive())

    def test_window_holiday_suspend_helper_uses_existing_manager(self) -> None:
        calls = []

        class Effects:
            def suspend_for_ui_work(self, duration_ms: int) -> None:
                calls.append(duration_ms)

        window = QWidget()
        window.visual_state = SimpleNamespace(holiday_effects=Effects())
        child = QWidget(window)

        suspend_window_holiday_effects_for_ui_work(child, duration_ms=321)

        self.assertEqual(calls, [321])


if __name__ == "__main__":
    unittest.main()
