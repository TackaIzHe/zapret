from __future__ import annotations

import inspect
import unittest


class Zapret2ControlLazyStartupTests(unittest.TestCase):
    def test_deferred_build_helpers_are_not_imported_on_page_module_import(self) -> None:
        import presets.ui.control.zapret2.page as zapret2_page

        module_source = inspect.getsource(zapret2_page)
        import_block = "\n".join(module_source.splitlines()[:80])
        deferred_source = inspect.getsource(zapret2_page.Zapret2ModeControlPage._build_deferred_sections)

        self.assertNotIn("from presets.ui.control.zapret2.deferred_build import", import_block)
        self.assertIn("from presets.ui.control.zapret2.deferred_build import", deferred_source)

    def test_additional_settings_workers_are_imported_only_when_requested(self) -> None:
        import presets.ui.control.zapret2.page as zapret2_page

        module_source = inspect.getsource(zapret2_page)
        import_block = "\n".join(module_source.splitlines()[:90])
        reload_source = inspect.getsource(zapret2_page.Zapret2ModeControlPage._schedule_additional_settings_reload)
        save_source = inspect.getsource(zapret2_page.Zapret2ModeControlPage._request_additional_settings_save)

        self.assertNotIn("create_additional_settings_worker as create_control_additional_settings_worker", import_block)
        self.assertIn("create_additional_settings_worker as create_control_additional_settings_worker", reload_source)
        self.assertIn("create_additional_settings_save_worker as create_control_additional_settings_save_worker", save_source)


if __name__ == "__main__":
    unittest.main()
