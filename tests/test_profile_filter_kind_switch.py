from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

from core.paths import AppPaths
from profile.parser import parse_preset_text
from profile.service import ProfilePresetService


class _PresetStore:
    def __init__(self, text: str) -> None:
        self.text = text

    def read_selected_preset_source(self, _launch_method: str):
        return self.text, SimpleNamespace(file_name="test.txt", name="test")

    def save_selected_preset_source(self, _launch_method: str, text: str) -> None:
        self.text = text


class ProfileFilterKindSwitchTests(unittest.TestCase):
    def _service(self, text: str, *, root: Path | None = None) -> tuple[ProfilePresetService, _PresetStore]:
        store = _PresetStore(text)
        base = root or Path("src").resolve()
        feature = SimpleNamespace(
            _presets_feature=store,
            _app_paths=AppPaths(user_root=base, local_root=base),
        )
        return ProfilePresetService(feature, "zapret2_mode"), store

    def test_switch_hostlist_profile_to_ipset_rewrites_same_profile_line(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lists_dir = root / "lists"
            lists_dir.mkdir()
            (lists_dir / "youtube.txt").write_text("youtube.com\n", encoding="utf-8")
            (lists_dir / "ipset-youtube.txt").write_text("1.1.1.1\n", encoding="utf-8")
            service, store = self._service(
                "\n".join(
                    (
                        "--filter-tcp=80,443",
                        "--hostlist=lists/youtube.txt",
                        "--out-range=-d8",
                        "--lua-desync=fake:blob=tls_max:badsum:repeats=8",
                        "--lua-desync=multidisorder:pos=1:seqovl=681:seqovl_pattern=tls_max",
                        "",
                    )
                ),
                root=root,
            )

            new_key = service.set_profile_filter_kind("profile:0", "ipset")

            self.assertEqual(new_key, "profile:0")
            self.assertIn("--ipset=lists/ipset-youtube.txt", store.text)
            self.assertNotIn("--hostlist=lists/youtube.txt", store.text)
            self.assertIn("--out-range=-d8", store.text)
            self.assertIn("--lua-desync=fake:blob=tls_max:badsum:repeats=8", store.text)
            preset = parse_preset_text(store.text, engine="winws2")
            self.assertEqual(len(preset.profiles), 1)

    def test_switch_ipset_profile_to_hostlist_rewrites_same_profile_line(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lists_dir = root / "lists"
            lists_dir.mkdir()
            (lists_dir / "youtube.txt").write_text("youtube.com\n", encoding="utf-8")
            (lists_dir / "ipset-youtube.txt").write_text("1.1.1.1\n", encoding="utf-8")
            service, store = self._service(
                "\n".join(
                    (
                        "--filter-tcp=80,443",
                        "--ipset=lists/ipset-youtube.txt",
                        "--out-range=-d8",
                        "--lua-desync=fake:repeats=6:blob=fake_default_quic",
                        "",
                    )
                ),
                root=root,
            )

            new_key = service.set_profile_filter_kind("profile:0", "hostlist")

            self.assertEqual(new_key, "profile:0")
            self.assertIn("--hostlist=lists/youtube.txt", store.text)
            self.assertNotIn("--ipset=lists/ipset-youtube.txt", store.text)
            self.assertIn("--out-range=-d8", store.text)
            preset = parse_preset_text(store.text, engine="winws2")
            self.assertEqual(len(preset.profiles), 1)

    def test_missing_generated_ipset_is_not_offered_or_written(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lists_dir = root / "lists"
            lists_dir.mkdir()
            (lists_dir / "discord-updates.txt").write_text("discord.com\n", encoding="utf-8")
            service, store = self._service(
                "\n".join(
                    (
                        "--filter-tcp=443",
                        "--hostlist=lists/discord-updates.txt",
                        "--lua-desync=pass",
                        "",
                    )
                ),
                root=root,
            )

            setup = service.get_profile_setup("profile:0")
            payload = service.list_profiles()
            new_key = service.set_profile_filter_kind("profile:0", "ipset")

        self.assertIsNotNone(setup)
        self.assertEqual(setup.editable_filter_kinds, ("hostlist",))
        self.assertEqual(setup.item.list_type, "")
        self.assertEqual(setup.list_editor.kind, "hostlist")
        self.assertTrue(setup.list_editor.editable)
        self.assertNotIn("hostlist", setup.match_summary)
        self.assertEqual(payload.items[0].list_type, "")
        self.assertIsNone(new_key)
        self.assertIn("--hostlist=lists/discord-updates.txt", store.text)
        self.assertNotIn("ipset-discord-updates.txt", store.text)

    def test_existing_generated_ipset_is_offered_and_written(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lists_dir = root / "lists"
            lists_dir.mkdir()
            (lists_dir / "discord.txt").write_text("discord.com\n", encoding="utf-8")
            (lists_dir / "ipset-discord.txt").write_text("1.1.1.1\n", encoding="utf-8")
            service, store = self._service(
                "\n".join(
                    (
                        "--filter-tcp=443",
                        "--hostlist=lists/discord.txt",
                        "--lua-desync=pass",
                        "",
                    )
                ),
                root=root,
            )

            setup = service.get_profile_setup("profile:0")
            payload = service.list_profiles()
            new_key = service.set_profile_filter_kind("profile:0", "ipset")

        self.assertIsNotNone(setup)
        self.assertEqual(setup.editable_filter_kinds, ("hostlist", "ipset"))
        self.assertEqual(setup.item.list_type, "hostlist")
        self.assertTrue(setup.list_editor.editable)
        self.assertIn("hostlist", setup.match_summary)
        self.assertEqual(payload.items[0].list_type, "hostlist")
        self.assertEqual(new_key, "profile:0")
        self.assertIn("--ipset=lists/ipset-discord.txt", store.text)

    def test_hostlist_and_ipset_variants_keep_same_gui_persistent_key(self) -> None:
        hostlist = parse_preset_text(
            "--filter-tcp=80,443\n--hostlist=lists/youtube.txt\n--lua-desync=pass\n",
            engine="winws2",
        ).profiles[0]
        ipset = parse_preset_text(
            "--filter-tcp=80,443\n--ipset=lists/ipset-youtube.txt\n--lua-desync=pass\n",
            engine="winws2",
        ).profiles[0]

        self.assertEqual(hostlist.persistent_key, ipset.persistent_key)

    def test_logical_key_does_not_strip_non_zapret_list_prefixes(self) -> None:
        hostlist = parse_preset_text(
            "--filter-tcp=80,443\n--hostlist=lists/list-youtube.txt\n--lua-desync=pass\n",
            engine="winws2",
        ).profiles[0]
        ipset = parse_preset_text(
            "--filter-tcp=80,443\n--ipset=lists/ipset-youtube.txt\n--lua-desync=pass\n",
            engine="winws2",
        ).profiles[0]

        self.assertNotEqual(hostlist.persistent_key, ipset.persistent_key)


if __name__ == "__main__":
    unittest.main()
