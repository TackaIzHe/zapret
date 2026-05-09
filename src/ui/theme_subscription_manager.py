# ui/theme_subscription_manager.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget

from log.log import log


PREMIUM_TITLE_BADGE_TEXT = "Premium"


class ThemeSubscriptionManager:
    """
    Миксин для отображения Premium-статуса в верхней панели окна.

    Базовый системный заголовок окна ставит ZapretFluentWindow при создании.
    Этот миксин не пересобирает заголовок целиком, а обновляет только отдельную
    Premium-метку, чтобы основной текст окна не прыгал при получении подписки.
    """

    def update_subscription_title_badge(
        self: QWidget,
        is_premium: bool = False,
        source: str = "api",
    ) -> None:
        """Добавляет или скрывает отдельную Premium-метку в верхней панели."""
        if not is_premium:
            badge = getattr(self, "_subscription_title_badge", None)
            if badge is None:
                return
            if badge.isVisible():
                badge.hide()
                log(f"Premium-метка скрыта (source: {source})", "DEBUG")
            return

        badge = self._ensure_subscription_title_badge()
        if badge is None:
            log(f"Premium-метка не обновлена: titleBar недоступен (source: {source})", "WARNING")
            return

        if badge.text() != PREMIUM_TITLE_BADGE_TEXT:
            badge.setText(PREMIUM_TITLE_BADGE_TEXT)
            badge.adjustSize()

        if not badge.isVisible():
            badge.show()
            log(f"Premium-метка показана (source: {source})", "DEBUG")

    def _ensure_subscription_title_badge(self: QWidget) -> QLabel | None:
        badge = getattr(self, "_subscription_title_badge", None)
        if badge is not None:
            return badge

        title_bar = getattr(self, "titleBar", None)
        if title_bar is None:
            return None

        layout = getattr(title_bar, "hBoxLayout", None)
        if layout is None:
            return None

        badge = QLabel(PREMIUM_TITLE_BADGE_TEXT, title_bar)
        badge.setObjectName("premiumTitleBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedHeight(22)
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        badge.setStyleSheet(
            "color: #b45309; "
            "font-size: 10px; "
            "font-weight: 600; "
            "background: rgba(255, 193, 7, 0.16); "
            "padding: 2px 8px; "
            "border-radius: 4px;"
        )

        insert_index = self._subscription_title_badge_insert_index(layout)
        layout.insertWidget(insert_index, badge, 0, Qt.AlignmentFlag.AlignVCenter)
        badge.hide()
        self._subscription_title_badge = badge
        return badge

    def _subscription_title_badge_insert_index(self: QWidget, layout) -> int:
        search_widget = getattr(self, "_sidebar_search_nav_widget", None)
        if search_widget is not None:
            search_index = layout.indexOf(search_widget)
            if search_index >= 0:
                return search_index

        return max(0, layout.count() - 1)
