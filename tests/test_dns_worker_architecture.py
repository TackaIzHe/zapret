from __future__ import annotations

import inspect
import unittest

from app.feature_facades.dns import build_dns_feature
from dns import dns_check_worker, page_workers


class DnsWorkerArchitectureTests(unittest.TestCase):
    def test_network_action_workers_receive_feature_action_callables(self) -> None:
        feature_source = inspect.getsource(build_dns_feature)
        worker_source = "\n".join(
            (
                inspect.getsource(page_workers.DnsForceDnsActionWorker),
                inspect.getsource(page_workers.DnsFlushCacheWorker),
                inspect.getsource(page_workers.DnsIspWarningWorker),
                inspect.getsource(page_workers.DnsApplyWorker),
            )
        )

        self.assertNotIn("dns_feature=feature", feature_source)
        self.assertNotIn("self._dns =", worker_source)
        self.assertNotIn("self._dns.", worker_source)
        self.assertNotIn("import dns.public", worker_source)
        self.assertNotIn("dns_public.", worker_source)

        for expected in (
            "get_force_dns_status=feature.get_force_dns_status",
            "enable_force_dns=feature.enable_force_dns",
            "disable_force_dns=feature.disable_force_dns",
            "flush_dns_cache=feature.flush_dns_cache",
            "apply_auto_dns=feature.apply_auto_dns",
            "apply_provider_dns=feature.apply_provider_dns",
            "apply_custom_dns=feature.apply_custom_dns",
            "refresh_dns_info=feature.refresh_dns_info",
            "is_isp_dns_warning_shown=feature.is_isp_dns_warning_shown",
            "mark_isp_dns_warning_shown=feature.mark_isp_dns_warning_shown",
            "normalize_adapter_alias=feature.normalize_adapter_alias",
        ):
            self.assertIn(expected, feature_source)

        for expected in (
            "_get_force_dns_status",
            "_enable_force_dns",
            "_disable_force_dns",
            "_flush_dns_cache",
            "_apply_auto_dns",
            "_apply_provider_dns",
            "_apply_custom_dns",
            "_refresh_dns_info",
            "_is_isp_dns_warning_shown",
            "_mark_isp_dns_warning_shown",
            "_normalize_adapter_alias",
        ):
            self.assertIn(expected, worker_source)

    def test_dns_check_workers_receive_feature_action_callables(self) -> None:
        feature_source = inspect.getsource(build_dns_feature)
        worker_source = "\n".join(
            (
                inspect.getsource(dns_check_worker.DNSCheckWorker),
                inspect.getsource(dns_check_worker.DNSCheckSaveWorker),
                inspect.getsource(dns_check_worker.DNSQuickCheckWorker),
            )
        )

        for expected in (
            "run_dns_poisoning_check=feature.run_dns_poisoning_check",
            "save_dns_check_results=feature.save_dns_check_results",
            "run_quick_dns_check=feature.run_quick_dns_check",
        ):
            self.assertIn(expected, feature_source)

        for expected in (
            "_run_dns_poisoning_check",
            "_save_dns_check_results",
            "_run_quick_dns_check",
        ):
            self.assertIn(expected, worker_source)

        self.assertNotIn("from dns import commands", worker_source)
        self.assertNotIn("from dns.commands import", worker_source)
        self.assertNotIn("dns_commands.", worker_source)


if __name__ == "__main__":
    unittest.main()
