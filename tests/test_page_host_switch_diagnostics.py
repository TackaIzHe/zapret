from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_SRC = Path(__file__).resolve().parent.parent / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class SwitchDiagnosticsSafetyTests(unittest.TestCase):
    """Диагностика переключения не имеет права ломать само переключение.

    Регрессия 21.1.2.3: cProfile в этом приложении падает на импорте (наш пакет
    src/profile затеняет stdlib profile), из-за чего первые 8 кликов по вкладкам
    молча не открывали страницы.
    """

    def test_callback_runs_exactly_once_when_diagnostics_break(self) -> None:
        from ui import page_host

        calls: list[int] = []
        with patch.object(page_host, "_SwitchTracer", side_effect=RuntimeError("boom")):
            page_host._profile_switch_call("TEST", lambda: calls.append(1))

        self.assertEqual(calls, [1])

    def test_callback_runs_exactly_once_on_happy_path(self) -> None:
        from ui import page_host

        calls: list[int] = []
        page_host._profile_switch_call("TEST", lambda: calls.append(1))

        self.assertEqual(calls, [1])

    def test_page_host_does_not_use_stdlib_cprofile(self) -> None:
        from ui import page_host

        source = inspect.getsource(page_host)

        self.assertNotIn("import cProfile", source)
        self.assertNotIn("import pstats", source)

    def test_stdlib_cprofile_is_broken_by_profile_package_shadow(self) -> None:
        """Фиксируем сам факт конфликта: если он исчезнет (переименование пакета),
        этот тест напомнит, что можно вернуться на stdlib cProfile."""
        try:
            import cProfile  # noqa: F401
        except AttributeError:
            return
        self.skipTest("stdlib cProfile снова импортируется — конфликт пакета profile устранён")

    def test_tracer_reports_python_and_c_frames(self) -> None:
        from ui.page_host import _SwitchTracer

        tracer = _SwitchTracer()
        sys.setprofile(tracer)
        try:
            sorted([3, 1, 2])
            sum(range(1000))
        finally:
            sys.setprofile(None)

        report = tracer.report()
        self.assertIn("<C> ", report)


class StackedBackgroundGuardTests(unittest.TestCase):
    """Переполировка стека (setStyle ~180ms) не должна гоняться на каждом переключении.

    Библиотечный гвард сравнивает bool с None и потому никогда не срабатывает;
    наш override нормализует обе стороны к bool.
    """

    def _make_window(self, *, page_transparent, stack_transparent):
        from types import SimpleNamespace
        from unittest.mock import Mock

        from ui.fluent_app_window import ZapretFluentWindow

        window = ZapretFluentWindow.__new__(ZapretFluentWindow)
        window.stackedWidget = SimpleNamespace(
            currentWidget=Mock(return_value=SimpleNamespace(property=Mock(return_value=page_transparent))),
            property=Mock(return_value=stack_transparent),
            setProperty=Mock(),
            setStyle=Mock(),
        )
        return window

    def test_no_restyle_when_state_unchanged_none_vs_none(self) -> None:
        from ui.fluent_app_window import ZapretFluentWindow

        window = self._make_window(page_transparent=None, stack_transparent=None)
        ZapretFluentWindow._updateStackedBackground(window)
        window.stackedWidget.setStyle.assert_not_called()

    def test_restyle_runs_on_real_state_change(self) -> None:
        from ui.fluent_app_window import ZapretFluentWindow

        window = self._make_window(page_transparent=True, stack_transparent=None)
        ZapretFluentWindow._updateStackedBackground(window)
        window.stackedWidget.setStyle.assert_called_once()

    def test_override_exists_on_app_window(self) -> None:
        from ui.fluent_app_window import ZapretFluentWindow

        source = inspect.getsource(ZapretFluentWindow._updateStackedBackground)
        self.assertIn("bool(", source)


if __name__ == "__main__":
    unittest.main()
