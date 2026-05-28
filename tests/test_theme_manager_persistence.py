from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class ThemeManagerPersistenceTests(unittest.TestCase):
    def test_theme_persistence_runs_through_worker(self) -> None:
        import ui.theme as theme

        self.assertTrue(hasattr(theme, "ThemePersistWorker"))

        worker_source = inspect.getsource(theme.ThemePersistWorker.run)
        apply_source = inspect.getsource(theme.ThemeManager._apply_css_only)
        request_source = inspect.getsource(theme.ThemeManager._request_theme_persist)
        finished_source = inspect.getsource(theme.ThemeManager._on_theme_persist_finished)

        self.assertIn("set_selected_theme", worker_source)
        self.assertIn("_request_theme_persist", apply_source)
        self.assertNotIn("set_selected_theme(clean)", apply_source)
        self.assertIn("_theme_persist_pending", request_source)
        self.assertIn("_theme_persist_pending", finished_source)


if __name__ == "__main__":
    unittest.main()
