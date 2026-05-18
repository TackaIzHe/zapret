from __future__ import annotations

import unittest

from folders.defaults import COMMON_FOLDER_KEY, build_default_preset_folders
from presets.user_presets_page_plans import build_preset_rows_plan


class _Hierarchy:
    def __init__(self, meta: dict[str, dict]) -> None:
        self._meta = meta

    def get_preset_meta(self, file_name: str) -> dict:
        return dict(self._meta.get(file_name) or {})


class PresetFolderRowsTests(unittest.TestCase):
    def test_rows_are_grouped_by_folders_with_pinned_folder_above_all(self) -> None:
        folder_state = build_default_preset_folders()
        folder_state["items"] = {
            "Default.txt": {"folder_key": COMMON_FOLDER_KEY, "order": None},
            "Manual.txt": {"folder_key": COMMON_FOLDER_KEY, "order": 0},
            "Game.txt": {"folder_key": "game-filter", "order": None},
            "Pinned.txt": {"folder_key": COMMON_FOLDER_KEY, "order": None},
        }
        hierarchy = _Hierarchy(
            {
                "Default.txt": {"rating": 9, "pinned": False, "order": None},
                "Manual.txt": {"rating": 0, "pinned": False, "order": 0},
                "Game.txt": {"rating": 0, "pinned": False, "order": None},
                "Pinned.txt": {"rating": 0, "pinned": True, "order": None},
            }
        )

        plan = build_preset_rows_plan(
            all_presets={
                "Default.txt": {"display_name": "Default", "is_builtin": True},
                "Manual.txt": {"display_name": "Manual", "is_builtin": False},
                "Game.txt": {"display_name": "Game", "is_builtin": True},
                "Pinned.txt": {"display_name": "Pinned", "is_builtin": False},
            },
            query="",
            active_file_name="Default.txt",
            language="ru",
            hierarchy=hierarchy,
            folder_state=folder_state,
            empty_not_found_key="missing",
            empty_none_key="empty",
        )

        rows = plan.rows
        self.assertEqual(rows[0]["kind"], "folder")
        self.assertEqual(rows[0]["name"], "Закрепленные")
        self.assertEqual(rows[1]["kind"], "preset")
        self.assertEqual(rows[1]["file_name"], "Pinned.txt")

        common_index = next(index for index, row in enumerate(rows) if row.get("kind") == "folder" and row.get("folder_key") == COMMON_FOLDER_KEY)
        common_items = [
            row["file_name"]
            for row in rows[common_index + 1:]
            if row.get("kind") == "preset"
        ][:2]
        self.assertEqual(common_items, ["Manual.txt", "Default.txt"])

    def test_search_shows_only_matching_folder_rows(self) -> None:
        folder_state = build_default_preset_folders()
        folder_state["items"] = {
            "Default.txt": {"folder_key": COMMON_FOLDER_KEY, "order": None},
            "Game.txt": {"folder_key": "game-filter", "order": None},
        }

        plan = build_preset_rows_plan(
            all_presets={
                "Default.txt": {"display_name": "Default", "is_builtin": True},
                "Game.txt": {"display_name": "Game", "is_builtin": True},
            },
            query="game",
            active_file_name="",
            language="ru",
            hierarchy=_Hierarchy({}),
            folder_state=folder_state,
            empty_not_found_key="missing",
            empty_none_key="empty",
        )

        folder_names = [row["name"] for row in plan.rows if row["kind"] == "folder"]
        item_names = [row["name"] for row in plan.rows if row["kind"] == "preset"]
        self.assertEqual(folder_names, ["Game filter"])
        self.assertEqual(item_names, ["Game"])


if __name__ == "__main__":
    unittest.main()
