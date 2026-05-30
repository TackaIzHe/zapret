from __future__ import annotations

import inspect
import unittest


class ProfileListViewStateWorkerTests(unittest.TestCase):
    def test_profile_list_worker_builds_view_state_off_gui_thread(self) -> None:
        from profile.profile_list_loader import ProfileListLoadWorker

        init_source = inspect.getsource(ProfileListLoadWorker.__init__)
        run_source = inspect.getsource(ProfileListLoadWorker.run)

        self.assertIn("build_view_state", init_source)
        self.assertIn("self._build_view_state", run_source)
        self.assertIn("ProfileListLoadResult", run_source)

    def test_preset_setup_page_applies_worker_view_state_to_profile_list(self) -> None:
        from profile.ui.preset_setup_page import PresetSetupPageBase

        apply_source = inspect.getsource(PresetSetupPageBase._apply_payload)

        self.assertIn("view_state", apply_source)
        self.assertIn("apply_view_state", apply_source)
        self.assertNotIn("profiles_list.build_profiles(tuple(payload.items))", apply_source)


if __name__ == "__main__":
    unittest.main()
