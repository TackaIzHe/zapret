from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from presets.ui.control.control_page_shared import ControlPageActionMixin


class _LoadRuntime:
    def __init__(self, *, running: bool) -> None:
        self.running = bool(running)
        self.started = 0

    def is_running(self) -> bool:
        return self.running

    def start_qthread_worker(self, **_kwargs) -> None:
        self.started += 1


class _Page(ControlPageActionMixin):
    create_program_settings_load_worker = Mock()
    _on_program_settings_load_finished = Mock()
    _on_program_settings_load_failed = Mock()


class ControlProgramSettingsLoadQueueTests(unittest.TestCase):
    def _make_page(self, *, running: bool):
        load_runtime = _LoadRuntime(running=running)
        page = _Page()
        page._cleanup_in_progress = False
        page._refresh_runtime = SimpleNamespace(
            program_settings_load_runtime=load_runtime,
            program_settings_load_pending=False,
        )
        page.create_program_settings_load_worker = Mock(return_value=object())
        return page, load_runtime

    def test_program_settings_load_marks_pending_while_worker_runs(self) -> None:
        page, load_runtime = self._make_page(running=True)

        page._request_program_settings_load()

        self.assertTrue(page._refresh_runtime.program_settings_load_pending)
        self.assertEqual(load_runtime.started, 0)

    def test_program_settings_load_worker_finished_restarts_pending_load_later(self) -> None:
        page, load_runtime = self._make_page(running=False)
        page._refresh_runtime.program_settings_load_pending = True
        callbacks = []

        with patch(
            "presets.ui.control.control_page_shared.QTimer.singleShot",
            side_effect=lambda _delay, callback: callbacks.append(callback),
        ):
            page._on_program_settings_load_worker_finished(object())

        self.assertFalse(page._refresh_runtime.program_settings_load_pending)
        self.assertEqual(load_runtime.started, 0)
        self.assertEqual(len(callbacks), 1)

        callbacks[0]()

        self.assertEqual(load_runtime.started, 1)


if __name__ == "__main__":
    unittest.main()
