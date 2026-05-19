from __future__ import annotations

import unittest

from profile.icons import resolve_profile_icon


class ProfileIconTests(unittest.TestCase):
    def test_known_profile_uses_brand_icon_from_list_file(self) -> None:
        icon = resolve_profile_icon(
            "YouTube",
            ("--filter-tcp=80,443", "--hostlist=lists/youtube.txt"),
        )

        self.assertEqual(icon.icon_name, "fa5b.youtube")
        self.assertEqual(icon.color, "#FF0000")

    def test_ipset_prefix_does_not_hide_known_identity(self) -> None:
        icon = resolve_profile_icon(
            "Discord",
            ("--filter-tcp=80,443", "--ipset=lists/ipset-discord.txt"),
        )

        self.assertEqual(icon.icon_name, "fa5b.discord")

    def test_unknown_site_gets_stable_initials_icon(self) -> None:
        first = resolve_profile_icon(
            "example.org",
            ("--filter-tcp=443", "--hostlist-domains=example.org"),
        )
        second = resolve_profile_icon(
            "example.org",
            ("--filter-tcp=443", "--hostlist-domains=example.org"),
        )

        self.assertEqual(first, second)
        self.assertTrue(first.icon_name.startswith("profile-initials:"))
        self.assertEqual(first.icon_name, "profile-initials:EX")

    def test_hoster_without_brand_icon_gets_named_fallback_color(self) -> None:
        icon = resolve_profile_icon(
            "cloudflare",
            ("--filter-tcp=80,443", "--ipset=lists/ipset-cloudflare.txt"),
        )

        self.assertEqual(icon.icon_name, "profile-initials:CL")
        self.assertEqual(icon.color, "#F38020")


if __name__ == "__main__":
    unittest.main()
