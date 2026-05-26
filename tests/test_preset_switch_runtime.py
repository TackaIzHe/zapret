from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace
import threading
import tempfile
import unittest
from unittest.mock import Mock, patch


class Winws2PresetSwitchTests(unittest.TestCase):
    def test_same_filter_exit_message_is_retryable_conflict(self) -> None:
        from winws_runtime.runners.zapret2_runner import Winws2StrategyRunner

        runner = object.__new__(Winws2StrategyRunner)

        self.assertTrue(
            runner._is_windivert_conflict_error(
                "Error: A copy of winws2 is already running with the same filter",
                1,
            )
        )

    def test_runner_file_watcher_restart_path_is_removed(self) -> None:
        from winws_runtime.runners import preset_runner_support, zapret1_runner, zapret2_runner

        combined_source = "\n".join(
            (
                inspect.getsource(zapret1_runner),
                inspect.getsource(zapret2_runner),
                inspect.getsource(preset_runner_support),
            )
        )

        self.assertNotIn("ConfigFileWatcher", combined_source)
        self.assertNotIn("_on_config_changed", combined_source)

    def test_fast_switch_cleans_existing_winws_process_not_owned_by_runner(self) -> None:
        from winws_runtime.runners.zapret2_runner import Winws2StrategyRunner

        with tempfile.TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "selected.txt"
            preset_path.write_text("--wf-tcp-out=80", encoding="utf-8")

            runner = object.__new__(Winws2StrategyRunner)
            runner._state_lock = threading.RLock()
            runner.running_process = None
            runner._preset_file_path = ""
            runner._set_last_error = Mock()
            runner._compile_preset_artifact = Mock(
                return_value=SimpleNamespace(
                    validation_ok=True,
                    validation_report="",
                    preset_path=str(preset_path),
                )
            )
            runner._spawn_process_locked = Mock(return_value=True)
            runner._perform_standard_windivert_cleanup = Mock()
            runner._ensure_windivert_ready_before_spawn = Mock(return_value=True)

            with patch(
                "winws_runtime.runners.zapret2_runner.get_all_winws_process_pids",
                return_value=[777],
            ):
                self.assertTrue(runner.switch_preset_file_fast(str(preset_path), "Selected"))

            runner._perform_standard_windivert_cleanup.assert_called_once()
            runner._spawn_process_locked.assert_called_once()

    def test_fast_switch_does_not_need_runner_file_watcher(self) -> None:
        from winws_runtime.runners.zapret2_runner import Winws2StrategyRunner

        with tempfile.TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "selected.txt"
            preset_path.write_text("--wf-tcp-out=80", encoding="utf-8")

            runner = object.__new__(Winws2StrategyRunner)
            runner._state_lock = threading.RLock()
            runner.running_process = None
            runner._preset_file_path = ""
            runner._set_last_error = Mock()
            runner._compile_preset_artifact = Mock(
                return_value=SimpleNamespace(
                    validation_ok=True,
                    validation_report="",
                    preset_path=str(preset_path),
                    launch_args=("--wf-tcp-out=80",),
                )
            )
            runner._spawn_process_locked = Mock(return_value=True)
            runner._perform_standard_windivert_cleanup = Mock()
            runner._ensure_windivert_ready_before_spawn = Mock(return_value=True)

            with patch("winws_runtime.runners.zapret2_runner.get_all_winws_process_pids", return_value=[]):
                self.assertTrue(runner.switch_preset_file_fast(str(preset_path), "Selected"))

    def test_fast_switch_retries_winws2_conflict_inside_switch_without_full_start_fallback(self) -> None:
        from winws_runtime.runners.zapret2_runner import Winws2StrategyRunner

        with tempfile.TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "selected.txt"
            preset_path.write_text("--wf-tcp-out=80", encoding="utf-8")

            runner = object.__new__(Winws2StrategyRunner)
            runner._state_lock = threading.RLock()
            runner.running_process = None
            runner._preset_file_path = ""
            runner.last_error = None
            runner._last_spawn_exit_code = None
            runner._last_spawn_stderr = ""
            runner._set_last_error = Mock()
            runner._perform_standard_windivert_cleanup = Mock()
            runner._aggressive_windivert_cleanup = Mock()
            runner._wait_after_aggressive_windivert_cleanup = Mock()
            runner._ensure_windivert_ready_before_spawn = Mock(return_value=True)
            runner._compile_preset_artifact = Mock(
                return_value=SimpleNamespace(
                    validation_ok=True,
                    validation_report="",
                    preset_path=str(preset_path),
                    launch_args=("--wf-tcp-out=80",),
                )
            )
            runner._start_from_preset_file_locked = Mock(return_value=True)

            def spawn_then_conflict_then_success(*_args, **_kwargs):
                if runner._spawn_process_locked.call_count == 1:
                    runner._last_spawn_exit_code = 1
                    runner._last_spawn_stderr = "A copy of winws2 is already running with the same filter"
                    return False
                return True

            runner._spawn_process_locked = Mock(side_effect=spawn_then_conflict_then_success)

            self.assertTrue(runner.switch_preset_file_fast(str(preset_path), "Selected"))

            self.assertEqual(runner._spawn_process_locked.call_count, 2)
            runner._start_from_preset_file_locked.assert_not_called()
            runner._aggressive_windivert_cleanup.assert_called_once()

    def test_fast_switch_retries_winws1_conflict_inside_switch_without_full_start_fallback(self) -> None:
        from winws_runtime.runners.zapret1_runner import Winws1StrategyRunner

        with tempfile.TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "selected.txt"
            preset_path.write_text("--wf-tcp-out=80", encoding="utf-8")

            runner = object.__new__(Winws1StrategyRunner)
            runner.winws_exe = "winws.exe"
            runner._state_lock = threading.RLock()
            runner.running_process = None
            runner._preset_file_path = ""
            runner.last_error = None
            runner._last_spawn_exit_code = None
            runner._last_spawn_stderr = ""
            runner._set_last_error = Mock()
            runner._prepare_cleanup_before_spawn_locked = Mock()
            runner._ensure_windivert_ready_before_spawn = Mock(return_value=True)
            runner._compile_preset_artifact = Mock(
                return_value=SimpleNamespace(
                    validation_ok=True,
                    validation_report="",
                    preset_path=str(preset_path),
                    launch_args=("--wf-tcp-out=80",),
                )
            )
            runner._start_from_preset_file_locked = Mock(return_value=True)

            def spawn_then_conflict_then_success(*_args, **_kwargs):
                if runner._spawn_process_locked.call_count == 1:
                    runner._last_spawn_exit_code = 1
                    runner._last_spawn_stderr = "A copy of winws is already running with the same filter"
                    return False
                return True

            runner._spawn_process_locked = Mock(side_effect=spawn_then_conflict_then_success)

            with patch("winws_runtime.runners.zapret1_runner.get_process_pids_by_name", return_value=[]):
                self.assertTrue(runner.switch_preset_file_fast(str(preset_path), "Selected"))

            self.assertEqual(runner._spawn_process_locked.call_count, 2)
            runner._start_from_preset_file_locked.assert_not_called()
            runner._prepare_cleanup_before_spawn_locked.assert_called_once_with(retry_count=1)


if __name__ == "__main__":
    unittest.main()
