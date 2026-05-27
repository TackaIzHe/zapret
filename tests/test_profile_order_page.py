from __future__ import annotations

import inspect
import unittest
from types import SimpleNamespace

from profile.state import ProfileListItem


def _item(name: str, *, key: str, in_preset: bool = True, profile_index: int = 0) -> ProfileListItem:
    return ProfileListItem(
        key=key,
        persistent_key=key,
        profile_index=profile_index,
        display_name=name,
        enabled=True,
        in_preset=in_preset,
        strategy_id="pass",
        strategy_name="pass",
        match_lines=("--filter-tcp=443", f"--hostlist=lists/{name.lower()}.txt"),
        list_type="hostlist",
        rating="",
        favorite=False,
        group="youtube",
        group_name="YouTube",
        order=profile_index,
        profile_name=name,
    )


class ProfileOrderPageTests(unittest.TestCase):
    def test_order_model_is_flat_and_keeps_only_real_preset_profiles(self) -> None:
        from profile.ui.profile_order_list import ProfileOrderListModel
        from profile.ui.profile_list_model import ProfileListModel

        model = ProfileOrderListModel()
        model.set_profiles((_item("YouTube", key="profile:0", profile_index=0), _item("Missing", key="template:0", in_preset=False)))

        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(ProfileListModel.KindRole), "profile")
        self.assertEqual(model.index(0, 0).data(ProfileListModel.ProfileKeyRole), "profile:0")
        self.assertEqual(model.index(0, 0).data(ProfileListModel.DisplayNameRole), "YouTube")

    def test_order_model_returns_icon_roles_from_profile_icon_spec(self) -> None:
        from profile.ui.profile_order_list import ProfileOrderListModel
        from profile.ui.profile_list_model import ProfileListModel

        model = ProfileOrderListModel()
        model.set_profiles((_item("YouTube", key="profile:0", profile_index=0),))

        index = model.index(0, 0)

        self.assertEqual(index.data(ProfileListModel.IconNameRole), "simple:youtube:YT")
        self.assertEqual(index.data(ProfileListModel.IconColorRole), "#FF0000")

    def test_order_page_explains_priority_and_uses_order_service_methods(self) -> None:
        from profile.ui.profile_order_page import ProfileOrderPageBase

        build_source = inspect.getsource(ProfileOrderPageBase._build_content)
        load_source = inspect.getsource(ProfileOrderPageBase._reload_order_profiles)
        before_source = inspect.getsource(ProfileOrderPageBase._on_profile_move_requested)
        after_source = inspect.getsource(ProfileOrderPageBase._on_profile_move_after_requested)
        end_source = inspect.getsource(ProfileOrderPageBase._on_profile_move_to_end_requested)

        self.assertIn("Profile выше в списке имеет больший приоритет", build_source)
        self.assertIn("list_preset_order_profiles", load_source)
        self.assertIn("move_preset_profile_before", before_source)
        self.assertIn("move_preset_profile_after", after_source)
        self.assertIn("move_preset_profile_to_end", end_source)
        self.assertIn("_reload_order_profiles()", before_source)
        self.assertIn("_reload_order_profiles()", after_source)
        self.assertIn("_reload_order_profiles()", end_source)

    def test_order_page_has_breadcrumbs_back_to_profiles_and_control(self) -> None:
        from profile.ui.profile_order_page import ProfileOrderPageBase

        build_source = inspect.getsource(ProfileOrderPageBase._build_content)
        breadcrumb_source = inspect.getsource(ProfileOrderPageBase._rebuild_breadcrumb)
        handler_source = inspect.getsource(ProfileOrderPageBase._on_breadcrumb_item_changed)

        self.assertIn("BreadcrumbBar", build_source)
        self.assertIn('"profiles"', breadcrumb_source)
        self.assertIn('"order"', breadcrumb_source)
        self.assertIn("_open_profiles()", handler_source)
        self.assertIn("_open_root()", handler_source)

    def test_order_list_does_not_expose_context_or_folder_actions(self) -> None:
        from profile.ui.profile_order_list import ProfileOrderList

        source = inspect.getsource(ProfileOrderList)

        self.assertNotIn("profile_context_requested", source)
        self.assertNotIn("folder_context_requested", source)
        self.assertNotIn("folder_toggled", source)


if __name__ == "__main__":
    unittest.main()
