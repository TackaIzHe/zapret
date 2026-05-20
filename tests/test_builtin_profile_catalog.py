from __future__ import annotations

from pathlib import Path
import unittest

from profile.models import build_profile_logical_key
from profile.parser import parse_preset_text


PUBLIC_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = PUBLIC_ROOT.parent / "private_zapretgui"
ALL_PROFILES_PATH = PRIVATE_ROOT / "resources" / "profile" / "templates" / "all_profiles.txt"
WIDE_DISCORD_TCP_FILTER = "--filter-tcp=80,443,1080,2053,2083,2087,2096,8443"
WIDE_DISCORD_PRIMARY_LINES = {
    "--hostlist-domains=discord.media",
    "--hostlist=lists/discord.txt",
    "--ipset=lists/ipset-discord.txt",
}


class BuiltinProfileCatalogTests(unittest.TestCase):
    def test_all_profiles_keeps_wide_discord_tcp_filter_only_for_discord_entries(self) -> None:
        preset = parse_preset_text(
            ALL_PROFILES_PATH.read_text(encoding="utf-8"),
            engine="winws2",
            source_name=ALL_PROFILES_PATH.name,
        )

        offenders: list[str] = []
        for profile in preset.profiles:
            if WIDE_DISCORD_TCP_FILTER not in profile.match.filter_lines:
                continue
            primary_lines = set(profile.match.hostlist_lines + profile.match.ipset_lines + profile.match.hostlist_domains_lines)
            if primary_lines != {next(iter(primary_lines & WIDE_DISCORD_PRIMARY_LINES), "")}:
                offenders.append(f"{profile.display_name}: {sorted(primary_lines)}")

        self.assertEqual(offenders, [])

    def test_builtin_presets_do_not_put_wide_discord_tcp_filter_on_other_lists(self) -> None:
        template_keys = _all_profile_keys()
        offenders: list[str] = []

        for engine in ("winws1", "winws2"):
            for path in sorted((PUBLIC_ROOT / "src" / "presets" / "builtin" / engine).glob("*.txt")):
                preset = parse_preset_text(
                    path.read_text(encoding="utf-8", errors="replace"),
                    engine=engine,
                    source_name=path.name,
                )
                for profile in preset.profiles:
                    if WIDE_DISCORD_TCP_FILTER not in profile.match.filter_lines:
                        continue
                    primary_lines = set(profile.match.hostlist_lines + profile.match.ipset_lines + profile.match.hostlist_domains_lines)
                    logical_key = build_profile_logical_key(profile.match_signature)
                    if primary_lines not in ({line} for line in WIDE_DISCORD_PRIMARY_LINES) or logical_key not in template_keys:
                        offenders.append(f"{engine}/{path.name} profile {profile.index}: {profile.display_name}")

        self.assertEqual(offenders, [])

    def test_builtin_presets_keep_known_launch_presets_that_are_not_ui_templates(self) -> None:
        """Builtin preset-ы являются runtime-ресурсами, а не копией all_profiles.txt.

        all_profiles.txt описывает библиотеку profile-ов для GUI. Встроенные preset-ы
        могут содержать технические all-sites, circular, voice и winws1 блоки, которых
        нет в этой библиотеке, но они всё равно должны оставаться в поставке.
        """
        known_presets = (
            ("winws1", "discord_voice_dtls.txt"),
            ("winws1", "alt10_190b_allsites.txt"),
            ("winws2", "ALL TCP & UDP discord_urgent_sni.txt"),
            ("winws2", "Default (circular).txt"),
            ("winws2", "syndata (circular).txt"),
        )
        offenders: list[str] = []

        for engine, file_name in known_presets:
            path = PUBLIC_ROOT / "src" / "presets" / "builtin" / engine / file_name
            if not path.exists():
                offenders.append(f"{engine}/{file_name}: missing")
                continue
            preset = parse_preset_text(
                path.read_text(encoding="utf-8", errors="replace"),
                engine=engine,
                source_name=path.name,
            )
            if not preset.profiles:
                offenders.append(f"{engine}/{file_name}: empty")

        self.assertEqual(offenders, [])

    def test_all_profiles_does_not_absorb_runtime_only_all_sites_templates(self) -> None:
        """all_profiles.txt не должен становиться авто-свалкой runtime-only блоков.

        Такие блоки правятся в builtin preset-ах вручную. Добавление их в библиотеку
        profile-ов маскирует проблему матчинга и потом провоцирует опасную чистку
        preset-ов по принципу "нет в all_profiles, значит удалить".
        """
        preset = parse_preset_text(
            ALL_PROFILES_PATH.read_text(encoding="utf-8"),
            engine="winws2",
            source_name=ALL_PROFILES_PATH.name,
        )
        offenders: list[str] = []

        for profile in preset.profiles:
            has_regular_list = bool(
                profile.match.hostlist_lines
                or profile.match.ipset_lines
                or profile.match.hostlist_domains_lines
            )
            if has_regular_list:
                continue
            has_all_sites_excludes = bool(
                profile.match.hostlist_exclude_lines
                or profile.match.ipset_exclude_lines
            )
            if has_all_sites_excludes:
                offenders.append(f"profile {profile.index}: {profile.display_name}")

        self.assertEqual(offenders, [])

    def test_builtin_presets_are_not_empty(self) -> None:
        offenders: list[str] = []

        for engine in ("winws1", "winws2"):
            for path in sorted((PUBLIC_ROOT / "src" / "presets" / "builtin" / engine).glob("*.txt")):
                preset = parse_preset_text(
                    path.read_text(encoding="utf-8", errors="replace"),
                    engine=engine,
                    source_name=path.name,
                )
                if not preset.profiles:
                    offenders.append(f"{engine}/{path.name}")

        self.assertEqual(offenders, [])

    def test_all_profiles_have_logical_keys(self) -> None:
        offenders: list[str] = []

        for engine in ("winws1", "winws2"):
            preset = parse_preset_text(
                ALL_PROFILES_PATH.read_text(encoding="utf-8"),
                engine=engine,
                source_name=ALL_PROFILES_PATH.name,
            )
            for profile in preset.profiles:
                if not build_profile_logical_key(profile.match_signature):
                    offenders.append(f"{engine} profile {profile.index}: {profile.display_name}")

        self.assertEqual(offenders, [])


def _all_profile_keys() -> set[str]:
    preset = parse_preset_text(
        ALL_PROFILES_PATH.read_text(encoding="utf-8"),
        engine="winws2",
        source_name=ALL_PROFILES_PATH.name,
    )
    return {
        build_profile_logical_key(profile.match_signature)
        for profile in preset.profiles
        if build_profile_logical_key(profile.match_signature)
    }


if __name__ == "__main__":
    unittest.main()
