import inspect
import unittest

import log.log as log_module


class LegacyLogViewerRuntimeTest(unittest.TestCase):
    def test_legacy_log_viewer_tail_uses_shared_runtime(self) -> None:
        source = inspect.getsource(log_module._build_log_viewer_dialog_class)

        self.assertIn("OneShotWorkerRuntime", source)
        self.assertIn("_tail_runtime = OneShotWorkerRuntime()", source)
        self.assertIn("_tail_runtime.start_qobject_worker", source)
        self.assertIn("_tail_runtime.stop", source)
        self.assertNotIn("QThread", source)
        self.assertNotIn("moveToThread", source)
        self.assertNotIn("thread.start()", source)
        self.assertNotIn("self._thread", source)
        self.assertNotIn("self._worker", source)


if __name__ == "__main__":
    unittest.main()
