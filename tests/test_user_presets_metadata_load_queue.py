from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


class _Signal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)


class _MetadataWorker:
    instances = []

    def __init__(self, request_id, load_all_metadata, load_folder_state, page) -> None:
        self.request_id = request_id
        self.load_all_metadata = load_all_metadata
        self.load_folder_state = load_folder_state
        self.page = page
        self.loaded = _Signal()
        self.failed = _Signal()
        self.finished = _Signal()
        self.start_calls = 0
        self.delete_later_calls = 0
        self._running = False
        self.__class__.instances.append(self)

    def isRunning(self) -> bool:  # noqa: N802
        return self._running

    def start(self) -> None:
        self.start_calls += 1
        self._running = True

    def deleteLater(self) -> None:  # noqa: N802
        self.delete_later_calls += 1
        self._running = False


class UserPresetsMetadataLoadQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        _MetadataWorker.instances.clear()

    def test_full_metadata_load_replays_latest_request_after_running_worker_finishes(self) -> None:
        from presets.user_presets_runtime_service import UserPresetsRuntimeAdapter, UserPresetsRuntimeService

        page = SimpleNamespace(isVisible=lambda: True)
        adapter = UserPresetsRuntimeAdapter(
            bulk_reset_running=lambda: False,
            read_single_metadata=lambda _name: None,
            selected_source_file_name=lambda: "",
            presets_dir=lambda: None,
            cached_metadata=lambda: {},
            load_all_metadata=lambda: {},
            load_folder_state=lambda: {},
            build_rows_plan=lambda _metadata, _folder_state: object(),
            apply_rows_plan=lambda _plan, _started_at: None,
            delete_preset_item_meta=lambda _name: None,
        )
        service = UserPresetsRuntimeService()
        service.attach_page(page, adapter)

        with patch(
            "presets.user_presets_runtime_service.UserPresetsMetadataLoadWorker",
            _MetadataWorker,
        ):
            service.load_presets(page)
            service.load_presets(page)

            self.assertEqual(len(_MetadataWorker.instances), 1)

            service._on_metadata_worker_finished(_MetadataWorker.instances[0])

        self.assertEqual(len(_MetadataWorker.instances), 2)
        self.assertEqual(_MetadataWorker.instances[1].request_id, 2)
        self.assertEqual(_MetadataWorker.instances[1].start_calls, 1)

    def test_duplicate_single_metadata_update_skips_visible_refresh(self) -> None:
        from presets.user_presets_runtime_service import UserPresetsRuntimeAdapter, UserPresetsRuntimeService

        page = SimpleNamespace(isVisible=lambda: True)
        adapter = UserPresetsRuntimeAdapter(
            bulk_reset_running=lambda: False,
            read_single_metadata=lambda _name: None,
            selected_source_file_name=lambda: "",
            presets_dir=lambda: None,
            cached_metadata=lambda: {},
            load_all_metadata=lambda: {},
            load_folder_state=lambda: {},
            build_rows_plan=lambda _metadata, _folder_state: object(),
            apply_rows_plan=lambda _plan, _started_at: None,
            delete_preset_item_meta=lambda _name: None,
        )
        service = UserPresetsRuntimeService()
        service.attach_page(page, adapter)
        metadata = {
            "display_name": "Default",
            "description": "",
            "modified_display": "today",
        }
        service._single_metadata_request_id = 3
        service._cached_presets_metadata = {"Default.txt": dict(metadata)}
        service.sync_watched_preset_files = Mock(
            side_effect=AssertionError("duplicate metadata must not resync watcher paths")
        )
        service.try_apply_single_preset_metadata_update = Mock(
            side_effect=AssertionError("duplicate metadata must not repaint preset row")
        )
        service.refresh_presets_view_from_cache = Mock(
            side_effect=AssertionError("duplicate metadata must not refresh preset list")
        )

        service._on_single_metadata_loaded(3, "Default.txt", ("Default.txt", dict(metadata)), page)

        self.assertEqual(service._cached_presets_metadata, {"Default.txt": metadata})


if __name__ == "__main__":
    unittest.main()
