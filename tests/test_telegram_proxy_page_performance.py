from __future__ import annotations

import os
import unittest
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from telegram_proxy.config import settings as telegram_proxy_settings
from telegram_proxy.ui.page import TelegramProxyPage


class TelegramProxyPagePerformanceTests(unittest.TestCase):
    def test_socks5_technical_values_do_not_auto_open_advanced_panel(self) -> None:
        page = TelegramProxyPage.__new__(TelegramProxyPage)
        state = replace(
            telegram_proxy_settings.default_state(),
            mode="socks5",
            upstream_enabled=True,
            upstream_preset_id="no",
            upstream_mode="fallback",
            mtproxy_secret="63dae4ef747d6b64b652ead084cbcad7",
            fake_tls_domain="cdn.example.com",
            proxy_protocol=True,
            pool_size=6,
        )

        self.assertFalse(TelegramProxyPage._advanced_settings_should_open(page, state))

    def test_mtproxy_mode_still_auto_opens_advanced_panel(self) -> None:
        page = TelegramProxyPage.__new__(TelegramProxyPage)
        state = replace(
            telegram_proxy_settings.default_state(),
            mode="mtproxy",
        )

        self.assertTrue(TelegramProxyPage._advanced_settings_should_open(page, state))

    def test_cloudflare_route_still_auto_opens_advanced_panel(self) -> None:
        page = TelegramProxyPage.__new__(TelegramProxyPage)
        state = replace(
            telegram_proxy_settings.default_state(),
            cloudflare_enabled=True,
            cloudflare_domains=("example.com",),
        )

        self.assertTrue(TelegramProxyPage._advanced_settings_should_open(page, state))


if __name__ == "__main__":
    unittest.main()
