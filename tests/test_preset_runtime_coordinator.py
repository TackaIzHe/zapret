from __future__ import annotations

import unittest
from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication


class PresetRuntimeCoordinatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_saving_active_preset_uses_content_apply_not_preset_switch(self) -> None:
        from core.runtime.preset_runtime_coordinator import PresetRuntimeCoordinator
        from settings.mode import ZAPRET2_MODE

        switch_calls: list[tuple[str, str, str]] = []
        content_calls: list[tuple[str, str, str]] = []
        active_path = "C:/Zapret/Dev/presets/winws2/Default v5.txt"
        presets_feature = SimpleNamespace(
            is_selected_source_preset_file=lambda method, file_name: (
                method == ZAPRET2_MODE and file_name == "Default v5.txt"
            )
        )
        ui_state = SimpleNamespace(
            content_revision=0,
            bump_preset_content_revision=lambda: setattr(
                ui_state,
                "content_revision",
                ui_state.content_revision + 1,
            ),
        )
        coordinator = PresetRuntimeCoordinator(
            presets_feature=presets_feature,
            ui_state_store=ui_state,
            get_launch_method=lambda: ZAPRET2_MODE,
            get_active_preset_path=lambda: active_path,
            refresh_after_switch=lambda: None,
            request_selected_source_preset_apply=lambda method, reason, file_name: switch_calls.append(
                (method, reason, file_name)
            )
            or True,
            request_preset_content_apply=lambda method, reason, file_name: content_calls.append(
                (method, reason, file_name)
            )
            or True,
        )
        coordinator._active_preset_file_path = active_path
        coordinator.setup_active_preset_file_watcher = lambda: None

        coordinator.handle_preset_content_changed(ZAPRET2_MODE, "Default v5.txt")

        self.assertEqual(content_calls, [(ZAPRET2_MODE, "preset_content_changed", "Default v5.txt")])
        self.assertEqual(switch_calls, [])
        self.assertEqual(ui_state.content_revision, 1)

    def test_active_preset_revision_is_published_after_click_event(self) -> None:
        from core.runtime.preset_runtime_coordinator import PresetRuntimeCoordinator
        from settings.mode import ZAPRET2_MODE

        class _UiState:
            def __init__(self) -> None:
                self.active_revision = 0

            def bump_active_preset_revision(self) -> None:
                self.active_revision += 1

        ui_state = _UiState()
        coordinator = PresetRuntimeCoordinator(
            presets_feature=SimpleNamespace(),
            ui_state_store=ui_state,
            get_launch_method=lambda: ZAPRET2_MODE,
            get_active_preset_path=lambda: "",
            refresh_after_switch=lambda: None,
            request_selected_source_preset_apply=lambda *_args: True,
            request_preset_content_apply=lambda *_args: True,
        )
        coordinator.setup_active_preset_file_watcher = lambda: None

        coordinator.handle_preset_switched(ZAPRET2_MODE, "Default v5.txt")

        self.assertEqual(ui_state.active_revision, 0)
        self._app.processEvents()
        self.assertEqual(ui_state.active_revision, 1)

    def test_raw_editor_can_save_active_preset_without_publishing_until_commit(self) -> None:
        from presets.raw_preset_editor_workflow import RawPresetEditorController
        from settings.mode import ZAPRET2_MODE

        save_calls: list[tuple[str, str, str, bool]] = []
        publish_calls: list[tuple[str, str]] = []

        class _PresetsFeature:
            def save_preset_source_by_file_name(
                self,
                launch_method,
                file_name,
                source_text,
                *,
                publish_content_changed=True,
            ):
                save_calls.append((launch_method, file_name, source_text, publish_content_changed))
                return type("Manifest", (), {"name": "Default v5", "file_name": file_name})()

            def get_preset_source_path_by_file_name(self, _launch_method, file_name):
                from pathlib import Path

                return Path("C:/Zapret/Dev/presets/winws2") / file_name

            def publish_preset_content_changed(self, launch_method, file_name):
                publish_calls.append((launch_method, file_name))

        feature = _PresetsFeature()
        controller = RawPresetEditorController(
            presets_feature=feature,
            launch_method=ZAPRET2_MODE,
        )

        controller.save_text(
            file_name="Default v5.txt",
            source_text="--new\n--filter-tcp=80\n",
            publish_content_changed=False,
        )
        controller.publish_content_changed("Default v5.txt")

        self.assertEqual(
            save_calls,
            [(ZAPRET2_MODE, "Default v5.txt", "--new\n--filter-tcp=80\n", False)],
        )
        self.assertEqual(publish_calls, [(ZAPRET2_MODE, "Default v5.txt")])

    def test_preset_content_apply_switches_running_preset_once(self) -> None:
        from pathlib import Path
        import tempfile
        from unittest.mock import Mock

        from winws_runtime.flow.apply_policy import request_preset_runtime_content_apply
        from settings.mode import ZAPRET2_MODE

        with tempfile.TemporaryDirectory() as tmp_dir:
            preset_path = Path(tmp_dir) / "selected.txt"
            preset_path.write_text(
                "--wf-tcp-out=80,443\n--filter-tcp=80\n--hostlist=list.txt\n--lua-desync=fake\n",
                encoding="utf-8",
            )

            launch_runtime = SimpleNamespace(
                is_running=Mock(return_value=True),
                switch_presets_async=Mock(),
                stop_dpi_async=Mock(),
            )
            presets_feature = SimpleNamespace(
                get_launch_snapshot=Mock(return_value=SimpleNamespace(preset_path=str(preset_path)))
            )
            runtime_feature = SimpleNamespace(
                objects=SimpleNamespace(launch_runtime=launch_runtime),
                dependencies=SimpleNamespace(presets_feature=presets_feature),
            )

            self.assertTrue(
                request_preset_runtime_content_apply(
                    runtime_feature=runtime_feature,
                    launch_method=ZAPRET2_MODE,
                    reason="preset_content_changed",
                )
            )

            launch_runtime.switch_presets_async.assert_called_once_with(ZAPRET2_MODE)
            launch_runtime.stop_dpi_async.assert_not_called()


if __name__ == "__main__":
    unittest.main()
