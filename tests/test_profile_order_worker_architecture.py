from __future__ import annotations

import inspect
import unittest


class ProfileOrderWorkerArchitectureTests(unittest.TestCase):
    def test_profile_order_load_worker_receives_narrow_profile_service(self) -> None:
        from profile.profile_order_loader import ProfileOrderListLoadWorker

        init_source = inspect.getsource(ProfileOrderListLoadWorker.__init__)
        run_source = inspect.getsource(ProfileOrderListLoadWorker.run)

        self.assertIn("profile_service", init_source)
        self.assertIn("self._service", init_source)
        self.assertNotIn("self._profile", init_source)
        self.assertNotIn("launch_method", init_source)
        self.assertIn("self._service.list_preset_order_profiles()", run_source)
        self.assertNotIn("self._profile.list_preset_order_profiles", run_source)

    def test_profile_order_move_worker_receives_narrow_profile_service(self) -> None:
        from profile.profile_order_loader import ProfilePresetOrderMoveWorker

        init_source = inspect.getsource(ProfilePresetOrderMoveWorker.__init__)
        run_source = inspect.getsource(ProfilePresetOrderMoveWorker.run)

        self.assertIn("profile_service", init_source)
        self.assertIn("self._service", init_source)
        self.assertNotIn("self._profile", init_source)
        self.assertNotIn("launch_method", init_source)
        self.assertIn("self._service.move_preset_profile_before", run_source)
        self.assertIn("self._service.move_preset_profile_after", run_source)
        self.assertIn("self._service.move_preset_profile_to_end", run_source)
        self.assertNotIn("self._profile.move_preset_profile", run_source)


if __name__ == "__main__":
    unittest.main()
