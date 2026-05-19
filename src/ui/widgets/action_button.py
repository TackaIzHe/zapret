from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSizePolicy
from qfluentwidgets import PushButton

from ui.theme import get_cached_qta_pixmap, get_themed_qta_icon, get_theme_tokens
from ui.theme_refresh import ThemeRefreshBinding


def _button_palette(tokens) -> dict[str, str]:
    if getattr(tokens, "is_light", False):
        return {
            "bg": "#ffffff",
            "hover": "#f4f5f7",
            "pressed": "#e9ebef",
            "fg": "rgba(0, 0, 0, 0.90)",
            "fg_disabled": "rgba(0, 0, 0, 0.36)",
            "border": "rgba(0, 0, 0, 0.14)",
            "border_hover": "rgba(0, 0, 0, 0.22)",
            "disabled": "rgba(0, 0, 0, 0.035)",
        }
    return {
        "bg": "#111111",
        "hover": "#1d1d1d",
        "pressed": "#070707",
        "fg": "rgba(255, 255, 255, 0.94)",
        "fg_disabled": "rgba(255, 255, 255, 0.38)",
        "border": "rgba(255, 255, 255, 0.14)",
        "border_hover": "rgba(255, 255, 255, 0.24)",
        "disabled": "rgba(255, 255, 255, 0.045)",
    }


def _set_icon(button, icon_name: str, color: str, size: int) -> None:
    if not icon_name:
        return
    try:
        pixmap = get_cached_qta_pixmap(icon_name, color=color, size=size)
        if not pixmap.isNull():
            button.setIcon(QIcon(pixmap))
            return
    except Exception:
        pass
    try:
        button.setIcon(get_themed_qta_icon(icon_name, color=color))
    except Exception:
        pass


def apply_themed_action_button(
    button,
    *,
    icon_name: str | None = None,
    alignment: str = "center",
    full_width: bool = False,
    min_width: int | None = None,
    icon_size: int = 15,
) -> object:
    if button is None:
        return button

    clean_alignment = "left" if str(alignment or "").strip().lower() == "left" else "center"
    button._themed_action_icon_name = str(icon_name or "")  # type: ignore[attr-defined]
    button._themed_action_alignment = clean_alignment  # type: ignore[attr-defined]
    button._themed_action_icon_size = int(icon_size or 15)  # type: ignore[attr-defined]

    try:
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(32)
        button.setIconSize(QSize(icon_size, icon_size))
    except Exception:
        pass

    try:
        policy = QSizePolicy.Policy.Expanding if full_width else QSizePolicy.Policy.Fixed
        button.setSizePolicy(policy, QSizePolicy.Policy.Fixed)
    except Exception:
        pass
    if min_width is not None:
        try:
            button.setMinimumWidth(int(min_width))
        except Exception:
            pass

    def _apply(tokens=None, force: bool = False) -> None:
        _ = force
        resolved_tokens = tokens or get_theme_tokens()
        palette = _button_palette(resolved_tokens)
        align = getattr(button, "_themed_action_alignment", clean_alignment)
        text_align = "left" if align == "left" else "center"
        padding = "0 16px 0 13px" if align == "left" else "0 16px"
        try:
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {palette["bg"]};
                    color: {palette["fg"]};
                    border: 1px solid {palette["border"]};
                    border-radius: 6px;
                    padding: {padding};
                    font-weight: 500;
                    text-align: {text_align};
                }}
                QPushButton:hover {{
                    background-color: {palette["hover"]};
                    border-color: {palette["border_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {palette["pressed"]};
                    border-color: {palette["border_hover"]};
                }}
                QPushButton:disabled {{
                    background-color: {palette["disabled"]};
                    color: {palette["fg_disabled"]};
                    border-color: transparent;
                }}
                """
            )
        except Exception:
            pass
        icon = getattr(button, "_themed_action_icon_name", "") or ""
        if icon:
            _set_icon(button, icon, palette["fg"], getattr(button, "_themed_action_icon_size", icon_size))

    _apply(get_theme_tokens(), force=True)
    try:
        binding = getattr(button, "_themed_action_button_refresh", None)
        if binding is None:
            button._themed_action_button_refresh = ThemeRefreshBinding(button, _apply)  # type: ignore[attr-defined]
        else:
            binding.invalidate()
            binding.request_refresh(force=True)
    except Exception:
        pass

    return button


class ThemedActionButton(PushButton):
    def __init__(
        self,
        text: str = "",
        icon_name: str | None = None,
        *,
        alignment: str = "center",
        full_width: bool = False,
        min_width: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setText(str(text or ""))
        apply_themed_action_button(
            self,
            icon_name=icon_name,
            alignment=alignment,
            full_width=full_width,
            min_width=min_width,
        )
