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
        from app.feature_facades.appearance import AppearanceFeature
        import settings.appearance_workers as appearance_workers
        import ui.theme as theme

        self.assertTrue(hasattr(appearance_workers, "ThemePersistWorker"))

        feature_source = inspect.getsource(AppearanceFeature)
        worker_source = inspect.getsource(appearance_workers.ThemePersistWorker.run)
        manager_init_source = inspect.getsource(theme.ThemeManager.__init__)
        apply_source = inspect.getsource(theme.ThemeManager._apply_css_only)
        request_source = inspect.getsource(theme.ThemeManager._request_theme_persist)
        start_source = inspect.getsource(theme.ThemeManager._start_theme_persist_worker)
        finished_source = inspect.getsource(theme.ThemeManager._on_theme_persist_finished)

        self.assertIn("create_theme_persist_worker", feature_source)
        self.assertIn("save_selected_theme=self.save_selected_theme", feature_source)
        self.assertIn("create_theme_persist_worker", manager_init_source)
        self.assertIn("_create_theme_persist_worker", start_source)
        self.assertNotIn("ThemePersistWorker(", start_source)
        self.assertNotIn("settings_store", worker_source)
        self.assertIn("_request_theme_persist", apply_source)
        self.assertNotIn("set_selected_theme(clean)", apply_source)
        self.assertIn("_theme_persist_pending", request_source)
        self.assertIn("_theme_persist_pending", finished_source)


if __name__ == "__main__":
    unittest.main()
