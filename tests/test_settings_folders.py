from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from settings.normalize import normalize_settings
from settings.schema import SETTINGS_DIR_NAME, SETTINGS_FILE_NAME, build_default_settings


class SettingsFoldersTests(unittest.TestCase):
    def test_default_settings_contains_folders_section(self) -> None:
        settings = build_default_settings()

        self.assertEqual(settings["folders"]["version"], 1)
        self.assertIn("winws2", settings["folders"]["presets"])
        self.assertIn("winws1", settings["folders"]["presets"])
        self.assertIn("profiles", settings["folders"])

    def test_normalize_settings_keeps_valid_folder_state(self) -> None:
        normalized = normalize_settings(
            {
                "folders": {
                    "version": 1,
                    "presets": {
                        "winws2": {
                            "folders": {
                                "common": {"name": "Общие", "order": 3, "collapsed": True, "system": True},
                                "custom": {"name": "Моя", "order": 0, "collapsed": False},
                            },
                            "items": {
                                "Default.txt": {"folder_key": "custom", "order": 0, "rating": 8},
                                "Broken.txt": {"folder_key": "missing", "order": "bad"},
                            },
                        }
                    },
                    "profiles": {
                        "folders": {
                            "common": {"name": "Общие", "order": 6, "collapsed": False, "system": True}
                        },
                        "items": {
                            "name:YouTube": {"folder_key": "common", "order": 1}
                        },
                    },
                }
            }
        )

        winws2 = normalized["folders"]["presets"]["winws2"]
        self.assertEqual(winws2["items"]["Default.txt"]["folder_key"], "custom")
        self.assertEqual(winws2["items"]["Broken.txt"]["folder_key"], "common")
        self.assertIsNone(winws2["items"]["Broken.txt"]["order"])
        self.assertEqual(normalized["folders"]["profiles"]["items"]["name:YouTube"]["order"], 1)

    def test_store_roundtrips_folders_settings(self) -> None:
        from settings import store as settings_store

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch("settings.store.MAIN_DIRECTORY", str(root)):
                saved = settings_store.set_folders_settings(
                    {
                        "presets": {
                            "winws1": {
                                "folders": {
                                    "common": {"name": "Общие", "order": 0, "system": True},
                                },
                                "items": {"preset.txt": {"folder_key": "common", "order": 0}},
                            }
                        }
                    }
                )
                loaded = settings_store.get_folders_settings()
                settings_path = root / SETTINGS_DIR_NAME / SETTINGS_FILE_NAME
                raw = json.loads(settings_path.read_text(encoding="utf-8"))

        self.assertEqual(saved, loaded)
        self.assertEqual(raw["folders"]["presets"]["winws1"]["items"]["preset.txt"]["folder_key"], "common")


if __name__ == "__main__":
    unittest.main()
