from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class WindowMetricsTests(unittest.TestCase):
    def test_full_hd_screen_uses_1280_by_720_default_size(self) -> None:
        import config.window_metrics as window_metrics

        with (
            patch.object(window_metrics, "_get_screen_dpi", return_value=120),
            patch.object(window_metrics, "_get_primary_screen_size", return_value=(1920, 1080)),
        ):
            self.assertEqual(window_metrics.get_scaled_window_size(), (1280, 720))

    def test_non_full_hd_screen_keeps_regular_default_size(self) -> None:
        import config.window_metrics as window_metrics

        with (
            patch.object(window_metrics, "_get_screen_dpi", return_value=96),
            patch.object(window_metrics, "_get_primary_screen_size", return_value=(2560, 1440)),
        ):
            self.assertEqual(
                window_metrics.get_scaled_window_size(),
                (window_metrics.BASE_WIDTH, window_metrics.BASE_HEIGHT),
            )


if __name__ == "__main__":
    unittest.main()
