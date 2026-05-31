import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from blockcheck.ui.page import BlockcheckPage


class BlockcheckUserDomainRuntimeArchitectureTests(unittest.TestCase):
    def test_user_domain_actions_use_runtime_not_manual_page_worker(self) -> None:
        page_source = inspect.getsource(BlockcheckPage)
        request_source = inspect.getsource(BlockcheckPage._request_user_domain_action)
        start_source = inspect.getsource(BlockcheckPage._start_user_domain_action_worker)
        finished_source = inspect.getsource(BlockcheckPage._on_user_domain_action_finished)
        failed_source = inspect.getsource(BlockcheckPage._on_user_domain_action_failed)
        cleanup_source = inspect.getsource(BlockcheckPage.cleanup)

        self.assertIn("_user_domain_action_runtime = OneShotWorkerRuntime()", page_source)
        self.assertIn("_user_domain_action_runtime.is_running()", request_source)
        self.assertIn("start_qthread_worker", start_source)
        self.assertIn("bind_worker", start_source)
        self.assertIn("_on_user_domain_action_runtime_finished", start_source)
        self.assertIn("_user_domain_action_runtime.is_current", finished_source)
        self.assertIn("_user_domain_action_runtime.is_current", failed_source)
        self.assertIn("_user_domain_action_runtime.stop", cleanup_source)
        self.assertIn("_user_domain_action_runtime.cancel", cleanup_source)
        self.assertNotIn("_user_domain_action_worker =", page_source)
        self.assertNotIn("_user_domain_action_request_id", page_source)
        self.assertNotIn("worker.start()", start_source)

    def test_pending_user_domain_action_restarts_after_event_loop_turn(self) -> None:
        import blockcheck.ui.page as blockcheck_page

        page = BlockcheckPage.__new__(BlockcheckPage)
        page._cleanup_in_progress = False
        page._user_domain_action_pending = [{"action": "add", "domain": "example.com"}]
        page._start_user_domain_action_worker = Mock()
        single_shot = Mock(side_effect=lambda _delay, _callback: None)

        with patch.object(blockcheck_page, "QTimer", SimpleNamespace(singleShot=single_shot), create=True):
            BlockcheckPage._on_user_domain_action_runtime_finished(page, object())

        single_shot.assert_called_once()
        self.assertEqual(single_shot.call_args.args[0], 0)
        page._start_user_domain_action_worker.assert_not_called()

        single_shot.call_args.args[1]()

        page._start_user_domain_action_worker.assert_called_once_with({"action": "add", "domain": "example.com"})


if __name__ == "__main__":
    unittest.main()
