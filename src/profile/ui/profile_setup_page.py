from __future__ import annotations

from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from log.log import log
from profile.winws2_editable_settings import normalize_winws2_filter_value
from profile.ui.profile_setup_controls import (
    range_expression_from_controls,
    set_combo_by_data,
    set_range_controls,
    sync_range_value_enabled,
)
from profile.setup_controller import ProfileSetupController
from qfluentwidgets import (
    BodyLabel,
    BreadcrumbBar,
    CheckBox,
    ComboBox,
    LineEdit,
    PlainTextEdit,
    PushButton,
    SearchLineEdit,
    SegmentedWidget,
    StrongBodyLabel,
    TitleLabel,
)
from settings.mode import ZAPRET1_MODE, ZAPRET2_MODE, is_zapret2_launch_method
from ui.pages.base_page import BasePage
from app.text_catalog import tr as tr_catalog
from ui.theme import get_theme_tokens, to_qcolor


class ProfileStrategyListDelegate(QStyledItemDelegate):
    """Рисует строки готовых стратегий в стиле списка «Мои пресеты»."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        tokens = get_theme_tokens()
        rect = option.rect.adjusted(8, 3, -8, -3)
        is_active = bool(index.data(ProfileStrategyListWidget._ROLE_IS_ACTIVE))
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        if is_active:
            bg = to_qcolor(
                tokens.accent_soft_bg_hover if (hovered or selected) else tokens.accent_soft_bg,
                tokens.accent_hex,
            )
        elif hovered or selected:
            bg = to_qcolor(tokens.surface_bg_hover, tokens.surface_bg)
        else:
            bg = to_qcolor(tokens.surface_bg, "#1f1f1f")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 10, 10)

        if is_active:
            marker_rect = QRect(rect.left() + 6, rect.top() + 7, 5, max(12, rect.height() - 14))
            painter.setBrush(to_qcolor(tokens.accent_hex, "#5caee8"))
            painter.drawRoundedRect(marker_rect, 2, 2)

        left = rect.left() + (24 if is_active else 18)
        right = rect.right() - 16
        status = str(index.data(ProfileStrategyListWidget._ROLE_STATUS_TEXT) or "")
        status_rect = QRect()

        font = painter.font()
        font.setBold(False)
        painter.setFont(font)
        metrics = QFontMetrics(font)

        if status:
            status_width = min(metrics.horizontalAdvance(status) + 18, max(0, rect.width() // 2))
            status_rect = QRect(right - status_width, rect.center().y() - 10, status_width, 20)
            right = status_rect.left() - 12

        name = str(index.data(ProfileStrategyListWidget._ROLE_NAME_TEXT) or "")
        name_rect = QRect(left, rect.top(), max(0, right - left), rect.height())
        painter.setPen(to_qcolor(tokens.fg, "#f5f5f5"))
        painter.drawText(
            name_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            metrics.elidedText(name, Qt.TextElideMode.ElideRight, name_rect.width()),
        )

        if status_rect.width() > 0:
            if is_active:
                badge_bg = to_qcolor(tokens.accent_soft_bg_hover, tokens.accent_hex)
                badge_fg = to_qcolor(tokens.accent_hex, "#5caee8")
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(badge_bg)
                painter.drawRoundedRect(status_rect, 9, 9)
                painter.setPen(badge_fg)
            else:
                painter.setPen(to_qcolor(tokens.fg_faint, "#aeb5c1"))
            painter.drawText(
                status_rect,
                int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
                metrics.elidedText(status, Qt.TextElideMode.ElideRight, max(0, status_rect.width() - 10)),
            )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        _ = (option, index)
        return QSize(0, 34)


class ProfileStrategyListWidget(QWidget):
    """Большой список готовых стратегий для profile."""

    strategy_activated = pyqtSignal(str)

    _ROLE_STRATEGY_ID = int(Qt.ItemDataRole.UserRole) + 1
    _ROLE_NAME_TEXT = int(Qt.ItemDataRole.UserRole) + 2
    _ROLE_STATUS_TEXT = int(Qt.ItemDataRole.UserRole) + 3
    _ROLE_IS_ACTIVE = int(Qt.ItemDataRole.UserRole) + 4

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_strategy_id = "none"
        self._entries = {}
        self._states = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        top_row = QWidget(self)
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self._search = SearchLineEdit(self)
        self._search.setPlaceholderText("Поиск по готовым стратегиям")
        self._search.textChanged.connect(self._apply_filter)
        top_layout.addWidget(self._search, 1)

        self._summary = BodyLabel("")
        top_layout.addWidget(self._summary)
        layout.addWidget(top_row)

        self._list = QListWidget(self)
        self._list.setItemDelegate(ProfileStrategyListDelegate(self._list))
        self._list.setUniformItemSizes(True)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.setMouseTracking(True)
        self._list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self._list.setMinimumHeight(520)
        self._list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._list.itemActivated.connect(self._on_item_activated)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.setStyleSheet(
            "QListWidget { background: transparent; border: none; outline: none; }"
            "QListWidget::item { border: none; padding: 0; }"
            "QListWidget::item:selected { background: transparent; }"
            "QListWidget::item:hover { background: transparent; }"
        )
        layout.addWidget(self._list, 1)

    def set_rows(self, *, entries, states, current_strategy_id: str) -> None:
        self._entries = dict(entries or {})
        self._states = dict(states or {})
        self._current_strategy_id = str(current_strategy_id or "none").strip() or "none"
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        search_text = self._search.text().strip().lower()
        self._list.clear()
        visible = 0
        current_item = None

        rows = list(self._entries.items())
        rows.sort(key=lambda pair: (
            not bool(getattr(self._states.get(pair[0]), "favorite", False)),
            str(getattr(pair[1], "name", "") or "").lower(),
        ))

        for strategy_id, entry in rows:
            name = str(getattr(entry, "name", "") or strategy_id)
            args = str(getattr(entry, "args", "") or "")
            if search_text and search_text not in name.lower() and search_text not in args.lower():
                continue

            item = QListWidgetItem()
            state = self._states.get(strategy_id)
            is_current = strategy_id == self._current_strategy_id
            status_parts = []
            if is_current:
                status_parts.append("Выбрана")
            if bool(getattr(state, "favorite", False)):
                status_parts.append("В избранном")
            rating = str(getattr(state, "rating", "") or "")
            if rating == "work":
                status_parts.append("Работает")
            elif rating == "notwork":
                status_parts.append("Не работает")

            item.setText(name)
            item.setData(self._ROLE_STRATEGY_ID, strategy_id)
            item.setData(self._ROLE_NAME_TEXT, name)
            item.setData(self._ROLE_STATUS_TEXT, " • ".join(status_parts))
            item.setData(self._ROLE_IS_ACTIVE, is_current)
            item.setToolTip(args)
            item.setSizeHint(QSize(0, 34))
            if is_current:
                current_item = item
            self._list.addItem(item)
            visible += 1

        self._summary.setText(f"{visible} из {len(self._entries)}")
        if current_item is not None:
            self._list.setCurrentItem(current_item)
            current_item.setSelected(True)

    def _apply_filter(self) -> None:
        self._rebuild_tree()

    def _strategy_id_for_item(self, item) -> str:
        return str(item.data(self._ROLE_STRATEGY_ID) or "").strip() if item is not None else ""

    def _on_item_clicked(self, item, _column: int) -> None:
        strategy_id = self._strategy_id_for_item(item)
        if strategy_id:
            self.strategy_activated.emit(strategy_id)

    def _on_item_activated(self, item, _column: int) -> None:
        strategy_id = self._strategy_id_for_item(item)
        if strategy_id:
            self.strategy_activated.emit(strategy_id)


def _section_label(text: str, parent=None) -> StrongBodyLabel:
    label = StrongBodyLabel(parent)
    label.setText(text)
    label.setProperty("tone", "primary")
    return label


class ProfileSetupPageBase(BasePage):
    profile_ui_mode_override: str | None = None
    launch_method = ZAPRET2_MODE
    title_key_name = "page.winws2_profile_setup.title"
    control_key = "page.winws2_profile_setup.breadcrumb.control"
    profiles_key = "page.winws2_pages.title"
    profiles_default = "Настройка пресета"

    def __init__(self, parent=None, *, profile_feature, open_profiles, open_root, on_profile_changed):
        super().__init__(
            title="",
            parent=parent,
            title_key=self.title_key_name,
        )
        self._controller = ProfileSetupController(
            profile_feature=profile_feature,
            launch_method=self.launch_method,
        )
        self._open_profiles = open_profiles
        self._open_root = open_root
        self._on_profile_changed_callback = on_profile_changed
        self._profile_key = ""
        self._loading = False
        self._payload = None
        self._profile_subpage = "profile"
        self._detail_strategy_id = ""
        self._main_widgets = []
        self._detail_widgets = []
        self._settings_title = None
        self._settings_container = None
        self._feedback_container = None
        self._open_feedback_button = None
        self._feedback_strategy_label = None
        self._feedback_status_label = None
        self._work_button = None
        self._notwork_button = None
        self._favorite_button = None
        self._clear_feedback_button = None
        self._settings_save_timer = QTimer(self)
        self._settings_save_timer.setSingleShot(True)
        self._settings_save_timer.setInterval(350)
        self._settings_save_timer.timeout.connect(self._autosave_editable_settings)
        self._build_content()

    def _build_content(self) -> None:
        if self.title_label is not None:
            self.title_label.hide()
        if self.subtitle_label is not None:
            self.subtitle_label.hide()

        self._breadcrumb = BreadcrumbBar()
        self._breadcrumb.currentItemChanged.connect(self._on_breadcrumb_item_changed)
        self.layout.addWidget(self._breadcrumb)

        self._title = TitleLabel("Профиль")
        self.layout.addWidget(self._title)

        self._summary = BodyLabel("")
        self._summary.setWordWrap(True)
        self.layout.addWidget(self._summary)

        controls = QWidget(self)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        self._enabled_checkbox = CheckBox("Включён")
        self._enabled_checkbox.stateChanged.connect(self._on_enabled_changed)
        controls_layout.addWidget(self._enabled_checkbox)
        controls_layout.addStretch(1)

        self.layout.addWidget(controls)
        self._main_widgets.append(controls)

        self._settings_container = QWidget(self)
        settings_layout = QHBoxLayout(self._settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        self._filter_combo = ComboBox()
        self._filter_combo.setMinimumWidth(150)
        self._filter_combo.addItem(tr_catalog("page.winws2_profile_setup.filter.hostlist", language=self._ui_language, default="Hostlist"), userData="hostlist")
        self._filter_combo.addItem(tr_catalog("page.winws2_profile_setup.filter.ipset", language=self._ui_language, default="IPset"), userData="ipset")
        settings_layout.addWidget(self._filter_combo)

        self._filter_value = LineEdit()
        self._filter_value.setMinimumWidth(260)
        self._filter_value.setPlaceholderText("lists/example.txt")
        settings_layout.addWidget(self._filter_value, 1)

        self._in_range_mode = ComboBox()
        self._in_range_mode.setMinimumWidth(86)
        self._fill_range_combo(self._in_range_mode)
        settings_layout.addWidget(BodyLabel("--in-range"))
        settings_layout.addWidget(self._in_range_mode)

        self._in_range_value = LineEdit()
        self._in_range_value.setMinimumWidth(90)
        self._in_range_value.setPlaceholderText("8")
        settings_layout.addWidget(self._in_range_value)

        self._out_range_mode = ComboBox()
        self._out_range_mode.setMinimumWidth(86)
        self._fill_range_combo(self._out_range_mode)
        settings_layout.addWidget(BodyLabel("--out-range"))
        settings_layout.addWidget(self._out_range_mode)

        self._out_range_value = LineEdit()
        self._out_range_value.setMinimumWidth(90)
        self._out_range_value.setPlaceholderText("8")
        settings_layout.addWidget(self._out_range_value)

        self._in_range_mode.currentIndexChanged.connect(
            lambda _index: self._on_range_mode_changed(self._in_range_mode, self._in_range_value)
        )
        self._out_range_mode.currentIndexChanged.connect(
            lambda _index: self._on_range_mode_changed(self._out_range_mode, self._out_range_value)
        )
        self._filter_combo.currentIndexChanged.connect(lambda _index: self._on_filter_kind_changed())
        self._filter_value.textEdited.connect(lambda _text: self._schedule_settings_autosave())
        self._in_range_value.textEdited.connect(lambda _text: self._schedule_settings_autosave())
        self._out_range_value.textEdited.connect(lambda _text: self._schedule_settings_autosave())

        self._settings_title = self.add_section_title("Настройки профиля", return_widget=True)
        self.layout.addWidget(self._settings_container)
        self._main_widgets.extend([self._settings_title, self._settings_container])

        self._strategy_stack = QStackedWidget(self)
        self._strategy_tabs = SegmentedWidget()
        self._strategy_tabs.addItem("strategies", "Готовые стратегии", lambda: self._strategy_stack.setCurrentIndex(0))
        self._strategy_tabs.addItem("match", "Когда применяется", lambda: self._strategy_stack.setCurrentIndex(1))
        self._strategy_tabs.setCurrentItem("strategies")
        self.layout.addWidget(self._strategy_tabs)
        self._main_widgets.append(self._strategy_tabs)

        self._strategy_list = ProfileStrategyListWidget(self)
        self._strategy_list.strategy_activated.connect(self._on_strategy_list_activated)
        self._strategy_stack.addWidget(self._strategy_list)

        match_tab = QWidget(self)
        match_layout = QVBoxLayout(match_tab)
        match_layout.setContentsMargins(0, 0, 0, 0)
        match_layout.setSpacing(10)
        self._match_text = PlainTextEdit()
        self._match_text.setReadOnly(True)
        self._match_text.setMinimumHeight(180)
        match_layout.addWidget(self._match_text)
        self._strategy_stack.addWidget(match_tab)

        self.layout.addWidget(self._strategy_stack, 1)
        self._main_widgets.append(self._strategy_stack)

        self._strategy_detail_container = QWidget(self)
        detail_layout = QVBoxLayout(self._strategy_detail_container)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(12)

        self._strategy_detail_title = TitleLabel("Готовая стратегия")
        detail_layout.addWidget(self._strategy_detail_title)

        self._strategy_detail_summary = BodyLabel("")
        self._strategy_detail_summary.setWordWrap(True)
        detail_layout.addWidget(self._strategy_detail_summary)

        detail_actions = QWidget(self._strategy_detail_container)
        detail_actions_layout = QHBoxLayout(detail_actions)
        detail_actions_layout.setContentsMargins(0, 0, 0, 0)
        detail_actions_layout.setSpacing(10)
        self._open_feedback_button = PushButton("Оценка стратегии")
        self._open_feedback_button.clicked.connect(self._open_feedback_subpage)
        detail_actions_layout.addWidget(self._open_feedback_button)
        detail_actions_layout.addStretch(1)
        detail_layout.addWidget(detail_actions)

        self._strategy_detail_args_title = _section_label("Аргументы готовой стратегии", self._strategy_detail_container)
        detail_layout.addWidget(self._strategy_detail_args_title)
        self._strategy_text = PlainTextEdit()
        self._strategy_text.setReadOnly(True)
        self._strategy_text.setMinimumHeight(190)
        detail_layout.addWidget(self._strategy_text)

        self._raw_title = _section_label("Что записано в профиль", self._strategy_detail_container)
        detail_layout.addWidget(self._raw_title)
        self._raw_text = PlainTextEdit()
        self._raw_text.setReadOnly(True)
        self._raw_text.setMinimumHeight(220)
        detail_layout.addWidget(self._raw_text)

        self._detail_match_title = _section_label("Когда профиль применяется", self._strategy_detail_container)
        detail_layout.addWidget(self._detail_match_title)
        self._detail_match_text = PlainTextEdit()
        self._detail_match_text.setReadOnly(True)
        self._detail_match_text.setMinimumHeight(120)
        detail_layout.addWidget(self._detail_match_text)

        self._strategy_detail_container.hide()
        self.layout.addWidget(self._strategy_detail_container)
        self._detail_widgets.append(self._strategy_detail_container)

        self._feedback_container = QWidget(self)
        feedback_layout = QVBoxLayout(self._feedback_container)
        feedback_layout.setContentsMargins(0, 0, 0, 0)
        feedback_layout.setSpacing(12)

        self._feedback_strategy_label = BodyLabel("")
        self._feedback_strategy_label.setWordWrap(True)
        feedback_layout.addWidget(self._feedback_strategy_label)

        self._feedback_status_label = BodyLabel("")
        self._feedback_status_label.setWordWrap(True)
        feedback_layout.addWidget(self._feedback_status_label)

        feedback_actions = QWidget(self._feedback_container)
        feedback_actions_layout = QHBoxLayout(feedback_actions)
        feedback_actions_layout.setContentsMargins(0, 0, 0, 0)
        feedback_actions_layout.setSpacing(12)

        self._work_button = PushButton("Работает")
        self._work_button.clicked.connect(lambda: self._set_current_strategy_feedback(rating="work"))
        feedback_actions_layout.addWidget(self._work_button)

        self._notwork_button = PushButton("Не работает")
        self._notwork_button.clicked.connect(lambda: self._set_current_strategy_feedback(rating="notwork"))
        feedback_actions_layout.addWidget(self._notwork_button)

        self._favorite_button = PushButton("В избранное")
        self._favorite_button.clicked.connect(self._toggle_current_strategy_favorite)
        feedback_actions_layout.addWidget(self._favorite_button)

        self._clear_feedback_button = PushButton("Убрать оценку")
        self._clear_feedback_button.clicked.connect(lambda: self._set_current_strategy_feedback(rating=""))
        feedback_actions_layout.addWidget(self._clear_feedback_button)
        feedback_actions_layout.addStretch(1)
        feedback_layout.addWidget(feedback_actions)

        self._feedback_container.hide()
        self.layout.addWidget(self._feedback_container)

    def _fill_range_combo(self, combo: ComboBox) -> None:
        combo.addItem("a", userData="a")
        combo.addItem("x", userData="x")
        combo.addItem("n", userData="n")
        combo.addItem("d", userData="d")
        combo.addItem("своё", userData="custom")

    def _rebuild_breadcrumb(self) -> None:
        self._breadcrumb.blockSignals(True)
        try:
            self._breadcrumb.clear()
            self._breadcrumb.addItem("control", tr_catalog(self.control_key, language=self._ui_language, default="Управление"))
            self._breadcrumb.addItem("profiles", tr_catalog(self.profiles_key, language=self._ui_language, default=self.profiles_default))
            title = str(getattr(getattr(self._payload, "item", None), "display_name", "") or "Профиль")
            self._breadcrumb.addItem("profile", title)
            if self._profile_subpage in {"strategy_detail", "feedback"}:
                self._breadcrumb.addItem("strategy_detail", self._detail_strategy_name())
            if self._profile_subpage == "feedback":
                self._breadcrumb.addItem("feedback", "Оценка стратегии")
        finally:
            self._breadcrumb.blockSignals(False)

    def _on_breadcrumb_item_changed(self, key: str) -> None:
        if key == "control":
            self._open_root()
        elif key == "profiles":
            self._open_profiles()
        elif key == "profile":
            self._profile_subpage = "profile"
            self._sync_subpage_visibility()
            self._rebuild_breadcrumb()
        elif key == "strategy_detail":
            self._profile_subpage = "strategy_detail"
            self._sync_subpage_visibility()
            self._rebuild_breadcrumb()
        elif key == "feedback":
            self._profile_subpage = "feedback"
            self._sync_subpage_visibility()
            self._rebuild_breadcrumb()

    def show_profile(self, profile_key: str) -> None:
        self._profile_key = str(profile_key or "").strip()
        self._profile_subpage = "profile"
        self._detail_strategy_id = ""
        self.reload_current_profile()

    def handle_page_command(self, command: str, payload: dict) -> bool:
        if command == "open_profile":
            self.show_profile(str((payload or {}).get("profile_key") or ""))
            return True
        return False

    def reload_current_profile(self) -> None:
        if not self._profile_key:
            return
        try:
            payload = self._controller.load(self._profile_key)
        except Exception as exc:
            log(f"{self.__class__.__name__}: не удалось прочитать профиль {self._profile_key}: {exc}", "ERROR")
            payload = None
        if payload is None:
            self._title.setText("Профиль не найден. Вернитесь к списку и нажмите «Обновить».")
            return
        self._payload = payload
        self._apply_payload(payload)

    def _apply_payload(self, payload) -> None:
        self._loading = True
        try:
            item = payload.item
            self._title.setText(item.display_name)
            self._summary.setText(payload.match_summary)
            self._enabled_checkbox.setChecked(bool(item.enabled))
            self._enabled_checkbox.setEnabled(True)
            self._apply_editable_settings(payload)

            self._match_text.setPlainText(payload.match_summary)
            self._strategy_list.set_rows(
                entries=payload.strategy_entries,
                states=payload.strategy_states,
                current_strategy_id=item.strategy_id or "none",
            )
            if self._profile_subpage in {"strategy_detail", "feedback"}:
                if not self._is_active_detail_strategy():
                    self._profile_subpage = "profile"
                    self._detail_strategy_id = ""
                else:
                    self._apply_strategy_detail(payload)
            self._strategy_text.setPlainText(payload.raw_strategy_text or "Стратегия не выбрана")
            self._raw_text.setPlainText(payload.raw_profile_text)
            self._detail_match_text.setPlainText(payload.match_summary)
            self._apply_feedback_buttons(payload)
            self._sync_subpage_visibility()
            self._rebuild_breadcrumb()
        finally:
            self._loading = False

    def _detail_strategy_name(self) -> str:
        payload = self._payload
        strategy_id = str(self._detail_strategy_id or "").strip()
        if payload is None or not strategy_id:
            return "Готовая стратегия"
        entry = payload.strategy_entries.get(strategy_id)
        return str(getattr(entry, "name", "") or "Готовая стратегия")

    def _is_active_detail_strategy(self) -> bool:
        payload = self._payload
        if payload is None:
            return False
        return bool(
            self._detail_strategy_id
            and self._detail_strategy_id == str(payload.item.strategy_id or "").strip()
            and self._detail_strategy_id not in {"none", "custom"}
        )

    def _apply_strategy_detail(self, payload) -> None:
        strategy_id = str(self._detail_strategy_id or "").strip()
        entry = payload.strategy_entries.get(strategy_id)
        if entry is None:
            return
        state = payload.strategy_states.get(strategy_id)
        status_parts = ["Активная готовая стратегия"]
        if bool(getattr(state, "favorite", False)):
            status_parts.append("в избранном")
        rating = str(getattr(state, "rating", "") or "")
        if rating == "work":
            status_parts.append("оценка: работает")
        elif rating == "notwork":
            status_parts.append("оценка: не работает")
        else:
            status_parts.append("оценка не выбрана")
        self._strategy_detail_title.setText(str(getattr(entry, "name", "") or "Готовая стратегия"))
        self._strategy_detail_summary.setText(" • ".join(status_parts))
        self._strategy_text.setPlainText(str(getattr(entry, "args", "") or "Стратегия не выбрана"))
        self._raw_text.setPlainText(payload.raw_profile_text)
        self._detail_match_text.setPlainText(payload.match_summary)

    def _apply_feedback_buttons(self, payload) -> None:
        item = payload.item
        state = payload.current_strategy_state
        editable = bool(
            item.in_preset
            and item.enabled
            and item.strategy_id not in {"", "none", "custom"}
        )
        if self._open_feedback_button is not None:
            self._open_feedback_button.setEnabled(editable and self._is_active_detail_strategy())
        for button in (self._work_button, self._notwork_button, self._favorite_button, self._clear_feedback_button):
            if button is not None:
                button.setEnabled(editable)
        if self._feedback_strategy_label is not None:
            self._feedback_strategy_label.setText(f"Готовая стратегия: {item.strategy_name}")
        if self._feedback_status_label is not None:
            status_parts = []
            if state.rating == "work":
                status_parts.append("Оценка: работает")
            elif state.rating == "notwork":
                status_parts.append("Оценка: не работает")
            else:
                status_parts.append("Оценка не выбрана")
            status_parts.append("В избранном" if state.favorite else "Не в избранном")
            if not editable:
                status_parts.append("Оценка доступна только для готовой стратегии внутри включённого профиля")
            self._feedback_status_label.setText(" • ".join(status_parts))
        if self._favorite_button is not None:
            self._favorite_button.setText("Убрать из избранного" if state.favorite else "В избранное")
        if self._work_button is not None:
            self._work_button.setProperty("selected", state.rating == "work")
        if self._notwork_button is not None:
            self._notwork_button.setProperty("selected", state.rating == "notwork")

    def _open_feedback_subpage(self) -> None:
        if not self._is_active_detail_strategy():
            return
        self._profile_subpage = "feedback"
        self._sync_subpage_visibility()
        self._rebuild_breadcrumb()

    def _sync_subpage_visibility(self) -> None:
        main_visible = self._profile_subpage == "profile"
        detail_visible = self._profile_subpage == "strategy_detail"
        feedback_visible = self._profile_subpage == "feedback"
        for widget in self._main_widgets:
            if widget is not None:
                widget.setVisible(main_visible)
        for widget in self._detail_widgets:
            if widget is not None:
                widget.setVisible(detail_visible)
        if main_visible and not is_zapret2_launch_method(self.launch_method):
            if self._settings_title is not None:
                self._settings_title.hide()
            if self._settings_container is not None:
                self._settings_container.hide()
        if self._feedback_container is not None:
            self._feedback_container.setVisible(feedback_visible)

    def _apply_editable_settings(self, payload) -> None:
        is_winws2 = is_zapret2_launch_method(self.launch_method)
        if self._settings_title is not None:
            self._settings_title.setVisible(is_winws2)
        if self._settings_container is not None:
            self._settings_container.setVisible(is_winws2)
        if not is_winws2:
            return

        filter_enabled = bool(getattr(payload, "editable_filter_enabled", True))
        self._filter_combo.setVisible(filter_enabled)
        self._filter_value.setVisible(filter_enabled)
        set_combo_by_data(self._filter_combo, getattr(payload, "editable_filter_kind", "") or "hostlist")
        self._filter_value.setText(str(getattr(payload, "editable_filter_value", "") or ""))
        set_range_controls(self._in_range_mode, self._in_range_value, getattr(payload, "in_range", "") or "x")
        set_range_controls(self._out_range_mode, self._out_range_value, getattr(payload, "out_range", "") or "a")

    def _on_range_mode_changed(self, combo: ComboBox, value_edit: LineEdit) -> None:
        sync_range_value_enabled(combo, value_edit)
        self._schedule_settings_autosave()

    def _on_filter_kind_changed(self) -> None:
        self._sync_filter_value_for_kind()
        self._schedule_settings_autosave()

    def _sync_filter_value_for_kind(self) -> None:
        if self._loading or not is_zapret2_launch_method(self.launch_method):
            return
        filter_kind = str(self._filter_combo.itemData(self._filter_combo.currentIndex()) or "hostlist")
        normalized = normalize_winws2_filter_value(self._filter_value.text(), filter_kind)
        if normalized and normalized != self._filter_value.text().strip():
            self._filter_value.setText(normalized)

    def _schedule_settings_autosave(self) -> None:
        if self._loading or not self._profile_key or not is_zapret2_launch_method(self.launch_method):
            return
        self._settings_save_timer.start()

    def _autosave_editable_settings(self) -> None:
        if self._loading or not self._profile_key or not is_zapret2_launch_method(self.launch_method):
            return
        filter_value = self._filter_value.text().strip()
        filter_enabled = bool(getattr(self._payload, "editable_filter_enabled", True))
        if filter_enabled and not filter_value:
            return
        try:
            new_key = self._controller.save_winws2_settings(
                profile_key=self._profile_key,
                filter_kind=str(self._filter_combo.itemData(self._filter_combo.currentIndex()) or "hostlist"),
                filter_value=filter_value,
                in_range=range_expression_from_controls(self._in_range_mode, self._in_range_value, default="x"),
                out_range=range_expression_from_controls(self._out_range_mode, self._out_range_value, default="a"),
            )
            if new_key:
                self._profile_key = new_key
            self.reload_current_profile()
            self._on_profile_changed_callback(self._profile_key, "settings")
        except Exception as exc:
            log(f"{self.__class__.__name__}: не удалось сохранить настройки профиля: {exc}", "ERROR")

    def _on_enabled_changed(self, state: int) -> None:
        if self._loading or not self._profile_key:
            return
        enabled = bool(state == Qt.CheckState.Checked.value or state == 2)
        try:
            new_key = self._controller.set_enabled(
                profile_key=self._profile_key,
                enabled=enabled,
            )
            if new_key:
                self._profile_key = new_key
            self.reload_current_profile()
            self._on_profile_changed_callback(self._profile_key, "enabled" if enabled else "disabled")
        except Exception as exc:
            log(f"{self.__class__.__name__}: не удалось изменить состояние профиля: {exc}", "ERROR")

    def _on_strategy_list_activated(self, strategy_id: str) -> None:
        if self._loading or not self._profile_key:
            return
        strategy_id = str(strategy_id or "").strip()
        if not strategy_id or strategy_id in {"none", "custom"}:
            return
        if self._payload is not None and strategy_id == str(self._payload.item.strategy_id or "").strip():
            self._detail_strategy_id = strategy_id
            self._profile_subpage = "strategy_detail"
            self._apply_strategy_detail(self._payload)
            self._sync_subpage_visibility()
            self._rebuild_breadcrumb()
            return
        try:
            new_key = self._controller.apply_strategy(
                profile_key=self._profile_key,
                strategy_id=strategy_id,
            )
            if new_key:
                self._profile_key = new_key
            self.reload_current_profile()
            self._on_profile_changed_callback(self._profile_key, "strategy")
        except Exception as exc:
            log(f"{self.__class__.__name__}: не удалось применить стратегию: {exc}", "ERROR")

    def _set_current_strategy_feedback(self, *, rating: str) -> None:
        if self._loading or not self._profile_key:
            return
        try:
            self._controller.set_strategy_feedback(
                profile_key=self._profile_key,
                rating=rating,
            )
            self.reload_current_profile()
            self._on_profile_changed_callback(self._profile_key, "feedback")
        except Exception as exc:
            log(f"{self.__class__.__name__}: не удалось обновить оценку стратегии: {exc}", "ERROR")

    def _toggle_current_strategy_favorite(self) -> None:
        if self._loading or not self._profile_key or self._payload is None:
            return
        try:
            current = bool(self._payload.current_strategy_state.favorite)
            self._controller.set_strategy_feedback(
                profile_key=self._profile_key,
                favorite=not current,
            )
            self.reload_current_profile()
            self._on_profile_changed_callback(self._profile_key, "feedback")
        except Exception as exc:
            log(f"{self.__class__.__name__}: не удалось обновить избранную стратегию: {exc}", "ERROR")


class Zapret2ProfileSetupPage(ProfileSetupPageBase):
    launch_method = ZAPRET2_MODE
    title_key_name = "page.winws2_profile_setup.title"
    control_key = "page.winws2_profile_setup.breadcrumb.control"
    profiles_key = "page.winws2_pages.title"
    profiles_default = "Настройка пресета"


class Zapret1ProfileSetupPage(ProfileSetupPageBase):
    launch_method = ZAPRET1_MODE
    title_key_name = "page.winws1_profile_setup.title"
    control_key = "page.winws1_profile_setup.breadcrumb.control"
    profiles_key = "page.winws1_pages.title"
    profiles_default = "Настройка пресета"
