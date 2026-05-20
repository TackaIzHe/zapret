from __future__ import annotations

import inspect
import unittest

from profile import commands as profile_commands
from profile.service import ProfilePresetService
from profile.ui.profile_setup_page import ProfileSetupPageBase
from profile.ui.preset_setup_page import PresetSetupPageBase
from presets import display_state
from presets import commands as preset_commands
from presets.ui.common.preset_subpage_base import PresetRawEditorPage
from presets.ui.control.zapret1.page import Zapret1ModeControlPage
from presets.ui.control.zapret2.page import Zapret2ModeControlPage
from presets.user_presets_runtime_service import UserPresetsRuntimeService
from lists.ui.custom_domains_page import CustomDomainsPage
from lists.ui.custom_ipset_page import CustomIpSetPage
from lists.ui.hostlist_page import HostlistPage
from lists.ui.netrogat_page import NetrogatPage


class PresetProfileAsyncArchitectureTests(unittest.TestCase):
    def test_preset_setup_page_loads_profiles_through_worker(self) -> None:
        refresh_source = inspect.getsource(PresetSetupPageBase.refresh_from_preset_switch)
        activated_source = inspect.getsource(PresetSetupPageBase.on_page_activated)

        self.assertNotIn(".list_profiles(", refresh_source)
        self.assertIn("_request_profiles_payload", refresh_source)
        self.assertIn("_request_profiles_payload", activated_source)

    def test_refresh_after_switch_uses_profile_snapshot_not_full_list(self) -> None:
        source = inspect.getsource(display_state.resolve_profile_strategy_display_state)

        self.assertNotIn(".list_profiles(", source)
        self.assertIn("get_profile_strategy_display_state", source)

    def test_user_presets_full_metadata_loading_is_worker_only(self) -> None:
        load_source = inspect.getsource(UserPresetsRuntimeService.load_presets)
        watcher_source = inspect.getsource(UserPresetsRuntimeService.reload_presets_from_watcher)

        self.assertNotIn("adapter.load_all_metadata()", load_source)
        self.assertNotIn("adapter.load_all_metadata()", watcher_source)
        self.assertIn("UserPresetsMetadataLoadWorker", load_source)

    def test_profile_commands_reuse_service_cache(self) -> None:
        source = inspect.getsource(profile_commands._profile_preset_service)

        self.assertIn("_preset_service_cache", source)
        self.assertIn("cache[key]", source)

    def test_profile_service_has_selected_preset_snapshot(self) -> None:
        source = inspect.getsource(ProfilePresetService.load_selected_preset)

        self.assertIn("_selected_preset_snapshot", source)
        self.assertIn("_selected_preset_revision", source)

    def test_profile_setup_page_loads_profile_payload_through_worker(self) -> None:
        source = inspect.getsource(ProfileSetupPageBase.reload_current_profile)

        self.assertNotIn("self._controller.load(", source)
        self.assertIn("_request_profile_setup_payload", source)

    def test_preset_selection_state_uses_profile_snapshot(self) -> None:
        source = inspect.getsource(preset_commands._profile_selection_details)

        self.assertNotIn(".list_profiles(", source)
        self.assertNotIn("get_profile_setup(", source)
        self.assertIn("get_profile_selection_details", source)

    def test_control_pages_use_cached_profile_count(self) -> None:
        zapret2_source = inspect.getsource(Zapret2ModeControlPage._load_enabled_profile_count)
        zapret1_source = inspect.getsource(Zapret1ModeControlPage._load_enabled_profile_count)

        self.assertNotIn("count_enabled_profiles", zapret2_source)
        self.assertNotIn("count_enabled_profiles", zapret1_source)
        self.assertIn("get_enabled_profile_count_snapshot", zapret2_source)
        self.assertIn("get_enabled_profile_count_snapshot", zapret1_source)

    def test_raw_preset_editor_loads_file_through_worker(self) -> None:
        source = inspect.getsource(PresetRawEditorPage._load_file)

        self.assertNotIn("self._controller.load_text(", source)
        self.assertIn("_request_raw_preset_text", source)

    def test_lists_pages_load_text_through_worker(self) -> None:
        methods = (
            HostlistPage._load_domains,
            HostlistPage._load_ips,
            HostlistPage._load_exclusions,
            HostlistPage._load_ipru_exclusions,
            CustomDomainsPage._load_domains,
            CustomIpSetPage._load_entries,
            NetrogatPage._load,
        )

        for method in methods:
            source = inspect.getsource(method)
            self.assertNotIn("load_text(", source)
            self.assertIn("request_editor_text", source)


if __name__ == "__main__":
    unittest.main()
