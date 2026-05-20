"""Build-helper верхней части страницы BlobsPage."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from qfluentwidgets import BreadcrumbBar, FluentIcon

from ui.fluent_widgets import (
    SettingsCard,
    QuickActionsBar,
    RefreshButton,
    insert_widget_into_setting_card_group,
)

@dataclass(slots=True)
class BlobsPageHeaderWidgets:
    breadcrumb: BreadcrumbBar
    desc_label: object
    actions_group: object | None
    actions_meta_card: object | None
    actions_bar: object | None
    add_btn: object
    reload_btn: object
    open_folder_btn: object
    open_json_btn: object
    count_label: object
    filter_icon_label: object
    filter_edit: object
    blobs_container: object
    blobs_layout: object


def build_blobs_page_header(
    *,
    page,
    setting_card_group_cls,
    line_edit_cls,
    action_button_cls,
    primary_action_button_cls,
    quick_actions_bar_cls,
    refresh_button_cls,
    add_widget,
    tr_fn,
    on_back,
    on_add_blob,
    on_reload_blobs,
    on_open_bin_folder,
    on_open_json,
    on_filter_blobs,
) -> BlobsPageHeaderWidgets:
    breadcrumb = BreadcrumbBar(page)
    breadcrumb.addItem("control", tr_fn("page.blobs.breadcrumb.control", "Управление"))
    breadcrumb.addItem("blobs", tr_fn("page.blobs.title", "Блобы"))
    breadcrumb.currentItemChanged.connect(lambda key: on_back() if key == "control" else None)
    page.vBoxLayout.insertWidget(0, breadcrumb)

    desc_card = SettingsCard()
    desc_label = QLabel(
        tr_fn(
            "page.blobs.description",
            "Блобы — это бинарные данные (файлы .bin или hex-значения), используемые в стратегиях для имитации TLS/QUIC пакетов.\nВы можете добавлять свои блобы для кастомных стратегий.",
        )
    )
    desc_label.setWordWrap(True)
    desc_card.add_widget(desc_label)
    add_widget(desc_card)

    actions_group = None
    actions_meta_card = None
    actions_bar = None

    actions_group = setting_card_group_cls(
        tr_fn("page.blobs.section.actions", "Действия"),
        page.content,
    )
    actions_bar = quick_actions_bar_cls(page.content)

    add_btn = primary_action_button_cls(
        tr_fn("page.blobs.button.add", "Добавить блоб"),
        icon=FluentIcon.ADD,
    )
    add_btn.clicked.connect(on_add_blob)

    reload_btn = refresh_button_cls()
    reload_btn.clicked.connect(on_reload_blobs)

    open_folder_btn = action_button_cls(
        tr_fn("page.blobs.button.bin_folder", "Папка bin"),
        icon=FluentIcon.FOLDER,
    )
    open_folder_btn.clicked.connect(on_open_bin_folder)

    open_json_btn = action_button_cls(
        tr_fn("page.blobs.button.open_json", "Открыть JSON"),
        icon=FluentIcon.DOCUMENT,
    )
    open_json_btn.clicked.connect(on_open_json)

    actions_bar.add_buttons([add_btn, reload_btn, open_folder_btn, open_json_btn])
    insert_widget_into_setting_card_group(actions_group, 1, actions_bar)

    actions_meta_card = SettingsCard()
    count_label = QLabel("")
    actions_meta_card.add_widget(count_label)
    actions_group.addSettingCard(actions_meta_card)
    add_widget(actions_group)

    filter_card = SettingsCard()
    filter_layout = QHBoxLayout()
    filter_layout.setSpacing(8)

    filter_icon_label = QLabel()
    filter_layout.addWidget(filter_icon_label)

    filter_edit = line_edit_cls()
    filter_edit.setPlaceholderText(tr_fn("page.blobs.filter.placeholder", "Фильтр по имени..."))
    filter_edit.textChanged.connect(on_filter_blobs)
    filter_layout.addWidget(filter_edit, 1)

    filter_card.add_layout(filter_layout)
    add_widget(filter_card)

    blobs_container = QWidget()
    blobs_container.setStyleSheet("background: transparent;")
    blobs_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    from PyQt6.QtWidgets import QVBoxLayout

    blobs_layout = QVBoxLayout(blobs_container)
    blobs_layout.setContentsMargins(0, 0, 0, 0)
    blobs_layout.setSpacing(6)
    add_widget(blobs_container)

    return BlobsPageHeaderWidgets(
        breadcrumb=breadcrumb,
        desc_label=desc_label,
        actions_group=actions_group,
        actions_meta_card=actions_meta_card,
        actions_bar=actions_bar,
        add_btn=add_btn,
        reload_btn=reload_btn,
        open_folder_btn=open_folder_btn,
        open_json_btn=open_json_btn,
        count_label=count_label,
        filter_icon_label=filter_icon_label,
        filter_edit=filter_edit,
        blobs_container=blobs_container,
        blobs_layout=blobs_layout,
    )
