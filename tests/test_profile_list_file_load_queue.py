from __future__ import annotations

import unittest
from unittest.mock import Mock

from profile.ui.profile_setup_page import ProfileSetupPageBase


class _Signal:
    def connect(self, _callback) -> None:
        return None


class _Worker:
    loaded = _Signal()
    failed = _Signal()
    finished = _Signal()

    def __init__(self, *, running: bool = False) -> None:
        self._running = running
        self.start = Mock()
        self.deleteLater = Mock()

    def isRunning(self) -> bool:  # noqa: N802
        return self._running


class ProfileListFileLoadQueueTests(unittest.TestCase):
    def test_list_file_load_keeps_pending_request_while_worker_runs(self) -> None:
        page = ProfileSetupPageBase.__new__(ProfileSetupPageBase)
        page._editor_tab_built = True
        page._profile_key = "profile-1"
        page._list_file_load_worker = _Worker(running=True)
        page._pending_list_file_load = False

        ProfileSetupPageBase._request_list_file_editor_state(page)

        self.assertTrue(page._pending_list_file_load)

    def test_list_file_load_worker_finished_starts_pending_request(self) -> None:
        page = ProfileSetupPageBase.__new__(ProfileSetupPageBase)
        old_worker = _Worker(running=False)
        next_worker = _Worker(running=False)
        page._editor_tab_built = True
        page._profile_key = "profile-1"
        page._list_file_load_worker = old_worker
        page._pending_list_file_load = True
        page._list_file_load_request_id = 0
        page._list_file_status_label = None
        page._current_filter_kind = Mock(return_value="hostlist")
        page._current_filter_value = Mock(return_value="example.com")
        page.create_profile_list_file_load_worker = Mock(return_value=next_worker)

        ProfileSetupPageBase._on_list_file_worker_finished(page, old_worker)

        page.create_profile_list_file_load_worker.assert_called_once_with(
            1,
            "profile-1",
            filter_kind="hostlist",
            filter_value="example.com",
            parent=page,
        )
        next_worker.start.assert_called_once_with()
        self.assertFalse(page._pending_list_file_load)


if __name__ == "__main__":
    unittest.main()
