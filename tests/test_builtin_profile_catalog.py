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
