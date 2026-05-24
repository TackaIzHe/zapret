from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class SidebarStateSettingsTests(unittest.TestCase):
    def test_normalize_settings_keeps_sidebar_expanded_state(self) -> None:
        from settings.normalize import normalize_settings

        normalized = normalize_settings({"ui_state": {"sidebar_expanded": True, "unknown": "ignored"}})

        self.assertEqual(normalized["ui_state"], {"sidebar_expanded": True})


if __name__ == "__main__":
    unittest.main()
