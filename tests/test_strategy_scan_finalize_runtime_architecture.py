import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from blockcheck.ui.strategy_scan_page import StrategyScanPage


class StrategyScanFinalizeRuntimeArchitectureTests(unittest.TestCase):
    def test_finalize_uses_runtime_not_manual_page_worker(self) -> None:
        page_source = inspect.getsource(StrategyScanPage)
        request_source = inspect.getsource(StrategyScanPage._request_strategy_scan_finalize)
        finished_source = inspect.getsource(StrategyScanPage._on_strategy_scan_finalize_finished)
        failed_source = inspect.getsource(StrategyScanPage._on_strategy_scan_finalize_failed)
        cleanup_source = inspect.getsource(StrategyScanPage.cleanup)

        self.assertIn("_strategy_scan_finalize_runtime = OneShotWorkerRuntime()", page_source)
        self.assertIn("_strategy_scan_finalize_runtime.is_running()", request_source)
        self.assertIn("start_qthread_worker", request_source)
        self.assertIn("bind_worker", request_source)
        self.assertIn("_strategy_scan_finalize_runtime.is_current", finished_source)
        self.assertIn("_strategy_scan_finalize_runtime.is_current", failed_source)
        self.assertIn("_strategy_scan_finalize_runtime.stop", cleanup_source)
        self.assertIn("_strategy_scan_finalize_runtime.cancel", cleanup_source)
        self.assertNotIn("_strategy_scan_finalize_worker =", page_source)
        self.assertNotIn("_strategy_scan_finalize_request_id", page_source)
        self.assertNotIn("worker.start()", request_source)

    def test_finalize_request_waits_while_restart_is_scheduled(self) -> None:
        page = StrategyScanPage.__new__(StrategyScanPage)
        report = object()
        page._strategy_scan_finalize_runtime = SimpleNamespace(is_running=Mock(return_value=False), start_qthread_worker=Mock())
        page._strategy_scan_finalize_start_scheduled = True
        page._strategy_scan_finalize_pending = None

        StrategyScanPage._request_strategy_scan_finalize(page, report)

        page._strategy_scan_finalize_runtime.start_qthread_worker.assert_not_called()
        self.assertIs(page._strategy_scan_finalize_pending, report)

    def test_pending_finalize_restarts_after_event_loop_turn(self) -> None:
        import blockcheck.ui.strategy_scan_page as strategy_scan_page

        page = StrategyScanPage.__new__(StrategyScanPage)
        report = object()
        page._cleanup_in_progress = False
        page._strategy_scan_finalize_pending = report
        page._strategy_scan_finalize_start_scheduled = False
        page._request_strategy_scan_finalize = Mock()
        single_shot = Mock(side_effect=lambda _delay, _callback: None)

        with patch.object(strategy_scan_page, "QTimer", SimpleNamespace(singleShot=single_shot), create=True):
            StrategyScanPage._on_strategy_scan_finalize_worker_finished(page, object())

        single_shot.assert_called_once()
        self.assertEqual(single_shot.call_args.args[0], 0)
        page._request_strategy_scan_finalize.assert_not_called()

        single_shot.call_args.args[1]()

        page._request_strategy_scan_finalize.assert_called_once_with(report)
        self.assertIsNone(page._strategy_scan_finalize_pending)


if __name__ == "__main__":
    unittest.main()
