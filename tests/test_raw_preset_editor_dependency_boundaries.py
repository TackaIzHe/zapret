from __future__ import annotations

import inspect
import unittest
from unittest.mock import Mock


class RawPresetEditorDependencyBoundaryTests(unittest.TestCase):
    def test_raw_preset_editor_receives_actions_instead_of_presets_feature(self) -> None:
        from presets.raw_preset_editor_workflow import RawPresetEditorController
        from presets.ui.common.preset_subpage_base import PresetRawEditorPage
        from ui.navigation_pages import PageName
        from ui.page_deps.presets import build_preset_raw_editor_page_kwargs

        page_init_source = inspect.getsource(PresetRawEditorPage.__init__)
        controller_source = inspect.getsource(RawPresetEditorController)

        for source in (page_init_source, controller_source):
            self.assertNotIn("presets_feature", source)
            self.assertNotIn("self._presets", source)

        expected_keys = {
            "save_preset_source_by_file_name",
            "get_preset_source_path_by_file_name",
            "get_preset_manifest_by_file_name",
            "open_preset_source_file",
            "rename_preset_by_file_name",
            "duplicate_preset_by_file_name",
            "export_preset_plain_text",
            "reset_preset_to_builtin_by_file_name",
            "delete_preset_by_file_name",
            "get_selected_source_preset_manifest",
            "get_selected_source_preset_file_name",
            "activate_preset_file",
            "publish_preset_content_changed",
        }
        for key in expected_keys:
            self.assertIn(key, page_init_source)
            self.assertIn(key, controller_source)

        presets = Mock()
        kwargs = build_preset_raw_editor_page_kwargs(
            page_name=PageName.ZAPRET2_PRESET_RAW_EDITOR,
            presets_feature=presets,
            runtime_feature=Mock(),
            show_page=Mock(),
            ui_state_store=Mock(),
        )

        for key in expected_keys:
            self.assertIs(kwargs[key], getattr(presets, key))
        self.assertNotIn("presets_feature", kwargs)


if __name__ == "__main__":
    unittest.main()
