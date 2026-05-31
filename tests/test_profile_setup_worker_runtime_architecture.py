from __future__ import annotations

import inspect
import unittest


class ProfileSetupWorkerRuntimeArchitectureTests(unittest.TestCase):
    def test_profile_setup_load_workers_start_through_runtime(self) -> None:
        from profile.ui.profile_setup_page import ProfileSetupPageBase

        init_source = inspect.getsource(ProfileSetupPageBase.__init__)
        payload_source = inspect.getsource(ProfileSetupPageBase._request_profile_setup_payload)
        list_source = inspect.getsource(ProfileSetupPageBase._request_list_file_editor_state)
        cleanup_source = inspect.getsource(ProfileSetupPageBase.cleanup)

        self.assertIn("_setup_load_runtime = OneShotWorkerRuntime()", init_source)
        self.assertIn("_list_file_load_runtime = OneShotWorkerRuntime()", init_source)
        self.assertIn('_worker_runtime("_setup_load_runtime")', payload_source)
        self.assertIn('_worker_runtime("_list_file_load_runtime")', list_source)
        self.assertIn("start_qthread_worker", payload_source)
        self.assertIn("start_qthread_worker", list_source)
        self.assertNotIn("worker.start()", payload_source)
        self.assertNotIn("worker.start()", list_source)
        self.assertNotIn("self._setup_load_worker", init_source)
        self.assertNotIn("self._list_file_load_worker", init_source)
        self.assertIn("_setup_load_runtime", cleanup_source)
        self.assertIn("_list_file_load_runtime", cleanup_source)


if __name__ == "__main__":
    unittest.main()
