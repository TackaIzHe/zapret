# lists/ui/netrogat_page.py
"""Страница управления пользовательскими исключениями lists/user/netrogat.txt"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)
import qtawesome as qta

from qfluentwidgets import (
    BodyLabel, CaptionLabel, FluentIcon, InfoBar, LineEdit, MessageBox, SettingCardGroup,
    PrimaryPushButton, PushButton,
    StrongBodyLabel,
)

from ui.pages.base_page import BasePage, ScrollBlockingPlainTextEdit
from ui.fluent_widgets import (
    SettingsCard,
    QuickActionsBar,
    insert_widget_into_setting_card_group,
    set_tooltip,
)
from ui.theme import get_theme_tokens
from app.text_catalog import tr as tr_catalog
from log.log import log
from lists.editor_workflow import (
    ListsEditorController,
)



class NetrogatPage(BasePage):
    """Страница пользовательских исключений lists/user/netrogat.txt"""

    data_changed = pyqtSignal()

    def __init__(self, parent=None, *, lists_feature):
        super().__init__(
            "Исключения",
            "Управление пользовательским списком `lists/user/netrogat.txt`. Итоговый `lists/netrogat.txt` собирается автоматически.",
            parent,
            title_key="page.netrogat.title",
            subtitle_key="page.netrogat.subtitle",
        )
        self._lists_controller = ListsEditorController(lists_feature)
        self._desc_label = None
        self._add_card = None
        self._actions_card = None
        self._actions_group = None
        self._actions_bar = None
        self._editor_card = None
        self._hint_label = None
        self._add_defaults_btn = None
        self._open_btn = None
        self._open_final_btn = None
        self._clear_btn = None
        self._status_state = {
            "total": 0,
            "base": 0,
            "user": 0,
            "saved": False,
        }
        self._runtime_initialized = False
        self._cleanup_in_progress = False
        self._editor_load_request_seq = 0
        self._editor_load_worker = None
        self._build_ui()
        self._apply_page_theme(force=True)
        self._run_runtime_init_once()

    def _run_runtime_init_once(self) -> None:
        if self._runtime_initialized:
            return
        self._runtime_initialized = True
        QTimer.singleShot(0, lambda: (not self._cleanup_in_progress) and self._load())

    def _tr(self, key: str, default: str, **kwargs) -> str:
        text = tr_catalog(key, language=self._ui_language, default=default)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def _build_ui(self):
        tokens = get_theme_tokens()
        # Описание
        desc_card = SettingsCard()
        desc = CaptionLabel(
            self._tr(
                "page.netrogat.description",
                "Редактируйте только `lists/user/netrogat.txt`.\n"
                "Системная база хранится в `lists/base/netrogat.txt`, а итоговый `lists/netrogat.txt` собирается автоматически.",
            )
        )
        self._desc_label = desc
        desc.setStyleSheet(f"color: {tokens.fg_muted};")
        desc.setWordWrap(True)
        desc_card.add_widget(desc)
        self.layout.addWidget(desc_card)

        # Добавление домена
        add_card = SettingsCard(self._tr("page.netrogat.section.add", "Добавить домен"))
        self._add_card = add_card
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)

        self.input = LineEdit()
        self.input.setPlaceholderText(
            self._tr(
                "page.netrogat.input.placeholder",
                "Например: example.com, site.com или через пробел",
            )
        )
        self.input.returnPressed.connect(self._add)
        add_layout.addWidget(self.input, 1)

        self.add_btn = PrimaryPushButton(
            self._tr("page.netrogat.button.add", "Добавить"),
            icon=FluentIcon.ADD,
        )
        self.add_btn.setFixedHeight(38)
        self.add_btn.clicked.connect(self._add)
        add_layout.addWidget(self.add_btn)

        add_card.add_layout(add_layout)
        self.layout.addWidget(add_card)

        # Действия
        self._add_defaults_btn = None
        self._open_btn = None
        self._open_final_btn = None
        self._clear_btn = None
        self._actions_card = None
        actions_group = SettingCardGroup(
            self._tr("page.netrogat.section.actions", "Действия"),
            self.content,
        )
        self._actions_group = actions_group

        self._actions_bar = QuickActionsBar(self.content)

        self._add_defaults_btn = PrimaryPushButton(
            self._tr("page.netrogat.button.add_missing", "Добавить недостающие"),
            icon=FluentIcon.ADD,
        )
        self._add_defaults_btn.clicked.connect(self._add_missing_defaults)
        set_tooltip(
            self._add_defaults_btn,
            self._tr(
                "page.netrogat.action.add_missing.description",
                "Восстановить недостающие домены по умолчанию в системной базе netrogat.",
            ),
        )

        self._open_btn = PushButton(
            self._tr("page.netrogat.button.open_file", "Открыть файл"),
            icon=FluentIcon.LINK,
        )
        self._open_btn.clicked.connect(self._open_file)
        set_tooltip(
            self._open_btn,
            self._tr(
                "page.netrogat.action.open_file.description",
                "Сохраняет изменения и открывает `lists/user/netrogat.txt` в проводнике.",
            ),
        )

        self._open_final_btn = PushButton(
            self._tr("page.netrogat.button.open_final", "Открыть итоговый"),
            icon=FluentIcon.DOCUMENT,
        )
        self._open_final_btn.clicked.connect(self._open_final_file)
        set_tooltip(
            self._open_final_btn,
            self._tr(
                "page.netrogat.action.open_final.description",
                "Сохраняет изменения и открывает собранный итоговый файл netrogat.txt.",
            ),
        )

        self._clear_btn = PushButton(
            self._tr("page.netrogat.button.clear_all", "Очистить всё"),
            icon=FluentIcon.DELETE,
        )
        self._clear_btn.clicked.connect(self._clear_all)
        set_tooltip(
            self._clear_btn,
            self._tr(
                "page.netrogat.action.clear_all.description",
                "Удаляет все пользовательские домены из `lists/user/netrogat.txt`.",
            ),
        )

        self._actions_bar.add_buttons([
            self._add_defaults_btn,
            self._open_btn,
            self._open_final_btn,
            self._clear_btn,
        ])
        insert_widget_into_setting_card_group(actions_group, 1, self._actions_bar)
        self.layout.addWidget(actions_group)

        # Текстовый редактор (вместо списка)
        editor_card = SettingsCard(self._tr("page.netrogat.section.editor", "lists/user/netrogat.txt (редактор)"))
        self._editor_card = editor_card
        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(8)

        self.text_edit = ScrollBlockingPlainTextEdit()
        self.text_edit.setPlaceholderText(
            self._tr(
                "page.netrogat.editor.placeholder",
                "Домены по одному на строку:\n"
                "gosuslugi.ru\n"
                "vk.com\n\n"
                "Комментарии начинаются с #",
            )
        )
        self.text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {tokens.surface_bg};
                border: 1px solid {tokens.surface_border};
                border-radius: 8px;
                padding: 12px;
                color: {tokens.fg};
                font-family: Consolas, 'Courier New', monospace;
                font-size: 13px;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {tokens.accent_hex};
            }}
        """)
        self.text_edit.setMinimumHeight(350)

        # Автосохранение
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._auto_save)
        self.text_edit.textChanged.connect(self._on_text_changed)

        editor_layout.addWidget(self.text_edit)

        self._hint_label = CaptionLabel(
            self._tr("page.netrogat.hint.autosave", "💡 Изменения сохраняются автоматически через 500мс")
        )
        self._hint_label.setStyleSheet(f"color: {tokens.fg_faint};")
        editor_layout.addWidget(self._hint_label)

        editor_card.add_layout(editor_layout)
        self.layout.addWidget(editor_card)

        self.status_label = CaptionLabel()
        self.status_label.setStyleSheet(f"color: {tokens.fg_faint};")
        self.layout.addWidget(self.status_label)

    def _load(self):
        if self._cleanup_in_progress:
            return
        self._request_editor_text("netrogat")

    def _request_editor_text(self, kind: str) -> None:
        self._editor_load_request_seq += 1
        request_seq = self._editor_load_request_seq
        worker = self._lists_controller.create_text_load_worker(request_seq, kind, self)
        self._editor_load_worker = worker
        worker.loaded.connect(self._on_editor_text_loaded)
        worker.failed.connect(self._on_editor_text_failed)
        worker.finished.connect(lambda w=worker: self._on_editor_text_worker_finished(w))
        worker.start()

    def _on_editor_text_loaded(self, request_seq: int, _kind: str, state) -> None:
        if self._cleanup_in_progress or request_seq != self._editor_load_request_seq:
            return
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(state.text)
        self.text_edit.blockSignals(False)
        self._status_state["saved"] = False
        self._update_status()
        log(f"Загружено {state.lines_count} строк из lists/user/netrogat.txt", "INFO")

    def _on_editor_text_failed(self, request_seq: int, _kind: str, error: str) -> None:
        if self._cleanup_in_progress or request_seq != self._editor_load_request_seq:
            return
        log(f"Ошибка загрузки lists/user/netrogat.txt: {error}", "ERROR")
        self.status_label.setText(f"Ошибка загрузки: {error}")

    def _on_editor_text_worker_finished(self, worker) -> None:
        if self._editor_load_worker is worker:
            self._editor_load_worker = None
        worker.deleteLater()

    def _render_status_label(self):
        summary = self._tr(
            "page.netrogat.status.summary",
            "📊 Доменов: {total} (база: {base}, пользовательские: {user})",
            total=self._status_state["total"],
            base=self._status_state["base"],
            user=self._status_state["user"],
        )
        if self._status_state.get("saved"):
            summary += self._tr("page.netrogat.status.saved_suffix", " • ✅ Сохранено")
        self.status_label.setText(summary)

    def set_ui_language(self, language: str) -> None:
        super().set_ui_language(language)

        if self._desc_label is not None:
            self._desc_label.setText(
                self._tr(
                "page.netrogat.description",
                    "Редактируйте только `lists/user/netrogat.txt`.\n"
                    "Системная база хранится в `lists/base/netrogat.txt`, а итоговый `lists/netrogat.txt` собирается автоматически.",
                )
            )
        if self._add_card is not None:
            self._add_card.set_title(self._tr("page.netrogat.section.add", "Добавить домен"))
        if self._actions_card is not None:
            self._actions_card.set_title(self._tr("page.netrogat.section.actions", "Действия"))
        if self._actions_group is not None:
            try:
                self._actions_group.titleLabel.setText(self._tr("page.netrogat.section.actions", "Действия"))
            except Exception:
                pass
        if self._editor_card is not None:
            self._editor_card.set_title(self._tr("page.netrogat.section.editor", "lists/user/netrogat.txt (редактор)"))

        self.input.setPlaceholderText(
            self._tr(
                "page.netrogat.input.placeholder",
                "Например: example.com, site.com или через пробел",
            )
        )
        self.add_btn.setText(self._tr("page.netrogat.button.add", "Добавить"))
        if self._add_defaults_btn is not None:
            self._add_defaults_btn.setText(self._tr("page.netrogat.button.add_missing", "Добавить недостающие"))
            set_tooltip(
                self._add_defaults_btn,
                self._tr(
                    "page.netrogat.action.add_missing.description",
                    "Восстановить недостающие домены по умолчанию в системной базе netrogat.",
                )
            )
        if self._open_btn is not None:
            self._open_btn.setText(self._tr("page.netrogat.button.open_file", "Открыть файл"))
            set_tooltip(
                self._open_btn,
                self._tr(
                    "page.netrogat.action.open_file.description",
                    "Сохраняет изменения и открывает `lists/user/netrogat.txt` в проводнике.",
                )
            )
        if self._open_final_btn is not None:
            self._open_final_btn.setText(self._tr("page.netrogat.button.open_final", "Открыть итоговый"))
            set_tooltip(
                self._open_final_btn,
                self._tr(
                    "page.netrogat.action.open_final.description",
                    "Сохраняет изменения и открывает собранный итоговый файл netrogat.txt.",
                )
            )
        if self._clear_btn is not None:
            self._clear_btn.setText(self._tr("page.netrogat.button.clear_all", "Очистить всё"))
            set_tooltip(
                self._clear_btn,
                self._tr(
                    "page.netrogat.action.clear_all.description",
                    "Удаляет все пользовательские домены из `lists/user/netrogat.txt`.",
                )
            )

        self.text_edit.setPlaceholderText(
            self._tr(
                "page.netrogat.editor.placeholder",
                "Домены по одному на строку:\n"
                "gosuslugi.ru\n"
                "vk.com\n\n"
                "Комментарии начинаются с #",
            )
        )
        if self._hint_label is not None:
            self._hint_label.setText(
                self._tr("page.netrogat.hint.autosave", "💡 Изменения сохраняются автоматически через 500мс")
            )

        self._render_status_label()

    def _on_text_changed(self):
        if self._cleanup_in_progress:
            return
        self._save_timer.start(500)
        self._status_state["saved"] = False
        self._update_status()

    def _auto_save(self):
        if self._cleanup_in_progress:
            return
        self._save()
        self._status_state["saved"] = True
        self._render_status_label()

    def _save(self):
        text = self.text_edit.toPlainText()
        state = self._lists_controller.save_text("netrogat", text)
        if state.success:
            # Обновляем UI - заменяем URL на домены
            new_text = state.normalized_text
            if new_text != text:
                cursor = self.text_edit.textCursor()
                pos = cursor.position()
                
                self.text_edit.blockSignals(True)
                self.text_edit.setPlainText(new_text)
                
                # Восстанавливаем позицию курсора
                cursor = self.text_edit.textCursor()
                cursor.setPosition(min(pos, len(new_text)))
                self.text_edit.setTextCursor(cursor)
                self.text_edit.blockSignals(False)
            
            self.data_changed.emit()
            return

        log("Не удалось сохранить lists/user/netrogat.txt или синхронизировать итоговый lists/netrogat.txt", "ERROR")

    def _update_status(self):
        if self._cleanup_in_progress:
            return
        plan = self._lists_controller.status_plan("netrogat", self.text_edit.toPlainText())
        self._status_state["total"] = plan.total_count
        self._status_state["base"] = plan.base_count
        self._status_state["user"] = plan.user_count
        self._render_status_label()

    def _add(self):
        plan = self._lists_controller.add_entry_plan(
            "netrogat",
            raw_text=self.input.text().strip(),
            current_text=self.text_edit.toPlainText(),
        )
        if plan.new_text is None and plan.level is None:
            return

        if plan.level == "warning":
            if InfoBar:
                InfoBar.warning(
                    title=self._tr("common.error.title", "Ошибка"),
                    content=plan.content,
                    parent=self.window(),
                )
            return
        if plan.level == "info":
            if InfoBar:
                InfoBar.info(
                    title=self._tr("page.netrogat.infobar.info_title", "Информация"),
                    content=plan.content,
                    parent=self.window(),
                )
            return
        self.text_edit.setPlainText(plan.new_text or "")
        if plan.clear_input:
            self.input.clear()
        if plan.level == "success":
            if InfoBar:
                InfoBar.success(
                    title=plan.title,
                    content=plan.content,
                    parent=self.window(),
                )

    def _clear_all(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        if MessageBox:
            box = MessageBox(
                self._tr("page.netrogat.dialog.clear.title", "Очистить всё"),
                self._tr("page.netrogat.dialog.clear.body", "Удалить все домены?"),
                self.window(),
            )
            if box.exec():
                self.text_edit.clear()
                log("Очистили lists/user/netrogat.txt", "INFO")
        else:
            self.text_edit.clear()
            log("Очистили lists/user/netrogat.txt", "INFO")

    def _open_file(self):
        try:
            # Сохраняем перед открытием
            self._save()
            self._lists_controller.open_user_file("netrogat")
        except Exception as e:
            log(f"Ошибка открытия lists/user/netrogat.txt: {e}", "ERROR")
            if InfoBar:
                InfoBar.warning(
                    title=self._tr("common.error.title", "Ошибка"),
                    content=self._tr("page.netrogat.error.open_file", "Не удалось открыть: {error}", error=e),
                    parent=self.window(),
                )

    def _open_final_file(self):
        try:
            # Сохраняем user и пересобираем итог перед открытием
            self._save()
            self._lists_controller.open_final_file("netrogat")
        except Exception as e:
            log(f"Ошибка открытия итогового netrogat.txt: {e}", "ERROR")
            if InfoBar:
                InfoBar.warning(
                    title=self._tr("common.error.title", "Ошибка"),
                    content=self._tr(
                        "page.netrogat.error.open_final_file",
                        "Не удалось открыть итоговый файл: {error}",
                        error=e,
                    ),
                    parent=self.window(),
                )

    def _add_missing_defaults(self):
        self._save()
        added = self._lists_controller.add_missing_netrogat_defaults()
        if added == 0:
            if InfoBar:
                InfoBar.success(
                    title=self._tr("page.netrogat.infobar.done_title", "Готово"),
                    content=self._tr(
                        "page.netrogat.info.defaults_already_present",
                        "Системная база уже содержит все домены по умолчанию.",
                    ),
                    parent=self.window(),
                )
            return

        self._update_status()
        if InfoBar:
            InfoBar.success(
                title=self._tr("page.netrogat.infobar.done_title", "Готово"),
                content=self._tr(
                    "page.netrogat.info.defaults_restored",
                    "Восстановлено доменов в системной базе: {count}",
                    count=added,
                ),
                parent=self.window(),
            )

    def cleanup(self) -> None:
        self._cleanup_in_progress = True
        try:
            self._save_timer.stop()
        except Exception:
            pass
