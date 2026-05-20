"""Build-helper shell страницы профилей."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from ui.fluent_widgets import QuickActionsBar, set_tooltip
from qfluentwidgets import BodyLabel, FluentIcon, PrimaryPushButton, PushButton


@dataclass(slots=True)
class ProfileShellWidgets:
    toolbar_actions_bar: object
    request_btn: object
    expand_btn: object
    collapse_btn: object
    info_btn: object
    content_host: object
    content_host_layout: object
    loading_label: object


def build_profile_shell(
    *,
    content_parent,
    content_layout,
    add_section_title,
    tr_fn,
    engine_label: str,
    toolbar_title_key: str,
    request_button_key: str,
    request_hint_key: str,
    loading_key: str,
    on_open_profile_request_form,
    on_expand_all,
    on_collapse_all,
    on_show_info_popup,
) -> ProfileShellWidgets:
    toolbar_key_prefix = str(toolbar_title_key or "").rsplit(".", 1)[0]

    def _toolbar_key(name: str) -> str:
        if toolbar_key_prefix:
            return f"{toolbar_key_prefix}.{name}"
        return f"page.winws2_pages.toolbar.{name}"

    add_section_title(text_key=toolbar_title_key)
    toolbar_actions_bar = QuickActionsBar(content_parent)

    request_btn = PrimaryPushButton(
        tr_fn(request_button_key, "ОТКРЫТЬ ФОРМУ НА GITHUB"),
        icon=FluentIcon.GITHUB,
    )
    request_btn.clicked.connect(on_open_profile_request_form)
    set_tooltip(
        request_btn,
        tr_fn(
            request_hint_key,
            f"Хотите добавить новый сайт или сервис в {engine_label}? Откройте готовую форму на GitHub и опишите, что нужно добавить в hostlist или ipset.",
        )
    )
    toolbar_actions_bar.add_button(request_btn)

    expand_btn = PushButton(
        tr_fn(_toolbar_key("expand"), "Развернуть"),
        icon=FluentIcon.FULL_SCREEN,
    )
    expand_btn.clicked.connect(on_expand_all)
    set_tooltip(
        expand_btn,
        tr_fn(
            _toolbar_key("expand.description"),
            "Развернуть все группы профилей в списке.",
        )
    )
    toolbar_actions_bar.add_button(expand_btn)

    collapse_btn = PushButton(
        tr_fn(_toolbar_key("collapse"), "Свернуть"),
        icon=FluentIcon.BACK_TO_WINDOW,
    )
    collapse_btn.clicked.connect(on_collapse_all)
    set_tooltip(
        collapse_btn,
        tr_fn(
            _toolbar_key("collapse.description"),
            "Свернуть все группы профилей в списке.",
        )
    )
    toolbar_actions_bar.add_button(collapse_btn)

    info_btn = PushButton(
        tr_fn(_toolbar_key("info"), "Что это такое?"),
        icon=FluentIcon.QUESTION,
    )
    info_btn.clicked.connect(on_show_info_popup)
    set_tooltip(
        info_btn,
        tr_fn(
            _toolbar_key("info.description"),
            f"Показать краткое объяснение по работе режима профилей {engine_label}.",
        )
    )
    toolbar_actions_bar.add_button(info_btn)
    content_layout.addWidget(toolbar_actions_bar)

    content_host = QWidget(content_parent)
    content_host_layout = QVBoxLayout(content_host)
    content_host_layout.setContentsMargins(0, 0, 0, 0)
    content_host_layout.setSpacing(8)

    loading_label = BodyLabel(
        tr_fn(loading_key, "Загрузка профилей выбранного пресета...")
    )
    loading_label.setWordWrap(True)
    loading_label.hide()
    content_host_layout.addWidget(loading_label)

    content_layout.addWidget(content_host, 1)

    return ProfileShellWidgets(
        toolbar_actions_bar=toolbar_actions_bar,
        request_btn=request_btn,
        expand_btn=expand_btn,
        collapse_btn=collapse_btn,
        info_btn=info_btn,
        content_host=content_host,
        content_host_layout=content_host_layout,
        loading_label=loading_label,
    )
