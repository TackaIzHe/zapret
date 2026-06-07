from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class ProgramSettingsFastSnapshotTests(unittest.TestCase):
    def test_fast_snapshot_reads_only_settings_json_values(self) -> None:
        from core.runtime.program_settings_runtime_service import ProgramSettingsRuntimeService

        defender_cls = Mock()
        max_blocked = Mock(return_value=True)

        with (
            patch("settings.store.get_dpi_autostart", return_value=True),
            patch("settings.store.get_gui_autostart_enabled", return_value=True),
            patch("settings.store.get_hide_to_tray_on_minimize_close", return_value=False),
            patch("settings.store.get_defender_disabled_memory", return_value=True),
            patch("settings.store.get_max_blocked", return_value=True),
            patch("windows_features.defender_manager.WindowsDefenderManager", defender_cls),
            patch("windows_features.max_blocker.is_max_blocked", max_blocked),
        ):
            snapshot = ProgramSettingsRuntimeService().read_snapshot()

        self.assertTrue(snapshot.auto_dpi_enabled)
        self.assertTrue(snapshot.gui_autostart_enabled)
        self.assertFalse(snapshot.hide_to_tray_on_minimize_close)
        self.assertTrue(snapshot.defender_disabled)
        self.assertTrue(snapshot.max_blocked)
        defender_cls.assert_not_called()
        max_blocked.assert_not_called()

    def test_windows_feature_snapshot_updates_only_heavy_values(self) -> None:
        from core.runtime.program_settings_runtime_service import ProgramSettingsRuntimeService

        service = ProgramSettingsRuntimeService()

        with (
            patch("settings.store.get_dpi_autostart", return_value=True),
            patch("settings.store.get_gui_autostart_enabled", return_value=False),
            patch("settings.store.get_hide_to_tray_on_minimize_close", return_value=True),
        ):
            fast_snapshot = service.refresh_fast()

        with (
            patch("settings.store.get_dpi_autostart", side_effect=AssertionError("fast settings were reread")),
            patch(
                "settings.store.get_gui_autostart_enabled",
                side_effect=AssertionError("fast settings were reread"),
            ),
            patch(
                "settings.store.get_hide_to_tray_on_minimize_close",
                side_effect=AssertionError("fast settings were reread"),
            ),
            patch("windows_features.defender_manager.WindowsDefenderManager") as defender_cls,
            patch("windows_features.max_blocker.is_max_blocked", return_value=True),
        ):
            defender_cls.return_value.is_defender_disabled.return_value = True
            heavy_snapshot = service.refresh_system_status()

        self.assertTrue(fast_snapshot.auto_dpi_enabled)
        self.assertTrue(heavy_snapshot.auto_dpi_enabled)
        self.assertFalse(heavy_snapshot.gui_autostart_enabled)
        self.assertTrue(heavy_snapshot.hide_to_tray_on_minimize_close)
        self.assertTrue(heavy_snapshot.defender_disabled)
        self.assertTrue(heavy_snapshot.max_blocked)

    def test_startup_warmed_fast_snapshot_is_used_without_settings_read(self) -> None:
        from core.runtime.program_settings_runtime_service import (
            ProgramSettingsRuntimeService,
            store_warmed_program_settings_fast_snapshot,
        )

        store_warmed_program_settings_fast_snapshot(
            auto_dpi_enabled=True,
            gui_autostart_enabled=True,
            hide_to_tray_on_minimize_close=False,
            defender_disabled=True,
            max_blocked=True,
        )
        service = ProgramSettingsRuntimeService()
        store_warmed_program_settings_fast_snapshot(
            auto_dpi_enabled=None,
            gui_autostart_enabled=None,
            hide_to_tray_on_minimize_close=None,
        )

        with (
            patch("settings.store.get_dpi_autostart", side_effect=AssertionError("settings were reread")),
            patch(
                "settings.store.get_gui_autostart_enabled",
                side_effect=AssertionError("settings were reread"),
            ),
            patch(
                "settings.store.get_hide_to_tray_on_minimize_close",
                side_effect=AssertionError("settings were reread"),
            ),
            patch(
                "settings.store.get_defender_disabled_memory",
                side_effect=AssertionError("settings were reread"),
            ),
            patch("settings.store.get_max_blocked", side_effect=AssertionError("settings were reread")),
            patch("windows_features.defender_manager.WindowsDefenderManager") as defender_cls,
            patch("windows_features.max_blocker.is_max_blocked") as max_blocked,
        ):
            snapshot = service.load_snapshot()

        self.assertTrue(snapshot.auto_dpi_enabled)
        self.assertTrue(snapshot.gui_autostart_enabled)
        self.assertFalse(snapshot.hide_to_tray_on_minimize_close)
        self.assertTrue(snapshot.defender_disabled)
        self.assertTrue(snapshot.max_blocked)
        defender_cls.assert_not_called()
        max_blocked.assert_not_called()

    def test_attach_program_settings_runtime_applies_ready_snapshot_immediately(self) -> None:
        from program_settings.runtime import attach_program_settings_runtime

        applied = []
        runtime_service = SimpleNamespace(
            subscribe=Mock(side_effect=lambda callback, emit_initial=False: callback("ready") or (lambda: None)),
        )

        attach_program_settings_runtime(
            SimpleNamespace(_program_settings_runtime_attached=False),
            runtime_service=runtime_service,
            apply_snapshot_fn=applied.append,
        )

        runtime_service.subscribe.assert_called_once()
        self.assertTrue(runtime_service.subscribe.call_args.kwargs["emit_initial"])
        self.assertEqual(applied, ["ready"])

    def test_load_program_settings_snapshot_refreshes_fast_settings_after_save(self) -> None:
        from program_settings.runtime import load_program_settings_snapshot

        runtime_service = SimpleNamespace(
            read_snapshot=Mock(return_value="stale"),
            refresh_fast=Mock(return_value="fresh"),
        )

        self.assertEqual(load_program_settings_snapshot(runtime_service), "fresh")
        runtime_service.refresh_fast.assert_called_once_with()
        runtime_service.read_snapshot.assert_not_called()

    def test_gui_autostart_is_not_window_level_ui_state(self) -> None:
        import app.state_store as state_store

        self.assertNotIn("autostart_enabled", state_store.AppUiState.__dataclass_fields__)
        self.assertFalse(hasattr(state_store.MainWindowStateStore, "set_autostart"))
        self.assertFalse(hasattr(state_store.AppRuntimeState, "is_autostart_enabled"))
        self.assertFalse(hasattr(state_store.AppRuntimeState, "set_autostart"))


if __name__ == "__main__":
    unittest.main()
