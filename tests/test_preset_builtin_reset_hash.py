from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from app.feature_facades.presets import PresetsFeature
from core.paths import AppPaths
from presets.models import PresetManifest
from presets.raw_preset_editor_workflow import load_raw_preset_for_file
from settings.mode import ENGINE_WINWS2, ZAPRET2_MODE


class _Feature(PresetsFeature):
    def __init__(self, app_paths: AppPaths, manifests: list[PresetManifest]) -> None:
        super().__init__(_services=SimpleNamespace(app_paths=app_paths))
        self._manifests = list(manifests)

    def list_preset_manifests(self, _launch_method: str):
        return list(self._manifests)


class PresetBuiltinResetHashTests(unittest.TestCase):
    def _feature_with_files(self, *, user_text: str, builtin_text: str) -> _Feature:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        app_paths = AppPaths(user_root=root, local_root=root)
        engine_paths = app_paths.engine_paths(ENGINE_WINWS2).ensure_directories()
        (engine_paths.user_presets_dir / "Default.txt").write_text(user_text, encoding="utf-8")
        (engine_paths.builtin_presets_dir / "Default.txt").write_text(builtin_text, encoding="utf-8")
        return _Feature(
            app_paths,
            [
                PresetManifest(
                    file_name="Default.txt",
                    name="Default",
                    updated_at="",
                    kind="user",
                    storage_scope="user",
                )
            ],
        )

    def test_metadata_marks_user_override_resettable_only_when_hash_differs(self) -> None:
        same_feature = self._feature_with_files(
            user_text="# Preset: Default\n--new\n",
            builtin_text="# Preset: Default\n--new\n",
        )
        _signature, same_metadata = same_feature._build_preset_list_metadata_snapshot(ZAPRET2_MODE)

        self.assertFalse(same_metadata["Default.txt"]["can_reset_to_builtin"])

        different_feature = self._feature_with_files(
            user_text="# Preset: Default\n--new\n--filter-tcp=443\n",
            builtin_text="# Preset: Default\n--new\n",
        )
        _signature, different_metadata = different_feature._build_preset_list_metadata_snapshot(ZAPRET2_MODE)

        self.assertTrue(different_metadata["Default.txt"]["can_reset_to_builtin"])

    def test_raw_preset_load_result_uses_hash_reset_flag(self) -> None:
        feature = self._feature_with_files(
            user_text="# Preset: Default\n--new\n",
            builtin_text="# Preset: Default\n--new\n",
        )
        feature.get_preset_manifest_by_file_name = lambda _method, _name: feature._manifests[0]
        feature.get_preset_source_path_by_file_name = lambda _method, _name: (
            feature._services.app_paths.engine_paths(ENGINE_WINWS2).user_presets_dir / "Default.txt"
        )
        feature.get_selected_source_preset_file_name = lambda _method: ""
        feature.get_selected_source_preset_manifest = lambda _method: None

        result = load_raw_preset_for_file(
            presets_feature=feature,
            launch_method=ZAPRET2_MODE,
            file_name="Default.txt",
        )

        self.assertFalse(result.can_reset_to_builtin)


if __name__ == "__main__":
    unittest.main()
