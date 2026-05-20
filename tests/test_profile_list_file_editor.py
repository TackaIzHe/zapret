from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from core.paths import AppPaths
from profile.list_file_editor import (
    profile_list_file_reference,
    validate_profile_list_file_text,
)
from profile.parser import parse_preset_text
from profile.service import ProfilePresetService
from settings.mode import ENGINE_WINWS2


class _PresetStore:
    def __init__(self, text: str) -> None:
        self.text = text

    def read_selected_preset_source(self, _launch_method: str):
        return self.text, SimpleNamespace(file_name="selected.txt", name="selected")

    def save_selected_preset_source(self, _launch_method: str, text: str) -> None:
        self.text = text


class ProfileListFileEditorTests(unittest.TestCase):
    def test_validates_hostlist_domains(self) -> None:
        invalid = validate_profile_list_file_text(
            "hostlist",
            "youtube.com\nbad domain\n# comment\nsub.example.org\n",
        )

        self.assertEqual(invalid, ((2, "bad domain"),))

    def test_validates_ipset_entries(self) -> None:
        invalid = validate_profile_list_file_text(
            "ipset",
            "1.1.1.1\n10.0.0.0/8\n1.1.1.1-2.2.2.2\n",
        )

        self.assertEqual(invalid, ((3, "1.1.1.1-2.2.2.2"),))

    def test_profile_reference_uses_current_hostlist_file(self) -> None:
        preset = parse_preset_text(
            "--filter-tcp=80,443\n--hostlist=lists/youtube.txt\n--lua-desync=pass\n",
            engine=ENGINE_WINWS2,
        )

        reference = profile_list_file_reference(preset.profiles[0], Path("/tmp/lists"))

        self.assertTrue(reference.editable)
        self.assertEqual(reference.kind, "hostlist")
        self.assertEqual(reference.file_name, "youtube.txt")

    def test_service_loads_and_saves_current_profile_list_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lists_dir = root / "lists"
            lists_dir.mkdir()
            (lists_dir / "youtube.txt").write_text("youtube.com\n", encoding="utf-8")
            (lists_dir / "ipset-youtube.txt").write_text("1.1.1.1\n", encoding="utf-8")
            store = _PresetStore(
                "--filter-tcp=80,443\n--ipset=lists/ipset-youtube.txt\n--lua-desync=pass\n"
            )
            feature = SimpleNamespace(
                _presets_feature=store,
                _app_paths=AppPaths(user_root=root, local_root=root),
            )
            service = ProfilePresetService(feature, "zapret2_mode")

            setup = service.get_profile_setup("profile:0")
            self.assertEqual(setup.list_editor.kind, "ipset")
            self.assertEqual(setup.list_editor.text, "1.1.1.1\n")

            saved = service.save_profile_list_file_text("profile:0", "8.8.8.8\n")
            saved_text = (lists_dir / "ipset-youtube.txt").read_text(encoding="utf-8")

            self.assertIsNotNone(saved)
            self.assertEqual(saved_text, "8.8.8.8\n")


if __name__ == "__main__":
    unittest.main()
