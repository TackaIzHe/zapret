from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class AppearanceWorkerQueueTests(unittest.TestCase):
    def test_appearance_save_pending_restarts_after_event_loop_turn(self) -> None:
        import ui.pages.appearance_page as appearance_page
        from ui.pages.appearance_page import AppearancePage

        page = AppearancePage.__new__(AppearancePage)
        page._cleanup_in_progress = False
        page._appearance_save_pending = [{"action": "display_mode", "value": "dark"}]
        page._start_appearance_save_worker = Mock()
        single_shot = Mock(side_effect=lambda _delay, _callback: None)

        with patch.object(appearance_page, "QTimer", SimpleNamespace(singleShot=single_shot)):
            AppearancePage._on_appearance_save_worker_finished(page, object())

        single_shot.assert_called_once()
        self.assertEqual(single_shot.call_args.args[0], 0)
        page._start_appearance_save_worker.assert_not_called()

        single_shot.call_args.args[1]()

        page._start_appearance_save_worker.assert_called_once_with({"action": "display_mode", "value": "dark"})

    def test_appearance_save_scheduled_start_uses_latest_pending_payload(self) -> None:
        import ui.pages.appearance_page as appearance_page
        from ui.pages.appearance_page import AppearancePage

        page = AppearancePage.__new__(AppearancePage)
        page._cleanup_in_progress = False
        page._appearance_save_pending = [{"action": "display_mode", "value": "dark"}]
        page._appearance_save_start_scheduled = False
        page._appearance_save_runtime = SimpleNamespace(is_running=Mock(return_value=False), start_qthread_worker=Mock())
        page._start_appearance_save_worker = Mock()
        single_shot = Mock(side_effect=lambda _delay, _callback: None)

        with patch.object(appearance_page, "QTimer", SimpleNamespace(singleShot=single_shot)):
            AppearancePage._on_appearance_save_worker_finished(page, object())
            AppearancePage._request_appearance_save(page, "display_mode", "light")

        single_shot.call_args.args[1]()

        page._start_appearance_save_worker.assert_called_once_with(
            {"action": "display_mode", "value": "light", "context_extra": {}}
        )

    def test_rkn_background_options_pending_restarts_after_event_loop_turn(self) -> None:
        import ui.pages.appearance_page as appearance_page
        from ui.pages.appearance_page import AppearancePage

        page = AppearancePage.__new__(AppearancePage)
        page._cleanup_in_progress = False
        page._rkn_background_options_pending = True
        page._start_rkn_background_options_load_worker = Mock()
        single_shot = Mock(side_effect=lambda _delay, _callback: None)

        with patch.object(appearance_page, "QTimer", SimpleNamespace(singleShot=single_shot)):
            AppearancePage._on_rkn_background_options_worker_finished(page, object())

        single_shot.assert_called_once()
        self.assertEqual(single_shot.call_args.args[0], 0)
        page._start_rkn_background_options_load_worker.assert_not_called()

        single_shot.call_args.args[1]()

        page._start_rkn_background_options_load_worker.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
