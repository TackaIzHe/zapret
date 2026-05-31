import inspect
import unittest
from unittest.mock import patch

from blockcheck import strategy_scan_targeting
from blockcheck.ui.strategy_scan_page import StrategyScanPage


class StrategyScanQuickTargetsRuntimeArchitectureTests(unittest.TestCase):
    def test_quick_targets_menu_uses_runtime_not_manual_page_worker(self) -> None:
        page_source = inspect.getsource(StrategyScanPage)
        request_source = inspect.getsource(StrategyScanPage._request_quick_targets_menu)
        loaded_source = inspect.getsource(StrategyScanPage._on_quick_targets_loaded)
        failed_source = inspect.getsource(StrategyScanPage._on_quick_targets_failed)
        cleanup_source = inspect.getsource(StrategyScanPage.cleanup)

        self.assertIn("_quick_targets_runtime = OneShotWorkerRuntime()", page_source)
        self.assertIn("_quick_targets_runtime.is_running()", request_source)
        self.assertIn("start_qthread_worker", request_source)
        self.assertIn("bind_worker", request_source)
        self.assertIn("_quick_targets_runtime.is_current", loaded_source)
        self.assertIn("_quick_targets_runtime.is_current", failed_source)
        self.assertIn("_quick_targets_runtime.stop", cleanup_source)
        self.assertIn("_quick_targets_runtime.cancel", cleanup_source)
        self.assertNotIn("_quick_targets_worker =", page_source)
        self.assertNotIn("_quick_targets_request_id", page_source)
        self.assertNotIn("worker.start()", request_source)

    def test_quick_domain_targets_cache_after_first_load(self) -> None:
        strategy_scan_targeting._quick_domains_cache = None

        with patch("blockcheck.targets.load_domains", return_value=[" Example.COM ", "example.com", "youtu.be"]):
            first = strategy_scan_targeting.load_quick_domains()
            second = strategy_scan_targeting.load_quick_domains()

        self.assertEqual(first, ["example.com", "youtu.be"])
        self.assertEqual(second, first)

    def test_quick_stun_targets_cache_after_first_load(self) -> None:
        strategy_scan_targeting._quick_stun_targets_cache = None

        with patch(
            "blockcheck.targets.get_default_stun_targets",
            return_value=[
                {"value": "stun.discord.media:50000"},
                {"value": "stun.discord.media:50000"},
                {"value": "stun.l.google.com:19302"},
            ],
        ):
            first = strategy_scan_targeting.load_quick_stun_targets()
            second = strategy_scan_targeting.load_quick_stun_targets()

        self.assertEqual(first, ["stun.discord.media:50000", "stun.l.google.com:19302"])
        self.assertEqual(second, first)


if __name__ == "__main__":
    unittest.main()
