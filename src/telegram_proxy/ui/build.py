"""Build-helper shell и простых панелей Telegram Proxy page."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget

from ui.pages.base_page import ScrollBlockingPlainTextEdit
from ui.log_limits import (
    TELEGRAM_PROXY_DIAG_VIEW_MAX_LINES,
    TELEGRAM_PROXY_LOG_VIEW_MAX_LINES,
    apply_text_line_limit,
)
from ui.widgets.action_button import apply_themed_action_button


@dataclass(slots=True)
class TelegramProxyShellWidgets:
    pivot: object
    stacked: QStackedWidget
    settings_panel: QWidget
    settings_layout: QVBoxLayout
    logs_panel: QWidget
    logs_layout: QVBoxLayout
    diag_panel: QWidget
    diag_layout: QVBoxLayout


@dataclass(slots=True)
class TelegramProxyLogsWidgets:
    btn_copy_logs: object
    btn_open_log_file: object
    btn_clear_logs: object
    log_edit: object


@dataclass(slots=True)
class TelegramProxyDiagWidgets:
    diag_desc_label: object
    btn_run_diag: object
    btn_copy_diag: object
    diag_edit: object


def build_telegram_proxy_shell(*, segmented_widget_cls, parent, on_switch_tab) -> TelegramProxyShellWidgets:
    pivot = segmented_widget_cls(parent)
    stacked = QStackedWidget(parent)

    settings_panel = QWidget(stacked)
    settings_layout = QVBoxLayout(settings_panel)
    settings_layout.setContentsMargins(0, 0, 0, 0)
    settings_layout.setSpacing(12)
    stacked.addWidget(settings_panel)

    logs_panel = QWidget(stacked)
    logs_layout = QVBoxLayout(logs_panel)
    logs_layout.setContentsMargins(0, 0, 0, 0)
    logs_layout.setSpacing(8)
    stacked.addWidget(logs_panel)

    diag_panel = QWidget(stacked)
    diag_layout = QVBoxLayout(diag_panel)
    diag_layout.setContentsMargins(0, 0, 0, 0)
    diag_layout.setSpacing(8)
    stacked.addWidget(diag_panel)

    pivot.addItem("settings", "Настройки", lambda: on_switch_tab(0))
    pivot.addItem("logs", "Логи", lambda: on_switch_tab(1))
    pivot.addItem("diag", "Диагностика", lambda: on_switch_tab(2))
    pivot.setCurrentItem("settings")

    return TelegramProxyShellWidgets(
        pivot=pivot,
        stacked=stacked,
        settings_panel=settings_panel,
        settings_layout=settings_layout,
        logs_panel=logs_panel,
        logs_layout=logs_layout,
        diag_panel=diag_panel,
        diag_layout=diag_layout,
    )


def build_telegram_proxy_logs_panel(
    layout: QVBoxLayout,
    *,
    push_button_cls,
    on_copy_all_logs,
    on_open_log_file,
    on_clear_logs,
) -> TelegramProxyLogsWidgets:
    toolbar = QHBoxLayout()
    toolbar.setSpacing(8)

    btn_copy_logs = push_button_cls()
    btn_copy_logs.setText("Копировать все")
    apply_themed_action_button(btn_copy_logs, icon_name="mdi.content-copy", alignment="left")
    btn_copy_logs.clicked.connect(on_copy_all_logs)
    toolbar.addWidget(btn_copy_logs)

    btn_open_log_file = push_button_cls()
    btn_open_log_file.setText("Открыть файл лога")
    apply_themed_action_button(btn_open_log_file, icon_name="fa5s.file-alt", alignment="left")
    btn_open_log_file.clicked.connect(on_open_log_file)
    toolbar.addWidget(btn_open_log_file)

    btn_clear_logs = push_button_cls()
    btn_clear_logs.setText("Очистить")
    apply_themed_action_button(btn_clear_logs, icon_name="fa5s.eraser", alignment="left")
    btn_clear_logs.clicked.connect(on_clear_logs)
    toolbar.addWidget(btn_clear_logs)

    toolbar.addStretch()
    layout.addLayout(toolbar)

    log_edit = ScrollBlockingPlainTextEdit()
    log_edit.setReadOnly(True)
    log_edit.setPlaceholderText("Лог подключений появится здесь...")
    apply_text_line_limit(log_edit, TELEGRAM_PROXY_LOG_VIEW_MAX_LINES)
    layout.addWidget(log_edit)

    return TelegramProxyLogsWidgets(
        btn_copy_logs=btn_copy_logs,
        btn_open_log_file=btn_open_log_file,
        btn_clear_logs=btn_clear_logs,
        log_edit=log_edit,
    )


def build_telegram_proxy_diag_panel(
    layout: QVBoxLayout,
    *,
    caption_label_cls,
    primary_push_button_cls,
    push_button_cls,
    on_run_diagnostics,
    on_copy_diag,
) -> TelegramProxyDiagWidgets:
    desc = caption_label_cls(
        "Проверка соединений к Telegram DC, WSS relay эндпоинтов (kws1-kws5), "
        "SOCKS5 прокси и определение типа блокировки."
    )
    desc.setWordWrap(True)
    layout.addWidget(desc)

    toolbar = QHBoxLayout()
    toolbar.setSpacing(8)

    btn_run_diag = primary_push_button_cls()
    btn_run_diag.setText("Запустить диагностику")
    apply_themed_action_button(btn_run_diag, icon_name="fa5s.stethoscope", alignment="left")
    btn_run_diag.clicked.connect(on_run_diagnostics)
    toolbar.addWidget(btn_run_diag)

    btn_copy_diag = push_button_cls()
    btn_copy_diag.setText("Копировать результат")
    apply_themed_action_button(btn_copy_diag, icon_name="mdi.content-copy", alignment="left")
    btn_copy_diag.clicked.connect(on_copy_diag)
    toolbar.addWidget(btn_copy_diag)

    toolbar.addStretch()
    layout.addLayout(toolbar)

    diag_edit = ScrollBlockingPlainTextEdit()
    diag_edit.setReadOnly(True)
    diag_edit.setPlaceholderText("Нажмите 'Запустить диагностику'...")
    apply_text_line_limit(diag_edit, TELEGRAM_PROXY_DIAG_VIEW_MAX_LINES)
    layout.addWidget(diag_edit)

    return TelegramProxyDiagWidgets(
        diag_desc_label=desc,
        btn_run_diag=btn_run_diag,
        btn_copy_diag=btn_copy_diag,
        diag_edit=diag_edit,
    )
