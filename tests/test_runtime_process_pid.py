import unittest
from types import SimpleNamespace

from app.feature_facades.runtime_parts import RuntimeObjects


class _RuntimeService:
    def snapshot(self):
        return SimpleNamespace()

    def observe_process_details(self, details):
        self.details = details


class _ProcessMonitorManager:
    def __init__(self, details):
        self.details = details
        self.refresh_count = 0

    def refresh_now(self):
        self.refresh_count += 1
        return self.details


class RuntimeProcessPidTests(unittest.TestCase):
    def test_current_process_pid_refreshes_and_resolves_winws2(self) -> None:
        manager = _ProcessMonitorManager({"winws2.exe": [2222]})
        objects = RuntimeObjects(runtime_service=_RuntimeService(), process_monitor_manager=manager)
        objects.process_details = {"winws2.exe": [1111]}

        pid = objects.current_process_pid("zapret2_mode", refresh=True)

        self.assertEqual(pid, 2222)
        self.assertEqual(manager.refresh_count, 1)
        self.assertEqual(objects.process_details, {"winws2.exe": [2222]})

    def test_current_process_pid_refreshes_and_resolves_winws1(self) -> None:
        manager = _ProcessMonitorManager({"winws.exe": [1111], "winws2.exe": [2222]})
        objects = RuntimeObjects(runtime_service=_RuntimeService(), process_monitor_manager=manager)

        pid = objects.current_process_pid("zapret1_mode", refresh=True)

        self.assertEqual(pid, 1111)
        self.assertEqual(manager.refresh_count, 1)


if __name__ == "__main__":
    unittest.main()
