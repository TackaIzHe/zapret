from __future__ import annotations

import unittest
from unittest.mock import Mock

from profile.ui.preset_setup_page import PresetSetupPageBase


class _Signal:
    def connect(self, _callback) -> None:
        return None


class _ContextWorker:
    finished_action = _Signal()
    failed = _Signal()
    finished = _Signal()

    def __init__(self) -> None:
        self.start = Mock()
        self.deleteLater = Mock()


class _MoveWorker:
    moved = _Signal()
    failed = _Signal()
    finished = _Signal()

    def __init__(self) -> None:
        self.start = Mock()
        self.deleteLater = Mock()


class _Runtime:
    def __init__(self, *, running: bool = False) -> None:
        self._running = running

    def is_running(self) -> bool:
        return self._running

    def start_qthread_worker(self, *, worker_factory, **_kwargs):
        worker = worker_factory(0)
        worker.start()
        return 0, worker


class ProfilePresetWriteSerializationTests(unittest.TestCase):
    def test_profile_move_waits_while_context_action_worker_runs(self) -> None:
        page = PresetSetupPageBase.__new__(PresetSetupPageBase)
        page.launch_method = "zapret2_mode"
        page._profile_context_action_runtime = _Runtime(running=True)
        page._profile_move_runtime = _Runtime(running=False)
        page._pending_profile_preset_write_operations = []
        page._pending_profile_moves = []
        page._profile_move_request_id = 0
        page._create_profile_move_worker = Mock(return_value=_MoveWorker())

        PresetSetupPageBase._request_profile_move(
            page,
            "after",
            "profile-a",
            destination_profile_key="profile-b",
            destination_group_key="games",
        )

        page._create_profile_move_worker.assert_not_called()
        self.assertEqual(
            page._pending_profile_preset_write_operations,
            [
                {
                    "kind": "move",
                    "action": "after",
                    "profile_key": "profile-a",
                    "enabled": None,
                    "source_profile_key": "profile-a",
                    "destination_profile_key": "profile-b",
                    "destination_group_key": "games",
                }
            ],
        )

    def test_profile_context_action_waits_while_move_worker_runs(self) -> None:
        page = PresetSetupPageBase.__new__(PresetSetupPageBase)
        page.launch_method = "zapret2_mode"
        page._profile_context_action_runtime = _Runtime(running=False)
        page._profile_move_runtime = _Runtime(running=True)
        page._pending_profile_preset_write_operations = []
        page._pending_profile_context_actions = []
        page._profile_context_action_request_id = 0
        page._profile_context_action_enabled_by_request = {}
        page._create_profile_context_action_worker = Mock(return_value=_ContextWorker())

        PresetSetupPageBase._request_profile_context_action(
            page,
            "set_enabled",
            "profile-a",
            enabled=False,
        )

        page._create_profile_context_action_worker.assert_not_called()
        self.assertEqual(
            page._pending_profile_preset_write_operations,
            [
                {
                    "kind": "context",
                    "action": "set_enabled",
                    "profile_key": "profile-a",
                    "enabled": False,
                    "source_profile_key": "",
                    "destination_profile_key": "",
                    "destination_group_key": "",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
