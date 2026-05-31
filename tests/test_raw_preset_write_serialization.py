from __future__ import annotations

import unittest
from unittest.mock import Mock

from presets.ui.common.preset_subpage_base import PresetRawEditorPage


class _Runtime:
    def __init__(self, *, running: bool = False) -> None:
        self.running = running
        self.started: list[object] = []

    def is_running(self) -> bool:
        return self.running

    def start_qthread_worker(self, *, worker_factory, **_kwargs):
        worker = worker_factory(0)
        self.started.append(worker)
        return 0, worker


class RawPresetWriteSerializationTests(unittest.TestCase):
    def test_raw_preset_action_waits_while_activation_runs(self) -> None:
        worker = object()
        page = PresetRawEditorPage.__new__(PresetRawEditorPage)
        page._raw_activate_runtime = _Runtime(running=True)
        page._raw_action_runtime = _Runtime(running=False)
        page._raw_action_request_id = 0
        page._pending_raw_preset_activation = ""
        page._pending_raw_preset_actions = []
        page._pending_raw_preset_write_operations = []
        page.create_raw_preset_action_worker = Mock(return_value=worker)

        PresetRawEditorPage._request_raw_preset_action(page, "export", file_name="Default.txt")

        page.create_raw_preset_action_worker.assert_not_called()
        self.assertEqual(
            page._pending_raw_preset_write_operations,
            [
                {
                    "kind": "action",
                    "action": "export",
                    "payload": {"file_name": "Default.txt"},
                }
            ],
        )

        page._raw_activate_runtime.running = False
        PresetRawEditorPage._on_preset_activation_worker_finished(page, object())

        page.create_raw_preset_action_worker.assert_called_once_with(
            1,
            action="export",
            payload={"file_name": "Default.txt"},
            parent=page,
        )
        self.assertEqual(page._raw_action_runtime.started, [worker])

    def test_raw_preset_activation_waits_while_action_runs(self) -> None:
        worker = object()
        page = PresetRawEditorPage.__new__(PresetRawEditorPage)
        page._raw_action_runtime = _Runtime(running=True)
        page._raw_activate_runtime = _Runtime(running=False)
        page._raw_activate_request_id = 0
        page._preset_file_name = "Next.txt"
        page._pending_raw_preset_activation = ""
        page._pending_raw_preset_actions = []
        page._pending_raw_preset_write_operations = []
        page.activateButton = None
        page.create_raw_preset_activate_worker = Mock(return_value=worker)

        PresetRawEditorPage._request_preset_activation(page)

        page.create_raw_preset_activate_worker.assert_not_called()
        self.assertEqual(
            page._pending_raw_preset_write_operations,
            [{"kind": "activate", "file_name": "Next.txt"}],
        )

        page._raw_action_runtime.running = False
        PresetRawEditorPage._on_raw_preset_action_worker_finished(page, object())

        page.create_raw_preset_activate_worker.assert_called_once_with(1, "Next.txt", page)
        self.assertEqual(page._raw_activate_runtime.started, [worker])

    def test_duplicate_raw_preset_action_is_not_replayed_from_old_queue(self) -> None:
        worker = object()
        page = PresetRawEditorPage.__new__(PresetRawEditorPage)
        page._raw_action_runtime = _Runtime(running=True)
        page._raw_activate_runtime = _Runtime(running=False)
        page._raw_action_request_id = 0
        page._pending_raw_preset_activation = ""
        page._pending_raw_preset_actions = []
        page._pending_raw_preset_write_operations = []
        page._cleanup_in_progress = False
        page.create_raw_preset_action_worker = Mock(return_value=worker)

        for _ in range(2):
            PresetRawEditorPage._request_raw_preset_action(
                page,
                "export",
                file_name="Default.txt",
            )

        self.assertEqual(
            page._pending_raw_preset_write_operations,
            [
                {
                    "kind": "action",
                    "action": "export",
                    "payload": {"file_name": "Default.txt"},
                }
            ],
        )
        self.assertEqual(
            page._pending_raw_preset_actions,
            [],
        )

        page._raw_action_runtime.running = False
        PresetRawEditorPage._on_raw_preset_action_worker_finished(page, object())
        PresetRawEditorPage._on_raw_preset_action_worker_finished(page, object())

        page.create_raw_preset_action_worker.assert_called_once_with(
            1,
            action="export",
            payload={"file_name": "Default.txt"},
            parent=page,
        )
        self.assertEqual(page._raw_action_runtime.started, [worker])

    def test_different_raw_preset_actions_are_kept_in_order(self) -> None:
        page = PresetRawEditorPage.__new__(PresetRawEditorPage)
        page._raw_action_runtime = _Runtime(running=True)
        page._raw_activate_runtime = _Runtime(running=False)
        page._pending_raw_preset_activation = ""
        page._pending_raw_preset_actions = []
        page._pending_raw_preset_write_operations = []
        page.create_raw_preset_action_worker = Mock()

        PresetRawEditorPage._request_raw_preset_action(
            page,
            "export",
            file_name="Default.txt",
        )
        PresetRawEditorPage._request_raw_preset_action(
            page,
            "delete",
            file_name="Default.txt",
        )

        page.create_raw_preset_action_worker.assert_not_called()
        self.assertEqual(
            page._pending_raw_preset_write_operations,
            [
                {
                    "kind": "action",
                    "action": "export",
                    "payload": {"file_name": "Default.txt"},
                },
                {
                    "kind": "action",
                    "action": "delete",
                    "payload": {"file_name": "Default.txt"},
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
